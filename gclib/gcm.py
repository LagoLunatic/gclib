
import os
from io import BytesIO
from typing import BinaryIO
import re

from gclib import fs_helpers as fs
from gclib.rarc import RARC
from gclib.yaz0_yay0 import Yaz0, Yay0

MAX_DATA_SIZE_TO_READ_AT_ONCE = 64*1024*1024 # 64MB

class GCM:
  def __init__(self, iso_path):
    self.iso_path = iso_path
    self.files_by_path: dict[str, GCMBaseFile] = {}
    self.files_by_path_lowercase: dict[str, GCMBaseFile] = {}
    self.dirs_by_path: dict[str, GCMBaseFile] = {}
    self.dirs_by_path_lowercase: dict[str, GCMBaseFile] = {}
    self.changed_files: dict[str, BinaryIO] = {}
  
  def read_entire_disc(self):
    self.iso_file = open(self.iso_path, "rb")
    
    try:
      self.fst_offset = fs.read_u32(self.iso_file, 0x424)
      self.fst_size = fs.read_u32(self.iso_file, 0x428)
      self.read_filesystem()
      self.read_system_data()
    finally:
      self.iso_file.close()
      self.iso_file = None
    
    for file_path, file_entry in self.files_by_path.items():
      self.files_by_path_lowercase[file_path.lower()] = file_entry
    for dir_path, file_entry in self.dirs_by_path.items():
      self.dirs_by_path_lowercase[dir_path.lower()] = file_entry
  
  def read_filesystem(self):
    self.file_entries = []
    num_file_entries = fs.read_u32(self.iso_file, self.fst_offset + 8)
    self.fnt_offset = self.fst_offset + num_file_entries*0xC
    for file_index in range(num_file_entries):
      file_entry_offset = self.fst_offset + file_index * 0xC
      file_entry = GCMFileEntry()
      file_entry.read(file_index, self.iso_file, file_entry_offset, self.fnt_offset)
      self.file_entries.append(file_entry)
    
    root_file_entry = self.file_entries[0]
    root_file_entry.file_path = "files"
    self.read_directory(root_file_entry, "files")
  
  def read_directory(self, directory_file_entry, dir_path):
    assert directory_file_entry.is_dir
    self.dirs_by_path[dir_path] = directory_file_entry
    
    i = directory_file_entry.file_index + 1
    while i < directory_file_entry.next_fst_index:
      file_entry = self.file_entries[i]
      
      # Set parent/children relationships
      file_entry.parent = directory_file_entry
      directory_file_entry.children.append(file_entry)
      
      if file_entry.is_dir:
        assert directory_file_entry.file_index == file_entry.parent_fst_index
        subdir_path = dir_path + "/" + file_entry.name
        file_entry.file_path = subdir_path
        self.read_directory(file_entry, subdir_path)
        i = file_entry.next_fst_index
      else:
        file_path = dir_path + "/" + file_entry.name
        self.files_by_path[file_path] = file_entry
        file_entry.file_path = file_path
        i += 1
  
  def read_system_data(self):
    self.files_by_path["sys/boot.bin"] = GCMSystemFile(0, 0x440, "boot.bin")
    self.files_by_path["sys/bi2.bin"] = GCMSystemFile(0x440, 0x2000, "bi2.bin")
    
    apploader_header_size = 0x20
    apploader_size = fs.read_u32(self.iso_file, 0x2440 + 0x14)
    apploader_trailer_size = fs.read_u32(self.iso_file, 0x2440 + 0x18)
    apploader_full_size = apploader_header_size + apploader_size + apploader_trailer_size
    self.files_by_path["sys/apploader.img"] = GCMSystemFile(0x2440, apploader_full_size, "apploader.img")
    
    dol_offset = fs.read_u32(self.iso_file, 0x420)
    main_dol_size = 0
    for i in range(7): # Text sections
      section_offset = fs.read_u32(self.iso_file, dol_offset + 0x00 + i*4)
      section_size = fs.read_u32(self.iso_file, dol_offset + 0x90 + i*4)
      section_end_offset = section_offset + section_size
      if section_end_offset > main_dol_size:
        main_dol_size = section_end_offset
    for i in range(11): # Data sections
      section_offset = fs.read_u32(self.iso_file, dol_offset + 0x1C + i*4)
      section_size = fs.read_u32(self.iso_file, dol_offset + 0xAC + i*4)
      section_end_offset = section_offset + section_size
      if section_end_offset > main_dol_size:
        main_dol_size = section_end_offset
    self.files_by_path["sys/main.dol"] = GCMSystemFile(dol_offset, main_dol_size, "main.dol")
    
    self.files_by_path["sys/fst.bin"] = GCMSystemFile(self.fst_offset, self.fst_size, "fst.bin")
    
    self.system_files = [
      self.files_by_path["sys/boot.bin"],
      self.files_by_path["sys/bi2.bin"],
      self.files_by_path["sys/apploader.img"],
      self.files_by_path["sys/main.dol"],
      self.files_by_path["sys/fst.bin"],
    ]
  
  def read_file_data(self, file_path):
    file_path = file_path.lower()
    if file_path not in self.files_by_path_lowercase:
      raise Exception("Could not find file: " + file_path)
    
    file_entry = self.files_by_path_lowercase[file_path]
    if file_entry.file_size > MAX_DATA_SIZE_TO_READ_AT_ONCE:
      raise Exception("Tried to read a very large file all at once")
    with open(self.iso_path, "rb") as iso_file:
      data = fs.read_bytes(iso_file, file_entry.file_data_offset, file_entry.file_size)
    data = BytesIO(data)
    
    return data
  
  def read_file_raw_data(self, file_path):
    file_path = file_path.lower()
    if file_path not in self.files_by_path_lowercase:
      raise Exception("Could not find file: " + file_path)
    
    file_entry = self.files_by_path_lowercase[file_path]
    with open(self.iso_path, "rb") as iso_file:
      data = fs.read_bytes(iso_file, file_entry.file_data_offset, file_entry.file_size)
    
    return data
  
  def get_or_create_dir_file_entry(self, dir_path):
    if dir_path.lower() in self.dirs_by_path_lowercase:
      return self.dirs_by_path_lowercase[dir_path.lower()]
    else:
      return self.add_new_directory(dir_path)
  
  def import_all_files_from_disk(self, input_directory):
    num_files_overwritten = 0
    
    for file_path, file_entry in self.files_by_path.items():
      full_file_path = os.path.join(input_directory, file_path)
      if os.path.isfile(full_file_path):
        with open(full_file_path, "rb") as f:
          self.changed_files[file_path] = BytesIO(f.read())
          num_files_overwritten += 1
    
    return num_files_overwritten
  
  def collect_files_to_replace_and_add_from_disk(self, input_directory, base_dir=None):
    # Creates lists of files in a folder, separated by ones that would replace existing files in the GCM and ones that are new.
    # base_dir can optionally be a GCMFileEntry to use as the root directory of the replacement.
    # If unspecified, the entire GCM will be treated as the root instead.
    
    path_prefix = ""
    if base_dir is not None:
      path_prefix = f"{base_dir.file_path}/"
    
    replace_paths = []
    add_paths = []
    for dir_path, subdir_names, file_names in os.walk(input_directory):
      for file_name in file_names:
        file_path = os.path.join(dir_path, file_name)
        relative_file_path = os.path.relpath(file_path, input_directory)
        relative_file_path = relative_file_path.replace("\\", "/")
        relative_file_path = path_prefix + relative_file_path
        
        if relative_file_path.startswith("sys/"):
          sys_rel_file_path = os.path.relpath(relative_file_path, "sys")
          if sys_rel_file_path not in ["apploader.img", "bi2.bin", "boot.bin", "fst.bin", "main.dol"]:
            raise Exception("Tried to add an invalid system file: %s" % relative_file_path)
        
        if relative_file_path.lower() in self.files_by_path_lowercase:
          replace_paths.append(relative_file_path)
        else:
          add_paths.append(relative_file_path)
    
    return (replace_paths, add_paths)
  
  def import_files_from_disk_by_paths(self, input_directory, replace_paths, add_paths, base_dir=None):
    path_prefix = ""
    if base_dir is not None:
      path_prefix = f"{base_dir.file_path}/"
    
    files_done = 0
    
    for gcm_file_path in replace_paths:
      assert gcm_file_path.startswith(path_prefix)
      relative_file_path = gcm_file_path.removeprefix(path_prefix)
      
      file_path = os.path.join(input_directory, relative_file_path)
      if os.path.isfile(file_path):
        with open(file_path, "rb") as f:
          self.changed_files[gcm_file_path] = BytesIO(f.read())
      else:
        raise Exception("File appears to have been deleted or moved: %s" % gcm_file_path)
      
      files_done += 1
      yield(gcm_file_path, files_done)
    
    for gcm_file_path in add_paths:
      assert gcm_file_path.startswith(path_prefix)
      relative_file_path = gcm_file_path.removeprefix(path_prefix)
      
      file_path = os.path.join(input_directory, relative_file_path)
      if os.path.isfile(file_path):
        with open(file_path, "rb") as f:
          self.add_new_file(gcm_file_path, BytesIO(f.read()))
      else:
        raise Exception("File appears to have been deleted or moved: %s" % gcm_file_path)
      
      files_done += 1
      yield(gcm_file_path, files_done)
  
  def get_num_files(self, base_dir=None):
    if base_dir is None:
      return len(self.files_by_path)
    
    base_dir_path = base_dir.file_path
    
    num_files = 0
    for file_path, file_entry in self.files_by_path.items():
      if file_path.startswith(f"{base_dir_path}/"):
        num_files += 1
    
    return num_files
  
  def get_all_file_paths_natsort(self):
    all_file_paths = list(self.files_by_path.keys())
    
    # Sort the file names for determinism. And use natural sorting so the room numbers are in order.
    try_int_convert = lambda string: int(string) if string.isdigit() else string
    all_file_paths.sort(key=lambda filename: [try_int_convert(c) for c in re.split("([0-9]+)", filename)])
    
    return all_file_paths
  
  def each_file_data(self, recurse_rarcs=True, only_file_exts: list[str] | None = None):
    all_file_paths = self.get_all_file_paths_natsort()
    
    for file_path in all_file_paths:
      _, file_ext = os.path.splitext(os.path.basename(file_path))
      
      if recurse_rarcs and self.check_file_is_rarc(file_path):
        rarc = RARC(self.get_changed_file_data(file_path))
        for rarc_file_path, file_data in rarc.each_file_data(only_file_exts=only_file_exts):
          yield (file_path + "/" + rarc_file_path, file_data)
      else:
        if only_file_exts is not None and file_ext not in only_file_exts:
          continue
        yield (file_path, self.get_changed_file_data(file_path))
  
  def check_file_is_rarc(self, file_path: str) -> bool:
    try:
      _, file_ext = os.path.splitext(os.path.basename(file_path))
      if file_ext in [".arc", ".szs", ".szp"]:
        file_data = self.get_changed_file_data(file_path)
        if Yaz0.check_is_compressed(file_data):
          magic = fs.read_str(file_data, 0x11, 4)
          if magic == "RARC":
            return True
        elif Yay0.check_is_compressed(file_data):
          chunk_offset = fs.read_u32(file_data, 0xC)
          magic = fs.read_str(file_data, chunk_offset, 4)
          if magic == "RARC":
            return True
        elif RARC.check_file_is_rarc(file_data):
          return True
    except Exception as e:
      pass
    return False
  
  def export_disc_to_folder_with_changed_files(self, output_folder_path, *, base_dir=None, only_changed_files=False):
    base_dir_path = None
    if base_dir is not None:
      base_dir_path = base_dir.file_path
    
    files_done = 0
    
    for file_path, file_entry in self.files_by_path.items():
      if base_dir is None:
        relative_file_path = file_path
      else:
        if file_path.startswith(f"{base_dir_path}/"):
          relative_file_path = os.path.relpath(file_path, base_dir_path)
        else:
          # This file isn't in the specified directory.
          continue
      
      out_file_path = os.path.join(output_folder_path, relative_file_path)
      dir_name = os.path.dirname(out_file_path)
      
      if file_path in self.changed_files:
        if not os.path.isdir(dir_name):
          os.makedirs(dir_name)
        
        file_data = self.changed_files[file_path]
        with open(out_file_path, "wb") as f:
          file_data.seek(0)
          f.write(file_data.read())
      else:
        if only_changed_files:
          continue
        if not os.path.isdir(dir_name):
          os.makedirs(dir_name)
        
        # Need to avoid reading enormous files all at once
        size_remaining = file_entry.file_size
        offset_in_file = 0
        with open(out_file_path, "wb") as f:
          while size_remaining > 0:
            size_to_read = min(size_remaining, MAX_DATA_SIZE_TO_READ_AT_ONCE)
            
            with open(self.iso_path, "rb") as iso_file:
              data = fs.read_bytes(iso_file, file_entry.file_data_offset + offset_in_file, size_to_read)
            f.write(data)
            
            size_remaining -= size_to_read
            offset_in_file += size_to_read
      
      files_done += 1
      yield(file_path, files_done)
  
  def export_disc_to_iso_with_changed_files(self, output_file_path):
    if os.path.realpath(self.iso_path) == os.path.realpath(output_file_path):
      raise Exception("Input ISO path and output ISO path are the same. Aborting.")
    
    self.output_iso = open(output_file_path, "wb")
    try:
      self.export_system_data_to_iso()
      yield("sys/main.dol", 5) # 5 system files
      
      for next_progress_text, files_done in self.export_filesystem_to_iso():
        yield(next_progress_text, 5+files_done)
      
      self.align_output_iso_to_nearest(2048)
      self.output_iso.close()
      self.output_iso = None
    except Exception:
      print("Error writing GCM, removing failed ISO.")
      self.output_iso.close()
      self.output_iso = None
      os.remove(output_file_path)
      raise
  
  def get_changed_file_data(self, file_path):
    if file_path in self.changed_files:
      return self.changed_files[file_path]
    else:
      return self.read_file_data(file_path)
  
  def get_changed_file_size(self, file_path):
    if file_path in self.changed_files:
      return fs.data_len(self.changed_files[file_path])
    else:
      file_path = file_path.lower()
      if file_path not in self.files_by_path_lowercase:
        raise Exception("Could not find file: " + file_path)
      file_entry = self.files_by_path_lowercase[file_path]
      return file_entry.file_size
  
  def add_new_directory(self, dir_path):
    assert dir_path.lower() not in self.dirs_by_path_lowercase
    
    parent_dir_name = os.path.dirname(dir_path)
    new_dir_name = os.path.basename(dir_path)
    
    if parent_dir_name == "sys":
      raise Exception("Cannot add a new directory to the system directory: %s" % dir_path)
    if not parent_dir_name:
      raise Exception("Cannot add a new directory to the root directory: %s" % dir_path)
    
    new_dir = GCMFileEntry()
    new_dir.is_dir = True
    new_dir.name = new_dir_name
    new_dir.file_path = dir_path
    new_dir.parent_fst_index = None # Recalculated if needed
    new_dir.next_fst_index = None # Recalculated if needed
    new_dir.children = []
    
    parent_dir = self.get_or_create_dir_file_entry(parent_dir_name)
    parent_dir.children.append(new_dir)
    new_dir.parent = parent_dir
    
    self.dirs_by_path[dir_path] = new_dir
    self.dirs_by_path_lowercase[dir_path.lower()] = new_dir
    
    return new_dir
  
  def add_new_file(self, file_path, file_data=None):
    assert file_path.lower() not in self.files_by_path_lowercase
    
    dirname = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    
    new_file = GCMFileEntry()
    new_file.name = basename
    new_file.file_path = file_path
    # file_data_offset is used for ordering the files in the new ISO, so we give it a huge value so new files are placed after vanilla files.
    new_file.file_data_offset = (1<<32)
    new_file.file_size = None # No original file size.
    
    parent_dir = self.get_or_create_dir_file_entry(dirname)
    parent_dir.children.append(new_file)
    new_file.parent = parent_dir
    
    if file_data is None:
      self.changed_files[file_path] = None
    else:
      self.changed_files[file_path] = file_data
    
    self.files_by_path[file_path] = new_file
    self.files_by_path_lowercase[file_path.lower()] = new_file
    
    return new_file
  
  def delete_directory(self, dir_entry):
    # Delete all children first.
    # Note that looping over a copy of the children list is necessary because the list gets modified as each child is removed.
    for child_entry in dir_entry.children.copy():
      if child_entry.is_dir:
        self.delete_directory(child_entry)
      else:
        self.delete_file(child_entry)
        
    parent_dir = dir_entry.parent
    parent_dir.children.remove(dir_entry)
    
    del self.dirs_by_path[dir_entry.file_path]
    del self.dirs_by_path_lowercase[dir_entry.file_path.lower()]
  
  def delete_file(self, file_entry):
    parent_dir = file_entry.parent
    parent_dir.children.remove(file_entry)
    
    del self.files_by_path[file_entry.file_path]
    del self.files_by_path_lowercase[file_entry.file_path.lower()]
    if file_entry.file_path in self.changed_files:
      del self.changed_files[file_entry.file_path]
  
  def rename_file_or_directory(self, file_entry: 'GCMFileEntry', new_name):
    if len(new_name) == 0:
      raise Exception("File name cannot be empty.")
    other_file_entry = next((fe for fe in file_entry.parent.children if fe.name == new_name), None)
    if other_file_entry == file_entry:
      # File name not changed
      return
    if other_file_entry is not None:
      raise Exception("The file name you entered is already used by another file or folder in this directory.")
    
    assert file_entry.name != new_name
    old_path = file_entry.file_path
    new_path = file_entry.file_path.rsplit("/", 1)[0] + "/" + new_name
    assert old_path != new_path
    
    file_entry.name = new_name
    file_entry.file_path = new_path
    
    if file_entry.is_dir:
      self.dirs_by_path[new_path] = file_entry
      self.dirs_by_path_lowercase[new_path.lower()] = file_entry
      del self.dirs_by_path[old_path]
      del self.dirs_by_path_lowercase[old_path.lower()]
    else:
      self.files_by_path[new_path] = file_entry
      self.files_by_path_lowercase[new_path.lower()] = file_entry
      del self.files_by_path[old_path]
      del self.files_by_path_lowercase[old_path.lower()]
      if old_path in self.changed_files:
        self.changed_files[new_path] = self.changed_files[old_path]
        del self.changed_files[old_path]
  
  def pad_output_iso_by(self, amount):
    self.output_iso.write(b"\0"*amount)
  
  def align_output_iso_to_nearest(self, size):
    current_offset = self.output_iso.tell()
    next_offset = current_offset + (size - current_offset % size) % size
    padding_needed = next_offset - current_offset
    self.pad_output_iso_by(padding_needed)
  
  def export_system_data_to_iso(self):
    boot_bin_data = self.get_changed_file_data("sys/boot.bin")
    assert fs.data_len(boot_bin_data) == 0x440
    self.output_iso.seek(0)
    boot_bin_data.seek(0)
    self.output_iso.write(boot_bin_data.read())
    
    bi2_data = self.get_changed_file_data("sys/bi2.bin")
    assert fs.data_len(bi2_data) == 0x2000
    self.output_iso.seek(0x440)
    bi2_data.seek(0)
    self.output_iso.write(bi2_data.read())
    
    apploader_data = self.get_changed_file_data("sys/apploader.img")
    apploader_header_size = 0x20
    apploader_size = fs.read_u32(apploader_data, 0x14)
    apploader_trailer_size = fs.read_u32(apploader_data, 0x18)
    apploader_full_size = apploader_header_size + apploader_size + apploader_trailer_size
    assert fs.data_len(apploader_data) == apploader_full_size
    self.output_iso.seek(0x2440)
    apploader_data.seek(0)
    self.output_iso.write(apploader_data.read())
    
    self.pad_output_iso_by(0x20)
    self.align_output_iso_to_nearest(0x100)
    
    dol_offset = self.output_iso.tell()
    dol_data = self.get_changed_file_data("sys/main.dol")
    dol_size = fs.data_len(dol_data)
    dol_data.seek(0)
    self.output_iso.write(dol_data.read())
    fs.write_u32(self.output_iso, 0x420, dol_offset)
    self.output_iso.seek(dol_offset + dol_size)
    
    self.pad_output_iso_by(0x20)
    self.align_output_iso_to_nearest(0x100)
    
    
    # Write the FST and FNT to the ISO.
    # File offsets and file sizes are left at 0, they will be filled in as the actual file data is written to the ISO.
    self.recalculate_file_entry_indexes()
    self.fst_offset = self.output_iso.tell()
    fs.write_u32(self.output_iso, 0x424, self.fst_offset)
    self.fnt_offset = self.fst_offset + len(self.file_entries)*0xC
    
    file_entry_offset = self.fst_offset
    next_name_offset = self.fnt_offset
    for file_index, file_entry in enumerate(self.file_entries):
      file_entry.name_offset = next_name_offset - self.fnt_offset
      
      is_dir_and_name_offset = 0
      if file_entry.is_dir:
        is_dir_and_name_offset |= 0x01000000
      is_dir_and_name_offset |= (file_entry.name_offset & 0x00FFFFFF)
      fs.write_u32(self.output_iso, file_entry_offset, is_dir_and_name_offset)
      
      if file_entry.is_dir:
        fs.write_u32(self.output_iso, file_entry_offset+4, file_entry.parent_fst_index)
        fs.write_u32(self.output_iso, file_entry_offset+8, file_entry.next_fst_index)
      
      file_entry_offset += 0xC
      
      if file_index != 0: # Root doesn't have a name
        fs.write_str_with_null_byte(self.output_iso, next_name_offset, file_entry.name)
        next_name_offset += len(file_entry.name)+1
    
    self.fst_size = self.output_iso.tell() - self.fst_offset
    fs.write_u32(self.output_iso, 0x428, self.fst_size)
    fs.write_u32(self.output_iso, 0x42C, self.fst_size) # Seems to be a duplicate size field that must also be updated
    self.output_iso.seek(self.fst_offset + self.fst_size)
  
  def recalculate_file_entry_indexes(self):
    root = self.file_entries[0]
    assert root.file_index == 0
    self.file_entries = []
    self.recalculate_file_entry_indexes_recursive(root)
  
  def recalculate_file_entry_indexes_recursive(self, curr_file_entry):
    curr_file_entry.file_index = len(self.file_entries)
    self.file_entries.append(curr_file_entry)
    if curr_file_entry.is_dir:
      if curr_file_entry.file_index != 0: # Root has no parent
        curr_file_entry.parent_fst_index = curr_file_entry.parent.file_index
      
      for child_file_entry in curr_file_entry.children:
        self.recalculate_file_entry_indexes_recursive(child_file_entry)
      
      curr_file_entry.next_fst_index = len(self.file_entries)
  
  def export_filesystem_to_iso(self):
    # Updates file offsets and sizes in the FST, and writes the files to the ISO.
    
    file_data_start_offset = self.fst_offset + self.fst_size
    self.output_iso.seek(file_data_start_offset)
    self.align_output_iso_to_nearest(4)
    
    # Instead of writing the file data in the order of file entries, write them in the order they were written in the vanilla ISO.
    # This increases the speed the game loads file for some unknown reason.
    file_entries_by_data_order = [
      file_entry for file_entry in self.file_entries
      if not file_entry.is_dir
    ]
    file_entries_by_data_order.sort(key=lambda fe: fe.file_data_offset)
    
    files_done = 0
    
    for file_entry in file_entries_by_data_order:
      current_file_start_offset = self.output_iso.tell()
      
      if file_entry.file_path in self.changed_files:
        file_data = self.changed_files[file_entry.file_path]
        file_data.seek(0)
        self.output_iso.write(file_data.read())
      else:
        # Unchanged file.
        # Most of the game's data falls into this category, so we read the data directly instead of calling read_file_data which would create a BytesIO object, which would add unnecessary performance overhead.
        # Also, we need to read very large files in chunks to avoid running out of memory.
        size_remaining = file_entry.file_size
        offset_in_file = 0
        while size_remaining > 0:
          size_to_read = min(size_remaining, MAX_DATA_SIZE_TO_READ_AT_ONCE)
          
          with open(self.iso_path, "rb") as iso_file:
            data = fs.read_bytes(iso_file, file_entry.file_data_offset + offset_in_file, size_to_read)
          self.output_iso.write(data)
          
          size_remaining -= size_to_read
          offset_in_file += size_to_read
      
      file_entry_offset = self.fst_offset + file_entry.file_index*0xC
      fs.write_u32(self.output_iso, file_entry_offset+4, current_file_start_offset)
      if file_entry.file_path in self.changed_files:
        file_size = fs.data_len(self.changed_files[file_entry.file_path])
      else:
        file_size = file_entry.file_size
      fs.write_u32(self.output_iso, file_entry_offset+8, file_size)
      
      # Note: The file_data_offset and file_size fields of the FileEntry must not be updated, they refer only to the offset and size of the file data in the input ISO, not this output ISO.
      
      self.output_iso.seek(current_file_start_offset + file_size)
      
      self.align_output_iso_to_nearest(4)
      
      files_done += 1
      yield(file_entry.file_path, files_done)

