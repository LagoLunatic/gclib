from enum import Enum
from io import BytesIO
from typing import BinaryIO, ClassVar

from gclib import fs_helpers as fs
from gclib.fs_helpers import u32, u24, u16, u8, s32, s16, s8, u16Rot, FixedStr, MagicStr
from gclib.bunfoe import BUNFOE, Field, bunfoe, field, fields
from gclib.jchunk import JChunk
from gclib.texture_utils import ImageFormat
import gclib.gx_enums as GX
from gclib.gx_enums import MDLCommandType, BPRegister, XFRegister

class MDLCommand(BUNFOE):
  VALID_REGISTERS: ClassVar[list[Enum]] = []
  
  @classmethod
  def new_from_register(cls, register: Enum, data: BinaryIO):
    # When instantiating the base class, try to find if any subclasses are for this register.
    for subcls in cls.__subclasses__():
      if register in subcls.VALID_REGISTERS:
        return subcls(data)
    # If not, just return a generic version of the command that holds a bitfield.
    return cls(data)
  
  def assert_valid(self):
    raise NotImplementedError
  
  def read(self, offset: int) -> int:
    offset = super().read(offset)
    self.assert_valid()
    return offset
  
  def save(self, offset: int) -> int:
    self.assert_valid()
    return super().save(offset)

@bunfoe
class BPCommand(MDLCommand):
  type: MDLCommandType = field(default=MDLCommandType.BP, assert_default=True) # TODO hide from GUI
  register: BPRegister # TODO read only # TODO hide from gui
  bitfield: u24 = field(bitfield=True)
  
  DATA_SIZE = 5
  VALID_REGISTERS: ClassVar[list[BPRegister]] = []
  
  def assert_valid(self):
    assert self.type == MDLCommandType.BP
    if self.__class__ is not BPCommand:
      assert self.register in self.VALID_REGISTERS

@bunfoe
class XFCommand(MDLCommand):
  type: MDLCommandType = field(default=MDLCommandType.XF, assert_default=True) # TODO hide from GUI
  num_args_minus_1: u16
  register: XFRegister # TODO read only # TODO hide from gui
  args: list[u32] = field(length_calculator=lambda inst: inst.num_args_minus_1 + 1)
  
  VALID_REGISTERS: ClassVar[list[XFRegister]] = []
  
  def assert_valid(self):
    assert self.type == MDLCommandType.XF
    if self.__class__ is not XFCommand:
      assert self.register in self.VALID_REGISTERS

@bunfoe
class TX_SETIMAGE(BPCommand):
  width_minus_1 : u16         = field(bits=10)
  height_minus_1: u16         = field(bits=10)
  format        : ImageFormat = field(bits=4)
  
  VALID_REGISTERS = [
    BPRegister.TX_SETIMAGE0_I0, BPRegister.TX_SETIMAGE0_I1, BPRegister.TX_SETIMAGE0_I2, BPRegister.TX_SETIMAGE0_I3,
    BPRegister.TX_SETIMAGE0_I4, BPRegister.TX_SETIMAGE0_I5, BPRegister.TX_SETIMAGE0_I6, BPRegister.TX_SETIMAGE0_I7,
    BPRegister.TX_SETIMAGE1_I0, BPRegister.TX_SETIMAGE1_I1, BPRegister.TX_SETIMAGE1_I2, BPRegister.TX_SETIMAGE1_I3,
    BPRegister.TX_SETIMAGE1_I4, BPRegister.TX_SETIMAGE1_I5, BPRegister.TX_SETIMAGE1_I6, BPRegister.TX_SETIMAGE1_I7,
    BPRegister.TX_SETIMAGE2_I0, BPRegister.TX_SETIMAGE2_I1, BPRegister.TX_SETIMAGE2_I2, BPRegister.TX_SETIMAGE2_I3,
    BPRegister.TX_SETIMAGE2_I4, BPRegister.TX_SETIMAGE2_I5, BPRegister.TX_SETIMAGE2_I6, BPRegister.TX_SETIMAGE2_I7,
    BPRegister.TX_SETIMAGE3_I0, BPRegister.TX_SETIMAGE3_I1, BPRegister.TX_SETIMAGE3_I2, BPRegister.TX_SETIMAGE3_I3,
    BPRegister.TX_SETIMAGE3_I4, BPRegister.TX_SETIMAGE3_I5, BPRegister.TX_SETIMAGE3_I6, BPRegister.TX_SETIMAGE3_I7,
  ]

