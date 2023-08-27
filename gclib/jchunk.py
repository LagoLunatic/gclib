
from gclib import fs_helpers as fs
from gclib.fs_helpers import u32, u16, u8, s32, s16, s8, u16Rot, FixedStr, MagicStr
from gclib.bunfoe import BUNFOE, Field, bunfoe, field, fields

# Set eq=False because we don't want to consider chunks equal just because they have the same type
# and size. (e.g. JPC textures are each their own TEX1 chunk.)
@bunfoe(eq=False)
class JChunk(BUNFOE):
  magic: MagicStr[4]
  size: u32
  
  def __init__(self, data):
    super().__init__(data)
    self.data = data
  
  def read(self, offset):
    super().read(offset)
    
    self.read_chunk_specific_data()
  
  def read_chunk_specific_data(self):
    pass
  
  def save(self):
    self.save_chunk_specific_data()
    
    # Pad the size of this chunk.
    fs.align_data_to_nearest(self.data, self.padding_alignment_size, padding_bytes=self.padding_bytes)
    
    self.size = fs.data_len(self.data)
    fs.write_magic_str(self.data, 0, self.magic, 4)
    fs.write_u32(self.data, 4, self.size)
  
  def save_chunk_specific_data(self):
    pass
  
  @property
  def padding_alignment_size(self) -> int:
    return 0x20
  
  @property
  def padding_bytes(self) -> bytes:
    return fs.PADDING_BYTES
  
  def read_string_table(self, string_table_offset):
    num_strings = fs.read_u16(self.data, string_table_offset+0x00)
    #padding = fs.read_u16(self.data, string_table_offset+0x02)
    #assert padding == 0xFFFF
    
    strings = []
    offset = string_table_offset + 4
    for i in range(num_strings):
      #string_hash = fs.read_u16(self.data, offset+0x00)
      string_data_offset = fs.read_u16(self.data, offset+0x02)
      
      string = fs.read_str_until_null_character(self.data, string_table_offset + string_data_offset)
      strings.append(string)
      
      offset += 4
    
    return strings
  
  def write_string_table(self, string_table_offset, strings) -> int:
    num_strings = len(strings)
    fs.write_u16(self.data, string_table_offset+0x00, num_strings)
    fs.write_u16(self.data, string_table_offset+0x02, 0xFFFF)
    
    offset = string_table_offset + 4
    next_string_data_offset = 4 + num_strings*4
    for string in strings:
      hash = 0
      for char in string:
        hash *= 3
        hash += ord(char)
        hash &= 0xFFFF
      
      fs.write_u16(self.data, offset+0x00, hash)
      fs.write_u16(self.data, offset+0x02, next_string_data_offset)
      
      fs.write_str_with_null_byte(self.data, string_table_offset+next_string_data_offset, string)
      
      offset += 4
      next_string_data_offset += len(string) + 1
    
    return string_table_offset+next_string_data_offset
