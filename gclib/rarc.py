
import os
from io import BytesIO
from enum import IntFlag
from typing import Type, TypeVar

from gclib import fs_helpers as fs
from gclib.gclib_file import GCLibFile, GCLibFileEntry
from gclib.yaz0_yay0 import Yaz0, Yay0

GCLibFileT = TypeVar('GCLibFileT', bound=GCLibFile)

class RARC(GCLibFile):
  def __init__(self, flexible_data = None):
    super().__init__(flexible_data)
    
    self.magic = "RARC"
    self.size = None
    self.data_header_offset = None
    self.file_data_list_offset = None
    self.total_file_data_size = None
    self.mram_file_data_size = None
    self.aram_file_data_size = None
    self.unknown_1 = 0
    
    self.num_nodes = 0
    self.node_list_offset = None
    self.total_num_file_entries = 0
    self.file_entries_list_offset = None
    self.string_list_size = None
    self.string_list_offset = None
    self.next_free_file_id = 0
    self.keep_file_ids_synced_with_indexes = 1
    self.unknown_2 = 0
    self.unknown_3 = 0
    
    self.nodes: list[RARCNode] = []
    self.file_entries: list[RARCFileEntry] = []
    self.instantiated_object_files = {}
    
    if flexible_data is not None:
      self.read()
  
  @classmethod
  def check_file_is_rarc(cls, data: BytesIO):
    if fs.data_len(data) < 4:
      return False
    if fs.read_bytes(data, 0, 4) != b"RARC":
      return False
    return True
  
  def read(self):
    # Read header.
    self.magic = fs.read_str(self.data, 0, 4)
    assert self.magic == "RARC"
    self.size = fs.read_u32(self.data, 4)
    self.data_header_offset = fs.read_u32(self.data, 0x8)
    assert self.data_header_offset == 0x20
    self.file_data_list_offset = fs.read_u32(self.data, 0xC) + self.data_header_offset
    self.total_file_data_size = fs.read_u32(self.data, 0x10)
    self.mram_file_data_size = fs.read_u32(self.data, 0x14)
    self.aram_file_data_size = fs.read_u32(self.data, 0x18)
    self.unknown_1 = fs.read_u32(self.data, 0x1C)
    assert self.unknown_1 == 0
    
    # Read data header.
    self.num_nodes = fs.read_u32(self.data, self.data_header_offset + 0x00)
    self.node_list_offset = fs.read_u32(self.data, self.data_header_offset + 0x04) + self.data_header_offset
    self.total_num_file_entries = fs.read_u32(self.data, self.data_header_offset + 0x08)
    self.file_entries_list_offset = fs.read_u32(self.data, self.data_header_offset + 0x0C) + self.data_header_offset
    self.string_list_size = fs.read_u32(self.data, self.data_header_offset + 0x10)
    self.string_list_offset = fs.read_u32(self.data, self.data_header_offset + 0x14) + self.data_header_offset
    self.next_free_file_id = fs.read_u16(self.data, self.data_header_offset + 0x18)
    self.keep_file_ids_synced_with_indexes = fs.read_u8(self.data, self.data_header_offset + 0x1A)
    self.unknown_2 = fs.read_u8(self.data, self.data_header_offset + 0x1B)
    assert self.unknown_2 == 0
    self.unknown_3 = fs.read_u32(self.data, self.data_header_offset + 0x1C)
    assert self.unknown_3 == 0
    
    self.nodes = []
    for node_index in range(self.num_nodes):
      offset = self.node_list_offset + node_index*RARCNode.ENTRY_SIZE
      node = RARCNode(self)
      node.read(offset)
      self.nodes.append(node)
    
    self.file_entries = []
    for file_index in range(self.total_num_file_entries):
      file_entry_offset = self.file_entries_list_offset + file_index*RARCFileEntry.ENTRY_SIZE
      file_entry = RARCFileEntry(self)
      file_entry.read(file_entry_offset)
      self.file_entries.append(file_entry)
      
      if file_entry.is_dir and file_entry.node_index != 0xFFFFFFFF:
        file_entry.node = self.nodes[file_entry.node_index]
        if file_entry.name not in [".", ".."]:
          assert file_entry.node.dir_entry is None, "Duplicate node index 0x%02X (%s)." % (file_entry.node_index, file_entry.node.name)
          file_entry.node.dir_entry = file_entry
    
    for node in self.nodes:
      for file_index in range(node.first_file_index, node.first_file_index+node.num_files):
        file_entry = self.file_entries[file_index]
        file_entry.parent_node = node
        node.files.append(file_entry)
    
    self.instantiated_object_files = {}
  
  def add_root_directory(self):
    root_node = RARCNode(self)
    root_node.type = "ROOT"
    root_node.name = "archive"
    self.nodes.append(root_node)
    
    dot_entry = RARCFileEntry(self)
    dot_entry.name = "."
    dot_entry.type = RARCFileAttrType.DIRECTORY
    dot_entry.node = root_node
    dot_entry.parent_node = root_node
    
    dotdot_entry = RARCFileEntry(self)
    dotdot_entry.name = ".."
    dotdot_entry.type = RARCFileAttrType.DIRECTORY
    dotdot_entry.node = None
    dotdot_entry.parent_node = root_node
    
    root_node.files.append(dot_entry)
    root_node.files.append(dotdot_entry)
    
    self.regenerate_all_file_entries_list()
  
  def add_new_directory(self, dir_name: str, node_type: str, parent_node: 'RARCNode'):
    if len(node_type) > 4:
      raise Exception("Node type must not be longer than 4 characters: %s" % node_type)
    if len(node_type) < 4:
      spaces_to_add = 4-len(node_type)
      node_type += " "*spaces_to_add
    
    node = RARCNode(self)
    node.type = node_type
    node.name = dir_name
    
    dir_entry = RARCFileEntry(self)
    dir_entry.name = dir_name
    dir_entry.type = RARCFileAttrType.DIRECTORY
    dir_entry.node = node
    dir_entry.parent_node = parent_node
    
    dot_entry = RARCFileEntry(self)
    dot_entry.name = "."
    dot_entry.type = RARCFileAttrType.DIRECTORY
    dot_entry.node = node
    dot_entry.parent_node = node
    
    dotdot_entry = RARCFileEntry(self)
    dotdot_entry.name = ".."
    dotdot_entry.type = RARCFileAttrType.DIRECTORY
    dotdot_entry.node = parent_node
    dotdot_entry.parent_node = node
    
    self.nodes.append(node)
    parent_node.files.append(dir_entry)
    node.files.append(dot_entry)
    node.files.append(dotdot_entry)
    node.dir_entry = dir_entry
    
    self.regenerate_all_file_entries_list()
    
    return dir_entry, node
  
  def add_new_file(self, file_name: str, file_data: BytesIO, node: 'RARCNode'):
    file_entry = RARCFileEntry(self)
    
    if not self.keep_file_ids_synced_with_indexes:
      if self.next_free_file_id == 0xFFFF:
        raise Exception("Next free file ID in RARC is 0xFFFF. Cannot add new file.")
      file_entry.id = self.next_free_file_id
      self.next_free_file_id += 1
    
    file_entry.type = RARCFileAttrType.FILE
    if file_name.endswith(".rel"):
      file_entry.type |= RARCFileAttrType.PRELOAD_TO_ARAM
    else:
      file_entry.type |= RARCFileAttrType.PRELOAD_TO_MRAM
    
    file_entry.name = file_name
    
    file_entry.data = file_data
    file_entry.data_size = fs.data_len(file_entry.data)
    
    file_entry.parent_node = node
    node.files.append(file_entry)
    
    self.regenerate_all_file_entries_list()
    
    return file_entry
  
  def delete_directory(self, dir_entry: 'RARCFileEntry'):
    assert dir_entry.name not in [".", ".."]
    assert dir_entry.node is not None
    
    node = dir_entry.node
    
    dir_entry.parent_node.files.remove(dir_entry)
    
    self.nodes.remove(node)
    
    # Recursively delete subdirectories.
    for file_entry in node.files:
      if file_entry.is_dir and file_entry.name not in [".", ".."]:
        self.delete_directory(file_entry)
    
    self.regenerate_all_file_entries_list()
  
  def delete_file(self, file_entry: 'RARCFileEntry'):
    file_entry.parent_node.files.remove(file_entry)
    
    self.regenerate_all_file_entries_list()
  
  def regenerate_all_file_entries_list(self):
    # Regenerate the list of all file entries so they're all together for the nodes, and update the first_file_index of the nodes.
    self.file_entries = []
    self.regenerate_files_list_for_node(self.nodes[0])
    
    if self.keep_file_ids_synced_with_indexes:
      self.next_free_file_id = len(self.file_entries)
      
      for file_entry in self.file_entries:
        if not file_entry.is_dir:
          file_entry.id = self.file_entries.index(file_entry)
  
  def regenerate_files_list_for_node(self, node: 'RARCNode'):
    # Sort the . and .. directory entries to be at the end of the node's file list.
    rel_dir_entries = []
    for file_entry in node.files:
      if file_entry.is_dir and file_entry.name in [".", ".."]:
        rel_dir_entries.append(file_entry)
    for rel_dir_entry in rel_dir_entries:
      node.files.remove(rel_dir_entry)
      node.files.append(rel_dir_entry)
    
    node.first_file_index = len(self.file_entries)
    self.file_entries += node.files
    
    # Recursively add this directory's subdirectory nodes.
    for file_entry in node.files:
      if file_entry.is_dir and file_entry.name not in [".", ".."]:
        self.regenerate_files_list_for_node(file_entry.node)
  
  def extract_all_files_to_disk_flat(self, output_directory: str):
    # Does not preserve directory structure.
    if not os.path.isdir(output_directory):
      os.mkdir(output_directory)
    
    for file_entry in self.file_entries:
      if file_entry.is_dir:
        continue
      
      output_file_path = os.path.join(output_directory, file_entry.name)
      
      file_entry.data.seek(0)
      with open(output_file_path, "wb") as f:
        f.write(file_entry.data.read())
  
  def extract_all_files_to_disk(self, output_directory: str):
    # Preserves directory structure.
    root_node = self.nodes[0]
    self.extract_node_to_disk(root_node, output_directory)
  
  def extract_node_to_disk(self, node: 'RARCNode', path: str):
    if not os.path.isdir(path):
      os.mkdir(path)
    
    for file in node.files:
      if file.is_dir:
        if file.name not in [".", ".."]:
          subdir_path = os.path.join(path, file.name)
          subdir_node = self.nodes[file.node_index]
          self.extract_node_to_disk(subdir_node, subdir_path)
      else:
        file_path = os.path.join(path, file.name)
        file.data.seek(0)
        with open(file_path, "wb") as f:
          f.write(file.data.read())
  
  def import_all_files_from_disk(self, input_directory: str):
    root_node = self.nodes[0]
    return self.import_node_from_disk(root_node, input_directory)
  
  def import_node_from_disk(self, node: 'RARCNode', path: str):
    num_files_overwritten = 0
    
    for file in node.files:
      if file.is_dir:
        if file.name not in [".", ".."]:
          subdir_path = os.path.join(path, file.name)
          subdir_node = self.nodes[file.node_index]
          num_files_overwritten += self.import_node_from_disk(subdir_node, subdir_path)
      else:
        file_path = os.path.join(path, file.name)
        if os.path.isfile(file_path):
          with open(file_path, "rb") as f:
            data = BytesIO(f.read())
            file.data = data
            num_files_overwritten += 1
    
    return num_files_overwritten
  
  def each_file_data(self, only_file_exts: list[str] | None = None):
    for file_entry in self.file_entries:
      if file_entry.is_dir:
        continue
      base_name, file_ext = os.path.splitext(file_entry.name)
      rel_dir = file_entry.parent_node.name
      display_path = rel_dir + "/" + base_name + file_ext
      
      if file_ext == ".arc":
        inner_rarc = self.get_file(file_entry.name, RARC)
        for inner_rarc_file_path, file_data in inner_rarc.each_file_data(only_file_exts=only_file_exts):
          yield (display_path + "/" + inner_rarc_file_path, file_data)
      else:
        if only_file_exts is not None and file_ext not in only_file_exts:
          continue
        file_entry.decompress_data_if_necessary()
        yield (display_path, file_entry.data)
  
  def save_changes(self):
    # Repacks the .arc file.
    # Supports files changing size, name, files being added or removed, nodes being added or removed, etc.
    
    # Cut off all the data since we're replacing it entirely.
    self.node_list_offset = 0x40
    self.data.truncate(0)
    self.data.seek(self.node_list_offset)
    
    # Assign the node offsets for each node, but don't actually save them yet because we need to write their names first.
    next_node_offset = self.node_list_offset
    for node in self.nodes:
      node.node_offset = next_node_offset
      self.data.seek(node.node_offset)
      self.data.write(b'\0'*RARCNode.ENTRY_SIZE)
      next_node_offset += RARCNode.ENTRY_SIZE
    
    # Reorders the self.file_entries list and sets the first_file_index field for each node.
    self.regenerate_all_file_entries_list()
    
    # Assign the entry offsets for each file entry, but don't actually save them yet because we need to write their data and names first.
    fs.align_data_to_nearest(self.data, 0x20, padding_bytes=b'\0')
    self.file_entries_list_offset = self.data.tell()
    next_file_entry_offset = self.file_entries_list_offset
    for file_entry in self.file_entries:
      file_entry.entry_offset = next_file_entry_offset
      self.data.seek(file_entry.entry_offset)
      self.data.write(b'\0'*RARCFileEntry.ENTRY_SIZE)
      next_file_entry_offset += RARCFileEntry.ENTRY_SIZE
    
    # Write the strings for the node names and file entry names.
    fs.align_data_to_nearest(self.data, 0x20)
    self.string_list_offset = self.data.tell()
    offsets_for_already_written_strings = {}
    # The dots for the current and parent directories are always written first.
    fs.write_str_with_null_byte(self.data, self.string_list_offset+0, ".")
    offsets_for_already_written_strings["."] = 0
    fs.write_str_with_null_byte(self.data, self.string_list_offset+2, "..")
    offsets_for_already_written_strings[".."] = 2
    next_string_offset = 5
    for file_entry in self.nodes + self.file_entries:
      string = file_entry.name
      if string in offsets_for_already_written_strings:
        offset = offsets_for_already_written_strings[string]
      else:
        offset = next_string_offset
        fs.write_str_with_null_byte(self.data, self.string_list_offset+offset, string)
        next_string_offset += len(string) + 1
        offsets_for_already_written_strings[string] = offset
      file_entry.name_offset = offset
    
    # Save the nodes.
    for node in self.nodes:
      node.save_changes()
    
    # Write the file data, and save the file entries as well.
    # Main RAM file entries must all be in a row before the ARAM file entries.
    fs.align_data_to_nearest(self.data, 0x20)
    self.file_data_list_offset = self.data.tell()
    mram_preload_file_entries: list[RARCFileEntry] = []
    aram_preload_file_entries: list[RARCFileEntry] = []
    no_preload_file_entries: list[RARCFileEntry] = []
    for file_entry in self.file_entries:
      if file_entry.is_dir:
        if file_entry.node is None:
          file_entry.node_index = 0xFFFFFFFF
        else:
          file_entry.node_index = self.nodes.index(file_entry.node)
        
        file_entry.save_changes()
      else:
        if file_entry.type & RARCFileAttrType.PRELOAD_TO_MRAM != 0:
          mram_preload_file_entries.append(file_entry)
        elif file_entry.type & RARCFileAttrType.PRELOAD_TO_ARAM != 0:
          aram_preload_file_entries.append(file_entry)
        elif file_entry.type & RARCFileAttrType.LOAD_FROM_DVD != 0:
          no_preload_file_entries.append(file_entry)
        else:
          raise Exception("File entry %s is not set as being loaded into any type of RAM." % file_entry.name)
    
    def write_file_entry_data(file_entry: RARCFileEntry):
      nonlocal next_file_data_offset
      
      if self.keep_file_ids_synced_with_indexes:
        file_entry.id = self.file_entries.index(file_entry)
      
      file_entry.data_offset = next_file_data_offset
      file_entry.save_changes()
      
      self.data.seek(self.file_data_list_offset + file_entry.data_offset)
      file_entry.data.seek(0)
      self.data.write(file_entry.data.read())
      
      next_file_data_offset += file_entry.data_size
      
      # Pad start of the next file to the next 0x20 bytes.
      fs.align_data_to_nearest(self.data, 0x20)
      next_file_data_offset = self.data.tell() - self.file_data_list_offset
    
    next_file_data_offset = 0
    
    for file_entry in mram_preload_file_entries:
      write_file_entry_data(file_entry)
    self.mram_file_data_size = next_file_data_offset
  
    for file_entry in aram_preload_file_entries:
      write_file_entry_data(file_entry)
    self.aram_file_data_size = next_file_data_offset - self.mram_file_data_size
    
    for file_entry in no_preload_file_entries:
      write_file_entry_data(file_entry)
    
    self.total_file_data_size = next_file_data_offset
    
    # Update the header.
    fs.write_magic_str(self.data, 0x00, self.magic, 4)
    self.size = self.file_data_list_offset + self.total_file_data_size
    fs.write_u32(self.data, 0x04, self.size)
    self.data_header_offset = 0x20
    fs.write_u32(self.data, 0x08, self.data_header_offset)
    fs.write_u32(self.data, 0x0C, self.file_data_list_offset-0x20)
    fs.write_u32(self.data, 0x10, self.total_file_data_size)
    fs.write_u32(self.data, 0x14, self.mram_file_data_size)
    fs.write_u32(self.data, 0x18, self.aram_file_data_size)
    fs.write_u32(self.data, 0x1C, 0)
    
    # Update the data header.
    self.num_nodes = len(self.nodes)
    fs.write_u32(self.data, self.data_header_offset + 0x00, self.num_nodes)
    self.total_num_file_entries = len(self.file_entries)
    fs.write_u32(self.data, self.data_header_offset + 0x04, self.node_list_offset - self.data_header_offset)
    fs.write_u32(self.data, self.data_header_offset + 0x08, self.total_num_file_entries)
    fs.write_u32(self.data, self.data_header_offset + 0x0C, self.file_entries_list_offset - self.data_header_offset)
    self.string_list_size = self.file_data_list_offset - self.string_list_offset
    fs.write_u32(self.data, self.data_header_offset + 0x10, self.string_list_size)
    fs.write_u32(self.data, self.data_header_offset + 0x14, self.string_list_offset - self.data_header_offset)
    fs.write_u16(self.data, self.data_header_offset + 0x18, self.next_free_file_id)
    fs.write_u8(self.data, self.data_header_offset + 0x1A, self.keep_file_ids_synced_with_indexes)
    fs.write_u8(self.data, self.data_header_offset + 0x1B, 0)
    fs.write_u32(self.data, self.data_header_offset + 0x1C, 0)
  
  def get_node_by_path(self, path: str):
    if path in ["", "."]:
      # Root node
      return self.nodes[0]
    
    for node in self.nodes[1:]:
      assert node.dir_entry is not None
      curr_path = node.dir_entry.name
      curr_node = node.dir_entry.parent_node
      while curr_node is not None:
        if curr_node == self.nodes[0]:
          # Root node
          break
        assert curr_node.dir_entry is not None
        curr_path = "%s/%s" % (curr_node.dir_entry.name, curr_path)
        curr_node = curr_node.dir_entry.parent_node
      
      if curr_path == path:
        return node
  
  def get_file_entry(self, file_name: str) -> 'RARCFileEntry':
    for file_entry in self.file_entries:
      if file_entry.name == file_name:
        return file_entry
    return None
  
  def get_file(self, file_name: str, file_type: Type[GCLibFileT]) -> GCLibFileT:
    if file_name in self.instantiated_object_files:
      return self.instantiated_object_files[file_name]
    
    file_entry = self.get_file_entry(file_name)
    if file_entry is None:
      return None
    
    file_instance = file_type(file_entry)
    self.instantiated_object_files[file_name] = file_instance
    return file_instance

