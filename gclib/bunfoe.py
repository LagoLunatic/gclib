from __future__ import annotations
import dataclasses
from dataclasses import MISSING, _EMPTY_METADATA
from enum import Enum
from typing import Any, BinaryIO, Sequence, Type, GenericAlias
import typing
import types

from gclib import fs_helpers as fs
from gclib.fs_helpers import u32, u16, u8, s32, s16, s8, u16Rot, FixedStr, MagicStr

# TODO: implement ignore field argument.
# TODO: implement assert_default field argument. (assert _padding fields are equal to their default value)

class BUNFOE:
  """Binary-UNpacking Field-Owning Entity.
  
  This is a wrapper around dataclasses that implements automatic reading and writing of binary
  struct data."""
  
  # TODO: automatically calculate BYTE_SIZE based on the size of all the fields combined?
  
  def __init__(self, data: BinaryIO):
    self.data = data
  
  @staticmethod
  def get_byte_size(field_type: Type) -> int:
    if field_type in fs.PRIMITIVE_TYPE_TO_BYTE_SIZE:
      return fs.PRIMITIVE_TYPE_TO_BYTE_SIZE[field_type]
    elif issubclass(field_type, bool):
      return BUNFOE.get_byte_size(u8)
    elif issubclass(field_type, u16Rot):
      return BUNFOE.get_byte_size(u16)
    elif isinstance(field_type, GenericAlias) and field_type.__origin__ in [FixedStr, MagicStr]:
      return typing.get_args(field_type)[0]
    elif isinstance(field_type, GenericAlias) and field_type.__origin__ in [tuple, list]:
      size = 0
      for arg_type in typing.get_args(field_type):
        size += BUNFOE.get_byte_size(arg_type)
      return size
    elif issubclass(field_type, Enum):
      for base_class in field_type.__mro__:
        if issubclass(base_class, int) and base_class in fs.PRIMITIVE_TYPE_TO_BYTE_SIZE:
          return BUNFOE.get_byte_size(base_class)
      raise Exception("Enum must inherit from a primitive int subclass.")
    else:
      raise NotImplementedError
  
  #region Reading
  def read(self, offset: int):
    for field in fields(self):
      offset = self.read_field(field, offset)
  
  def read_field(self, field: Field, offset: int) -> int:
    if field.indexed_by:
      index_type, attrs_path_to_list_offset = field.indexed_by
      index = self.read_value(index_type, offset)
      offset += self.get_byte_size(index_type)
      
      curr = self
      for attr_name in attrs_path_to_list_offset:
        curr = getattr(curr, attr_name)
      list_offset = curr
      assert isinstance(list_offset, int)
      value_offset = list_offset + index*self.get_byte_size(field.type)
      value = self.read_value(field.type, value_offset)
    else:
      value = self.read_value(field.type, offset)
      offset += self.get_byte_size(field.type)
    
    setattr(self, field.name, value)
    return offset
  
  def read_value(self, field_type: Type, offset: int) -> Any:
    if field_type in fs.PRIMITIVE_TYPE_TO_READ_FUNC:
      read_func = fs.PRIMITIVE_TYPE_TO_READ_FUNC[field_type]
      return read_func(self.data, offset)
    elif issubclass(field_type, bool):
      raw_value = self.read_value(u8, offset)
      assert raw_value in [0, 1], f"Boolean must be zero or one, but got value: {raw_value}"
      return bool(raw_value)
    elif issubclass(field_type, u16Rot):
      return self.read_value(u16, offset)
    elif isinstance(field_type, GenericAlias) and field_type.__origin__ in [FixedStr, MagicStr]:
      str_len = typing.get_args(field_type)[0]
      return fs.read_str(self.data, offset, str_len)
    elif isinstance(field_type, GenericAlias) and field_type.__origin__ in [tuple, list]:
      return self.read_sequence(field_type, offset)
    elif issubclass(field_type, Enum):
      for base_class in field_type.__mro__:
        if issubclass(base_class, int) and base_class in fs.PRIMITIVE_TYPE_TO_BYTE_SIZE:
          raw_value = self.read_value(base_class, offset)
          return field_type(raw_value)
      raise Exception("Enum must inherit from a primitive int subclass.")
    else:
      raise NotImplementedError
  
  def read_sequence(self, field_type: Type, offset: int) -> Sequence:
    values = []
    for arg_type in typing.get_args(field_type):
      value = self.read_value(arg_type, offset)
      values.append(value)
      offset += self.get_byte_size(arg_type)
    return field_type(values)
  #endregion
  
  #region Saving
  def save(self, offset: int):
    for field in fields(self):
      offset = self.save_field(field.type, field.name, offset)
  
  def save_field(self, field_type: Type, field_name: str, offset: int) -> int:
    value = getattr(self, field_name)
    self.save_value(field_type, offset, value)
    offset += self.get_byte_size(field_type)
    return offset
  
  def save_value(self, field_type: Type, offset: int, value: Any) -> None:
    if field_type in fs.PRIMITIVE_TYPE_TO_WRITE_FUNC:
      write_func = fs.PRIMITIVE_TYPE_TO_WRITE_FUNC[field_type]
      write_func(self.data, offset, value)
    elif issubclass(field_type, bool):
      self.save_value(u8, offset, int(value))
    elif issubclass(field_type, u16Rot):
      self.save_value(u16, offset, value)
    elif isinstance(field_type, GenericAlias) and field_type.__origin__ == FixedStr:
      str_len = typing.get_args(field_type)[0]
      fs.write_str(self.data, offset, str_len)
    elif isinstance(field_type, GenericAlias) and field_type.__origin__ == MagicStr:
      str_len = typing.get_args(field_type)[0]
      fs.write_magic_str(self.data, offset, str_len)
    elif isinstance(field_type, GenericAlias) and field_type.__origin__ in [tuple, list]:
      self.save_sequence(field_type, offset, value)
    elif issubclass(field_type, Enum):
      for base_class in field_type.__mro__:
        if issubclass(base_class, int) and base_class in fs.PRIMITIVE_TYPE_TO_BYTE_SIZE:
          raw_value = value.value
          self.save_value(base_class, offset, raw_value)
          return
      raise Exception("Enum must inherit from a primitive int subclass.")
    else:
      raise NotImplementedError
  
  def save_sequence(self, field_type: Type, offset: int, value: Sequence):
    for i, arg_type in enumerate(typing.get_args(field_type)):
      self.save_value(arg_type, offset, value[i])
      offset += self.get_byte_size(arg_type)
  #endregion