@bunfoe
class TX_SETMODE(BPCommand):
  wrap_s    : GX.WrapMode = field(bits=2)
  wrap_t    : GX.WrapMode = field(bits=2)
  mag_filter: u8          = field(bits=1)
  min_filter: u8          = field(bits=3)
  diag_lod  : bool        = field(bits=1)
  lod_bias  : u8          = field(bits=8)
  unknown   : u8          = field(bits=2)
  max_aniso : u8          = field(bits=2)
  lod_clamp : bool        = field(bits=1)
  
  VALID_REGISTERS = [
    BPRegister.TX_SETMODE0_I0, BPRegister.TX_SETMODE0_I1, BPRegister.TX_SETMODE0_I2, BPRegister.TX_SETMODE0_I3,
    BPRegister.TX_SETMODE0_I4, BPRegister.TX_SETMODE0_I5, BPRegister.TX_SETMODE0_I6, BPRegister.TX_SETMODE0_I7,
    BPRegister.TX_SETMODE1_I0, BPRegister.TX_SETMODE1_I1, BPRegister.TX_SETMODE1_I2, BPRegister.TX_SETMODE1_I3,
    BPRegister.TX_SETMODE1_I4, BPRegister.TX_SETMODE1_I5, BPRegister.TX_SETMODE1_I6, BPRegister.TX_SETMODE1_I7,
  ]

@bunfoe
class SU_SSIZE(BPCommand):
  width_minus_1: u16  = field(bits=16)
  unknown      : bool = field(bits=1)
  
  VALID_REGISTERS = [
    BPRegister.SU_SSIZE0, BPRegister.SU_SSIZE1, BPRegister.SU_SSIZE2, BPRegister.SU_SSIZE3,
    BPRegister.SU_SSIZE4, BPRegister.SU_SSIZE5, BPRegister.SU_SSIZE6, BPRegister.SU_SSIZE7,
  ]

@bunfoe
class SU_TSIZE(BPCommand):
  height_minus_1: u16  = field(bits=16)
  unknown       : bool = field(bits=1)
  
  VALID_REGISTERS = [
    BPRegister.SU_TSIZE0, BPRegister.SU_TSIZE1, BPRegister.SU_TSIZE2, BPRegister.SU_TSIZE3,
    BPRegister.SU_TSIZE4, BPRegister.SU_TSIZE5, BPRegister.SU_TSIZE6, BPRegister.SU_TSIZE7,
  ]

@bunfoe
class TEV_REGISTERL(BPCommand):
  r: u16 = field(bits=11)
  a: u16 = field(bits=11)
  
  VALID_REGISTERS = [
    BPRegister.TEV_REGISTERL_0, BPRegister.TEV_REGISTERL_1, BPRegister.TEV_REGISTERL_2, BPRegister.TEV_REGISTERL_3,
  ]

@bunfoe
class TEV_REGISTERH(BPCommand):
  b: u16 = field(bits=11)
  g: u16 = field(bits=11)
  
  VALID_REGISTERS = [
    BPRegister.TEV_REGISTERH_0, BPRegister.TEV_REGISTERH_1, BPRegister.TEV_REGISTERH_2, BPRegister.TEV_REGISTERH_3,
  ]