class GCMBaseFile:
  def __init__(self):
    self.file_index = None
    
    self.file_data_offset = None
    self.file_size = None
    
    self.name = None
    self.file_path = None
    
    self.is_dir = False
    self.is_system_file = False
  
  def read(self, file_index, iso_file, file_entry_offset, fnt_offset):
    pass

class GCMFileEntry(GCMBaseFile):
  def read(self, file_index, iso_file, file_entry_offset, fnt_offset):
    self.file_index = file_index
    
    is_dir_and_name_offset = fs.read_u32(iso_file, file_entry_offset)
    file_data_offset_or_parent_fst_index = fs.read_u32(iso_file, file_entry_offset+4)
    file_size_or_next_fst_index = fs.read_u32(iso_file, file_entry_offset+8)
    
    self.is_dir = ((is_dir_and_name_offset & 0xFF000000) != 0)
    self.name_offset = (is_dir_and_name_offset & 0x00FFFFFF)
    self.name = ""
    self.file_path = None
    if self.is_dir:
      self.parent_fst_index = file_data_offset_or_parent_fst_index
      self.next_fst_index = file_size_or_next_fst_index
      self.children = []
    else:
      self.file_data_offset = file_data_offset_or_parent_fst_index
      self.file_size = file_size_or_next_fst_index
    self.parent = None
    
    if file_index == 0:
      self.name = "" # Root
    else:
      self.name = fs.read_str_until_null_character(iso_file, fnt_offset + self.name_offset)

class GCMSystemFile(GCMBaseFile):
  def __init__(self, file_data_offset, file_size, name):
    super().__init__()
    
    self.file_data_offset = file_data_offset
    self.file_size = file_size
    
    self.name = name
    self.file_path = "sys/" + name
    
    self.is_system_file = True