class RARCNode:
  ENTRY_SIZE = 0x10
  
  def __init__(self, rarc: RARC):
    self.rarc = rarc
    
    self.type: str = None
    self.name_offset: int = None
    self.name_hash: int = None
    self.name: str = None
    self.files: list[RARCFileEntry] = [] # This will be populated after the file entries have been read.
    self.num_files: int = 0
    self.first_file_index: int = None
    self.dir_entry: RARCFileEntry | None = None # This will be populated when the corresponding directory entry is read. (The root node has no dir_entry.)
  
  def read(self, node_offset: int):
    self.node_offset = node_offset
    
    self.type = fs.read_str(self.rarc.data, self.node_offset+0x00, 4)
    self.name_offset = fs.read_u32(self.rarc.data, self.node_offset+0x04)
    self.name_hash = fs.read_u16(self.rarc.data, self.node_offset+0x08)
    self.num_files = fs.read_u16(self.rarc.data, self.node_offset+0x0A)
    self.first_file_index = fs.read_u32(self.rarc.data, self.node_offset+0x0C)
    
    self.name = fs.read_str_until_null_character(self.rarc.data, self.rarc.string_list_offset + self.name_offset)
  
  def save_changes(self):
    hash = 0
    for char in self.name:
      hash *= 3
      hash += ord(char)
      hash &= 0xFFFF
    self.name_hash = hash
    
    self.num_files = len(self.files)
    
    fs.write_magic_str(self.rarc.data, self.node_offset+0x00, self.type, 4)
    fs.write_u32(self.rarc.data, self.node_offset+0x04, self.name_offset)
    fs.write_u16(self.rarc.data, self.node_offset+0x08, self.name_hash)
    fs.write_u16(self.rarc.data, self.node_offset+0x0A, self.num_files)
    fs.write_u32(self.rarc.data, self.node_offset+0x0C, self.first_file_index)
  
  def __str__(self):
    return f"<{self.__class__.__name__}: {self.type!r}>"
  
  def __repr__(self):
    return str(self)