@bunfoe
class PE_ZMODE(BPCommand):
  depth_test : bool           = field(bits=1)
  depth_func : GX.CompareType = field(bits=3)
  depth_write: bool           = field(bits=1)
  
  VALID_REGISTERS = [
    BPRegister.PE_ZMODE,
  ]

@bunfoe
class TEXMTX(XFCommand):
  pass
  
  VALID_REGISTERS = [
    XFRegister.TEXMTX0, XFRegister.TEXMTX1, XFRegister.TEXMTX2, XFRegister.TEXMTX3,
    XFRegister.TEXMTX4, XFRegister.TEXMTX5, XFRegister.TEXMTX6, XFRegister.TEXMTX7,
    XFRegister.TEXMTX8, XFRegister.TEXMTX9,
  ]

@bunfoe
class MDLEntry(BUNFOE):
  bp_commands: list[BPCommand] = field(default_factory=list)
  xf_commands: list[XFCommand] = field(default_factory=list)
  
  def __post_init__(self):
    super().__post_init__()
    
    self.chan_color_subpacket_offset = None
    self.chan_control_subpacket_offset = None
    self.tex_gen_subpacket_offset = None
    self.texture_subpacket_offset = None
    self.tev_subpacket_offset = None
    self.pixel_subpacket_offset = None
  
  def read(self, offset: int, size: int) -> int:
    self.bp_commands.clear()
    self.xf_commands.clear()
    
    orig_offset = offset
    while offset < orig_offset+size:
      command_type = fs.read_u8(self.data, offset)
      if command_type == MDLCommandType.BP.value:
        register = BPRegister(fs.read_u8(self.data, offset+1))
        command = BPCommand.new_from_register(register, self.data)
        offset = command.read(offset)
        self.bp_commands.append(command)
      elif command_type == MDLCommandType.XF.value:
        register = XFRegister(fs.read_u16(self.data, offset+3))
        command = XFCommand.new_from_register(register, self.data)
        offset = command.read(offset)
        self.xf_commands.append(command)
      elif command_type == MDLCommandType.END_MARKER.value:
        break
      else:
        raise Exception("Invalid MDL3 command type: %02X" % command_type)
    
    return offset
  
  def save(self, offset: int):
    orig_offset = offset
    
    self.chan_color_subpacket_offset = None
    self.chan_control_subpacket_offset = None
    self.tex_gen_subpacket_offset = None
    self.texture_subpacket_offset = None # TODO
    self.tev_subpacket_offset = None
    self.pixel_subpacket_offset = None
    
    for command in self.bp_commands:
      if self.tev_subpacket_offset is None and (isinstance(command, TEV_REGISTERL) or isinstance(command, TEV_REGISTERH)):
        self.tev_subpacket_offset = offset - orig_offset
      if self.pixel_subpacket_offset is None and command.register in [BPRegister.TEV_FOG_PARAM_0, BPRegister.TEV_FOG_PARAM_1, BPRegister.TEV_FOG_PARAM_2, BPRegister.TEV_FOG_PARAM_3]:
        self.pixel_subpacket_offset = offset - orig_offset
      
      offset = command.save(offset)
    
    for command in self.xf_commands:
      if self.chan_color_subpacket_offset is None and command.register in [XFRegister.CHAN0_AMBCOLOR, XFRegister.CHAN0_MATCOLOR]:
        self.chan_color_subpacket_offset = offset - orig_offset
      if self.chan_control_subpacket_offset is None and command.register in [XFRegister.CHAN0_COLOR]:
        self.chan_control_subpacket_offset = offset - orig_offset
      if self.tex_gen_subpacket_offset is None and (isinstance(command, TEXMTX) or command.register in [XFRegister.TEXMTXINFO]):
        self.tex_gen_subpacket_offset = offset - orig_offset
      
      offset = command.save(offset)
    
    if offset % 0x20 != 0:
      padding_bytes_needed = (0x20 - (offset % 0x20))
      padding = b"\0"*padding_bytes_needed
      fs.write_bytes(self.data, offset, padding)
      offset += padding_bytes_needed
    
    return offset

