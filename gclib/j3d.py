
from gclib import fs_helpers as fs
from gclib.gclib_file import GCLibFile
from gclib.jchunk import JChunk
from gclib.j3d_chunks import CHUNK_TYPES

class J3D(GCLibFile):
  def __init__(self, file_entry_or_data = None):
    super().__init__(file_entry_or_data)
    
    self.read()
  
  def read(self):
    data = self.data
    
    self.magic = fs.read_str(data, 0, 4)
    assert self.magic.startswith("J3D"), f"Unknown J3D magic: {self.magic!r}"
    self.file_type = fs.read_str(data, 4, 4)
    self.length = fs.read_u32(data, 8)
    self.num_chunks = fs.read_u32(data, 0x0C)
    
    self.bck_sound_data_offset = fs.read_u32(data, 0x1C)
    if self.file_type == "bck1" and self.bck_sound_data_offset != 0xFFFFFFFF:
      num_bck_sound_data_entries = fs.read_u16(data, self.bck_sound_data_offset)
      bck_sound_data_length = 8 + num_bck_sound_data_entries*0x20
      self.bck_sound_data = fs.read_bytes(data, self.bck_sound_data_offset, bck_sound_data_length)
    else:
      self.bck_sound_data = None
    
    self.chunks: list[JChunk] = []
    self.chunk_by_type = {}
    offset = 0x20
    for chunk_index in range(self.num_chunks):
      if offset == fs.data_len(data):
        # Normally the number of chunks tells us when to stop reading.
        # But in rare cases like Bk.arc/bk_boko.bmt, the number of chunks can be greater than how many chunks are actually in the file, so we need to detect when we've reached the end of the file manually.
        break
      
      chunk_magic = fs.read_str(data, offset, 4)
      chunk_class = CHUNK_TYPES.get(chunk_magic, JChunk)
      
      size = fs.read_u32(data, offset+4)
      chunk_data = fs.read_sub_data(data, offset, size)
      chunk = chunk_class(chunk_data)
      chunk.read(0)
      
      self.chunks.append(chunk)
      self.chunk_by_type[chunk.magic] = chunk
      
      if chunk.magic in CHUNK_TYPES:
        setattr(self, chunk.magic.lower(), chunk)
      
      offset += chunk.size
  
  def save(self, only_chunks:set=None):
    data = self.data
    
    # Cut off the chunk data first since we're replacing this data entirely.
    data.truncate(0x20)
    data.seek(0x20)
    
    for chunk in self.chunks:
      if only_chunks is None or chunk.magic in only_chunks:
        chunk.save()
      
      data.write(fs.read_all_bytes(chunk.data))
    
    if self.bck_sound_data is not None:
      self.bck_sound_data_offset = fs.data_len(data)
      fs.write_bytes(data, self.bck_sound_data_offset, self.bck_sound_data)
      
      # Pad the size of the whole file to the next 0x20 bytes.
      fs.align_data_to_nearest(data, 0x20, padding_bytes=b'\0')
    
    self.length = fs.data_len(data)
    self.num_chunks = len(self.chunks)
    
    fs.write_magic_str(data, 0, self.magic, 4)
    fs.write_magic_str(data, 4, self.file_type, 4)
    fs.write_u32(data, 8, self.length)
    fs.write_u32(data, 0xC, self.num_chunks)
    fs.write_u32(data, 0x1C, self.bck_sound_data_offset)

class BDL(J3D):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D2"
    assert self.file_type == "bdl4"

class BMD(J3D):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D2"
    assert self.file_type == "bmd3" or self.file_type == "bmd2"

class BMT(J3D):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D2"
    assert self.file_type == "bmt3"

class BRK(J3D):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D1"
    assert self.file_type == "brk1"

class BTK(J3D):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D1"
    assert self.file_type == "btk1"