class RARCFileEntry(GCLibFileEntry):
  ENTRY_SIZE = 0x14
  
  def __init__(self, rarc: RARC):
    super().__init__()
    
    self.rarc = rarc
    
    self.parent_node: RARCNode = None
    self.id: int = 0xFFFF
    self.name_hash: int = None
    self.data_size: int = 0
    self.data: BytesIO | None = None # None for directories.
    self.type: RARCFileAttrType = None
    self.name_offset: int = None
    self.name: str = None
    self.node: RARCNode | None = None # Only None for the root node's ".." entry.
  
  def read(self, entry_offset: int):
    self.entry_offset = entry_offset
    
    self.id = fs.read_u16(self.rarc.data, entry_offset)
    self.name_hash = fs.read_u16(self.rarc.data, entry_offset + 2)
    type_and_name_offset = fs.read_u32(self.rarc.data, entry_offset + 4)
    data_offset_or_node_index = fs.read_u32(self.rarc.data, entry_offset + 8)
    self.data_size = fs.read_u32(self.rarc.data, entry_offset + 0xC)
    
    self.type = RARCFileAttrType((type_and_name_offset & 0xFF000000) >> 24)
    
    self.name_offset = type_and_name_offset & 0x00FFFFFF
    self.name = fs.read_str_until_null_character(self.rarc.data, self.rarc.string_list_offset + self.name_offset)
    
    if self.is_dir:
      assert self.data_size == 0x10
      self.node_index = data_offset_or_node_index
      self.node = None # This will be populated later.
      self.data = None
    else:
      self.data_offset = data_offset_or_node_index
      absolute_data_offset = self.rarc.file_data_list_offset + self.data_offset
      self.rarc.data.seek(absolute_data_offset)
      self.data = BytesIO(self.rarc.data.read(self.data_size))
  
  @property
  def is_dir(self):
    return (self.type & RARCFileAttrType.DIRECTORY) != 0
  
  @is_dir.setter
  def is_dir(self, value: bool):
    if value:
      self.type |= RARCFileAttrType.DIRECTORY
    else:
      self.type &= ~RARCFileAttrType.DIRECTORY
  
  def decompress_data_if_necessary(self) -> bool:
    was_compressed = super().decompress_data_if_necessary()
    if was_compressed:
      self.update_compression_flags_from_data()
    return was_compressed
  
  def update_compression_flags_from_data(self):
    if self.is_dir:
      self.type &= ~RARCFileAttrType.COMPRESSED
      self.type &= ~RARCFileAttrType.YAZ0_COMPRESSED
      return
    
    if Yaz0.check_is_compressed(self.data):
      self.type |= RARCFileAttrType.COMPRESSED
      self.type |= RARCFileAttrType.YAZ0_COMPRESSED
    elif Yay0.check_is_compressed(self.data):
      self.type |= RARCFileAttrType.COMPRESSED
      self.type &= ~RARCFileAttrType.YAZ0_COMPRESSED
    else:
      self.type &= ~RARCFileAttrType.COMPRESSED
      self.type &= ~RARCFileAttrType.YAZ0_COMPRESSED
  
  def check_is_nested_rarc(self) -> bool:
    if self.is_dir:
      return False
    assert self.data is not None
    try:
      _, file_ext = os.path.splitext(self.name)
      if file_ext in [".arc", ".szs", ".szp"]:
        if Yaz0.check_is_compressed(self.data):
          magic = fs.read_str(self.data, 0x11, 4)
          if magic == "RARC":
            return True
        elif Yay0.check_is_compressed(self.data):
          chunk_offset = fs.read_u32(self.data, 0xC)
          magic = fs.read_str(self.data, chunk_offset, 4)
          if magic == "RARC":
            return True
        elif RARC.check_file_is_rarc(self.data):
          return True
    except Exception as e:
      pass
    return False
  
  def save_changes(self):
    hash = 0
    for char in self.name:
      hash *= 3
      hash += ord(char)
      hash &= 0xFFFF
    self.name_hash = hash
    
    self.update_compression_flags_from_data()
    
    type_and_name_offset = (self.type << 24) | (self.name_offset & 0x00FFFFFF)
    
    if self.is_dir:
      data_offset_or_node_index = self.node_index
      self.data_size = 0x10
    else:
      data_offset_or_node_index = self.data_offset
      self.data_size = fs.data_len(self.data)
    
    fs.write_u16(self.rarc.data, self.entry_offset+0x00, self.id)
    fs.write_u16(self.rarc.data, self.entry_offset+0x02, self.name_hash)
    fs.write_u32(self.rarc.data, self.entry_offset+0x04, type_and_name_offset)
    fs.write_u32(self.rarc.data, self.entry_offset+0x08, data_offset_or_node_index)
    fs.write_u32(self.rarc.data, self.entry_offset+0x0C, self.data_size)
    fs.write_u32(self.rarc.data, self.entry_offset+0x10, 0) # Pointer to the file's data, filled at runtime.
  
  def __str__(self):
    return f"<{self.__class__.__name__}: {self.name!r}>"
  
  def __repr__(self):
    return str(self)

class RARCFileAttrType(IntFlag):
  FILE            = 0x01
  DIRECTORY       = 0x02
  COMPRESSED      = 0x04
  PRELOAD_TO_MRAM = 0x10
  PRELOAD_TO_ARAM = 0x20
  LOAD_FROM_DVD   = 0x40
  YAZ0_COMPRESSED = 0x80
