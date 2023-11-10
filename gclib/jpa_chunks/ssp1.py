
from gclib import fs_helpers as fs
from gclib.jchunk import JPAChunk
from gclib.jpa_enums import JPACVersion

class SSP1(JPAChunk):
  def read_chunk_specific_data(self):
    if self.version == JPACVersion.JPAC1_00:
      self.read_chunk_specific_data_jpc100()
    elif self.version == JPACVersion.JPAC2_10:
      self.read_chunk_specific_data_jpc210()
  
  def save_chunk_specific_data(self):
    if self.version == JPACVersion.JPAC1_00:
      self.save_chunk_specific_data_jpc100()
    elif self.version == JPACVersion.JPAC2_10:
      self.save_chunk_specific_data_jpc210()
    
  def read_chunk_specific_data_jpc100(self):
    r = fs.read_u8(self.data, 0xC + 0x3C)
    g = fs.read_u8(self.data, 0xC + 0x3D)
    b = fs.read_u8(self.data, 0xC + 0x3E)
    a = fs.read_u8(self.data, 0xC + 0x3F)
    self.color_prm = (r, g, b, a)
    r = fs.read_u8(self.data, 0xC + 0x40)
    g = fs.read_u8(self.data, 0xC + 0x41)
    b = fs.read_u8(self.data, 0xC + 0x42)
    a = fs.read_u8(self.data, 0xC + 0x43)
    self.color_env = (r, g, b, a)
  
  def read_chunk_specific_data_jpc210(self):
    r = fs.read_u8(self.data, 0x34)
    g = fs.read_u8(self.data, 0x35)
    b = fs.read_u8(self.data, 0x36)
    a = fs.read_u8(self.data, 0x37)
    self.color_prm = (r, g, b, a)
    r = fs.read_u8(self.data, 0x38)
    g = fs.read_u8(self.data, 0x39)
    b = fs.read_u8(self.data, 0x3A)
    a = fs.read_u8(self.data, 0x3B)
    self.color_env = (r, g, b, a)
    
  def save_chunk_specific_data_jpc100(self):
    r, g, b, a = self.color_prm
    fs.write_u8(self.data, 0xC + 0x3C, r)
    fs.write_u8(self.data, 0xC + 0x3D, g)
    fs.write_u8(self.data, 0xC + 0x3E, b)
    fs.write_u8(self.data, 0xC + 0x3F, a)
    r, g, b, a = self.color_env
    fs.write_u8(self.data, 0xC + 0x40, r)
    fs.write_u8(self.data, 0xC + 0x41, g)
    fs.write_u8(self.data, 0xC + 0x42, b)
    fs.write_u8(self.data, 0xC + 0x43, a)
  
  def save_chunk_specific_data_jpc210(self):
    r, g, b, a = self.color_prm
    fs.write_u8(self.data, 0x34, r)
    fs.write_u8(self.data, 0x35, g)
    fs.write_u8(self.data, 0x36, b)
    fs.write_u8(self.data, 0x37, a)
    r, g, b, a = self.color_env
    fs.write_u8(self.data, 0x38, r)
    fs.write_u8(self.data, 0x39, g)
    fs.write_u8(self.data, 0x3A, b)
    fs.write_u8(self.data, 0x3B, a)
