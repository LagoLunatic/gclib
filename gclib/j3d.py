
from gclib import fs_helpers as fs
from gclib.gclib_file import GCLibFile
from gclib.jchunk import JChunk
from gclib.j3d_chunks import CHUNK_TYPES
from gclib.j3d_chunks.inf1 import INF1
from gclib.j3d_chunks.vtx1 import VTX1
# from gclib.j3d_chunks.evp1 import EVP1
# from gclib.j3d_chunks.drw1 import DRW1
from gclib.j3d_chunks.jnt1 import JNT1
from gclib.j3d_chunks.shp1 import SHP1
from gclib.j3d_chunks.mat3 import MAT3
from gclib.j3d_chunks.mdl3 import MDL3
from gclib.j3d_chunks.tex1 import TEX1
from gclib.j3d_chunks.trk1 import TRK1
from gclib.j3d_chunks.ttk1 import TTK1

class J3D(GCLibFile):
  KNOWN_MAGICS = None
  KNOWN_FILE_TYPES = None
  
  def __init__(self, file_entry_or_data = None):
    super().__init__(file_entry_or_data)
    
    self.read()
  
  def read(self):
    data = self.data
    
    self.magic = fs.read_str(data, 0, 4)
    assert self.magic.startswith("J3D"), f"Unknown J3D magic: {self.magic!r}"
    if self.KNOWN_MAGICS is not None:
      assert self.magic in self.KNOWN_MAGICS, f"Unknown {type(self).__name__} magic: {self.magic!r}"
    self.file_type = fs.read_str(data, 4, 4)
    if self.KNOWN_FILE_TYPES is not None:
      assert self.file_type in self.KNOWN_FILE_TYPES, f"Unknown {type(self).__name__} file type: {self.file_type!r}"
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

class BMD(J3D):
  KNOWN_MAGICS = ["J3D2"]
  KNOWN_FILE_TYPES = ["bmd2", "bmd3"]
  
  inf1: INF1
  vtx1: VTX1
  # evp1: EVP1
  # drw1: DRW1
  jnt1: JNT1
  shp1: SHP1
  mat3: MAT3
  tex1: TEX1

class BDL(BMD):
  KNOWN_MAGICS = ["J3D2"]
  KNOWN_FILE_TYPES = ["bdl4"]
  
  mdl3: MDL3

class BMT(J3D):
  KNOWN_MAGICS = ["J3D2"]
  KNOWN_FILE_TYPES = ["bmt3"]

class BRK(J3D):
  KNOWN_MAGICS = ["J3D1"]
  KNOWN_FILE_TYPES = ["brk1"]
  
  trk1: TRK1

class BTK(J3D):
  KNOWN_MAGICS = ["J3D1"]
  KNOWN_FILE_TYPES = ["btk1"]
  
  ttk1: TTK1