def _process_class(cls, init, repr, eq, order, unsafe_hash, frozen,
                   match_args, kw_only, slots, weakref_slot):
  
  # if BUNFOE not in cls.__bases__:
  #   # Modify the class to inherit from BUNFOE.
  #   if cls.__bases__ == (object,):
  #     cls_bases = (BUNFOE,)
  #   else:
  #     cls_bases = cls.__bases__ + (BUNFOE,)
  #   cls_dict = dict(cls.__dict__)
  #   qualname = getattr(cls, '__qualname__', None)
  #   cls = type(cls.__name__, cls_bases, cls_dict)
  #   if qualname is not None:
  #       cls.__qualname__ = qualname
  
  cls_annotations = cls.__dict__.get('__annotations__', {})
  for field_name, field_type in cls_annotations.items():
    default = getattr(cls, field_name, MISSING)
    if not isinstance(default, Field):
      setattr(cls, field_name, field(default=default))
  
  cls = dataclasses._process_class(cls, init, repr, eq, order, unsafe_hash, frozen,
                                   match_args, kw_only, slots, weakref_slot)
  
  assert issubclass(cls, BUNFOE)
  
  return cls

def bunfoe(cls=None, /, *,
           # Dataclass arguments. Some defaults are changed.
           init=False, repr=True, eq=False, order=False,
           unsafe_hash=False, frozen=False, match_args=True,
           kw_only=False, slots=False, weakref_slot=False,
           ):
  def wrap(cls):
    return _process_class(cls,
      init=init, repr=repr, eq=eq, order=order,
      unsafe_hash=unsafe_hash, frozen=frozen, match_args=match_args,
      kw_only=kw_only, slots=slots, weakref_slot=weakref_slot
    )

  if cls is None:
    # Called as @bunfoe() with parentheses.
    return wrap

  # Called as @bunfoe without parentheses.
  return wrap(cls)


class Field(dataclasses.Field):
    __slots__ = ('name',
                 'type',
                 'default',
                 'default_factory',
                 'repr',
                 'hash',
                 'init',
                 'compare',
                 'metadata',
                 'kw_only',
                 '_field_type',  # Private: not to be used by user code.
                 
                 # Custom.
                 'ignore',
                 'indexed_by',
                 'assert_default',
                 )

    def __init__(self, default, default_factory, init, repr, hash, compare,
                 metadata, kw_only, ignore, indexed_by, assert_default):
        self.name = None
        self.type = None
        self.default = default
        self.default_factory = default_factory
        self.init = init
        self.repr = repr
        self.hash = hash
        self.compare = compare
        self.metadata = (_EMPTY_METADATA
                         if metadata is None else
                         types.MappingProxyType(metadata))
        self.kw_only = kw_only
        self._field_type = None
        
        # Custom.
        self.ignore = ignore
        self.indexed_by = indexed_by
        self.assert_default = assert_default

    @dataclasses._recursive_repr
    def __repr__(self):
        return ('Field('
                f'name={self.name!r},'
                f'type={self.type!r},'
                f'default={self.default!r},'
                f'default_factory={self.default_factory!r},'
                f'init={self.init!r},'
                f'repr={self.repr!r},'
                f'hash={self.hash!r},'
                f'compare={self.compare!r},'
                f'metadata={self.metadata!r},'
                f'kw_only={self.kw_only!r},'
                f'_field_type={self._field_type},'
                
                # Custom.
                f'ignore={self.ignore!r},'
                f'indexed_by={self.indexed_by!r},'
                f'assert_default={self.assert_default!r},'
                ')')

def field(*, default=MISSING, default_factory=MISSING, init=True, repr=True,
          hash=None, compare=True, metadata=None, kw_only=MISSING,
          ignore=False, indexed_by=None, assert_default=False):
  return Field(default, default_factory, init, repr, hash, compare,
               metadata, kw_only, ignore, indexed_by, assert_default)

def fields(class_or_instance):
  if not isinstance(class_or_instance, BUNFOE) and not issubclass(class_or_instance, BUNFOE):
    raise TypeError(f'{class_or_instance} does not inherit from BUNFOE') from None
  if not hasattr(class_or_instance, dataclasses._FIELDS):
    raise TypeError(f'{class_or_instance} does not use the @bunfoe decorator') from None
  return dataclasses.fields(class_or_instance)