@bunfoe
class MDL3(JChunk):
  num_entries           : u16
  _padding_1            : u16 = 0xFFFF
  packets_offset        : u32
  subpackets_offset     : u32
  matrix_index_offset   : u32
  unknown_0_offset      : u32
  indexes_offset        : u32
  mat_names_table_offset: u32
  
  def read_chunk_specific_data(self):
    BUNFOE.read(self, 0)
    
    self.entries: list[MDLEntry] = []
    packet_offset = self.packets_offset
    for i in range(self.num_entries):
      entry_offset = packet_offset + fs.read_u32(self.data, packet_offset + 0x00)
      entry_size = fs.read_u32(self.data, packet_offset + 0x04)
      entry = MDLEntry(self.data)
      entry.read(entry_offset, entry_size)
      self.entries.append(entry)
      packet_offset += 8
    
    self.string_table_offset = fs.read_u32(self.data, 0x20)
    self.mat_names = self.read_string_table(self.string_table_offset)
  
  def save_chunk_specific_data(self):
    self.data.truncate(0x40)
    
    self.num_entries = len(self.entries)
    
    self.packets_offset = fs.data_len(self.data)
    packet_offset = self.packets_offset
    entry_offset = self.packets_offset + 8*len(self.entries)
    for entry in self.entries:
      next_entry_offset = entry.save(entry_offset)
      entry_size = next_entry_offset - entry_offset
      fs.write_u32(self.data, packet_offset+0, entry_offset - packet_offset)
      fs.write_u32(self.data, packet_offset+4, entry_size)
      entry_offset = next_entry_offset
      packet_offset += 8
    offset = entry_offset
    offset = fs.align_data_and_pad_offset(self.data, offset, 4)
    
    self.subpackets_offset = fs.data_len(self.data)
    for entry in self.entries:
      fs.write_u16(self.data, offset+0x00, entry.chan_color_subpacket_offset or 0)
      fs.write_u16(self.data, offset+0x02, entry.chan_control_subpacket_offset or 0)
      fs.write_u16(self.data, offset+0x04, entry.tex_gen_subpacket_offset or 0)
      fs.write_u16(self.data, offset+0x06, entry.texture_subpacket_offset or 0)
      fs.write_u16(self.data, offset+0x08, entry.tev_subpacket_offset or 0)
      fs.write_u16(self.data, offset+0x0A, entry.pixel_subpacket_offset or 0)
      fs.write_s32(self.data, offset+0x0C, -1) # Padding
      offset += 0x10
    offset = fs.align_data_and_pad_offset(self.data, offset, 4)
    
    # TODO placeholder
    self.matrix_index_offset = fs.data_len(self.data)
    for entry in self.entries:
      fs.write_bytes(self.data, offset, b'\0'*8)
      offset += 8
    offset = fs.align_data_and_pad_offset(self.data, offset, 4)
    
    # TODO placeholder
    self.unknown_0_offset = fs.data_len(self.data)
    for entry in self.entries:
      fs.write_bytes(self.data, offset, b'\0'*1)
      offset += 1
    offset = fs.align_data_and_pad_offset(self.data, offset, 4)
    
    # TODO placeholder
    self.indexes_offset = fs.data_len(self.data)
    for entry in self.entries:
      fs.write_bytes(self.data, offset, b'\0'*2)
      offset += 2
    offset = fs.align_data_and_pad_offset(self.data, offset, 4)
    
    # Write the material names.
    self.mat_names_table_offset = offset
    offset = self.write_string_table(self.mat_names_table_offset, self.mat_names)
    offset = fs.align_data_and_pad_offset(self.data, offset, 4)
    
    # Finally, save the new offsets to each list back to the header.
    BUNFOE.save(self, 0)
