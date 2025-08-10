
from gclib import fs_helpers as fs
from gclib.jchunk import JPAChunk
from gclib.jpa_enums import JPACVersion
from gclib.fs_helpers import u32, u24, u16, u8, s32, s16, s8, f32, u16Rot, FixedStr, MagicStr
from gclib.bunfoe import BUNFOE, bunfoe, field
from gclib.bunfoe_types import Vec2float, Vec3float, Matrix2x3, Matrix4x4, RGBAu8, RGBAs16, Vec3u16Rot

@bunfoe
class ColorAnimationKeyframe(BUNFOE):
  DATA_SIZE = 6
  
  time: u16
  color: RGBAu8

class BSP1(JPAChunk):
  prm_color_anim_offset: s16
  env_color_anim_offset: s16
  prm_color_anim_key_count: u8
  env_color_anim_key_count: u8
  prm_color_anim_keys: list[ColorAnimationKeyframe]
  env_color_anim_keys: list[ColorAnimationKeyframe]
  
  def __new__(cls, *args, **kwargs):
    if cls != BSP1:
      return super().__new__(cls)
    data, version = args
    if version == JPACVersion.JPAC1_00:
      return BSP1_JPC100(data, version)
    elif version == JPACVersion.JPAC2_10:
      return BSP1_JPC210(data, version)
    return super().__new__(cls)

@bunfoe
class BSP1_JPC100(BSP1): # JPABaseShape
  DATA_SIZE = JPAChunk.HEADER_SIZE + 4 + 0x54
  
  unused_jpachunk_field: u32 = field(default=0, assert_default=True)

  flags: u32
  prm_color_anim_offset: s16
  env_color_anim_offset: s16
  base_size: Vec2float
  loop_offset: s16
  blend_mode_flags: u16
  alpha_compare_flags: u8
  alpha_compare_ref0: u8
  alpha_compare_ref1: u8
  z_mode_flags: u8
  texture_flags: u8
  texture_index_anim_key_count: u8
  texture_index: u8
  color_flags: u8
  prm_color_anim_key_count: u8
  env_color_anim_key_count: u8
  color_reg_anim_max_frame: s16
  prm_color: RGBAu8
  env_color: RGBAu8
  tiling: Vec2float
  texture_init_translation: Vec2float
  texture_init_scale: Vec2float
  texture_inc_translation: Vec2float
  texture_inc_scale: Vec2float
  texture_inc_rotate: f32
  
  texture_index_anim_keys: list[u8] = field(manual_read=True, default_factory=list)
  prm_color_anim_keys: list[ColorAnimationKeyframe] = field(manual_read=True, default_factory=list)
  env_color_anim_keys: list[ColorAnimationKeyframe] = field(manual_read=True, default_factory=list)
  
  def read_chunk_specific_data(self):
    offset = 0x60
    
    self.texture_index_anim_keys = []
    for i in range(self.texture_index_anim_key_count):
      tex_idx = fs.read_u8(self.data, offset)
      self.texture_index_anim_keys.append(tex_idx)
      offset += 1
    
    offset = self.prm_color_anim_offset
    self.prm_color_anim_keys = []
    for i in range(self.prm_color_anim_key_count):
      keyframe = ColorAnimationKeyframe(self.data)
      self.prm_color_anim_keys.append(keyframe)
      offset = keyframe.read(offset)
    
    offset = self.env_color_anim_offset
    self.env_color_anim_keys = []
    for i in range(self.env_color_anim_key_count):
      keyframe = ColorAnimationKeyframe(self.data)
      self.env_color_anim_keys.append(keyframe)
      offset = keyframe.read(offset)
  
  def save_chunk_specific_data(self):
    offset = 0x60
    self.data.truncate(offset)
    
    if len(self.texture_index_anim_keys) > 0:
      self.texture_index_anim_key_count = len(self.texture_index_anim_keys)
      for tex_idx in self.texture_index_anim_keys:
        fs.write_u8(self.data, offset, tex_idx)
        offset += 1
    else:
      self.texture_index_anim_keys = []
      self.texture_index_anim_key_count = 0
    offset = fs.align_data_and_pad_offset(self.data, offset, 4, padding_bytes=b'\0')
    
    if len(self.prm_color_anim_keys) > 0:
      self.prm_color_anim_key_count = len(self.prm_color_anim_keys)
      self.prm_color_anim_offset = offset
      for keyframe in self.prm_color_anim_keys:
        offset = keyframe.save(offset)
      offset = fs.align_data_and_pad_offset(self.data, offset, 4, padding_bytes=b'\0')
    else:
      self.prm_color_anim_key_count = 0
      self.prm_color_anim_offset = 0
    
    if len(self.env_color_anim_keys) > 0:
      self.env_color_anim_key_count = len(self.env_color_anim_keys)
      self.env_color_anim_offset = offset
      for keyframe in self.env_color_anim_keys:
        offset = keyframe.save(offset)
      offset = fs.align_data_and_pad_offset(self.data, offset, 4, padding_bytes=b'\0')
    else:
      self.env_color_anim_key_count = 0
      self.env_color_anim_offset = 0
    
    self.save_value(s16, JPAChunk.HEADER_SIZE + 4 + 0x04, self.prm_color_anim_offset)
    self.save_value(s16, JPAChunk.HEADER_SIZE + 4 + 0x06, self.env_color_anim_offset)
    self.save_value(u8, JPAChunk.HEADER_SIZE + 4 + 0x19, self.texture_index_anim_key_count)
    self.save_value(u8, JPAChunk.HEADER_SIZE + 4 + 0x1C, self.prm_color_anim_key_count)
    self.save_value(u8, JPAChunk.HEADER_SIZE + 4 + 0x1D, self.env_color_anim_key_count)

@bunfoe
class BSP1_JPC210(BSP1): # JPABaseShape
  DATA_SIZE = JPAChunk.HEADER_SIZE + 0x2C
  
  flags: u32
  prm_color_anim_offset: s16
  env_color_anim_offset: s16
  base_size: Vec2float
  blend_mode_flags: u16
  alpha_compare_flags: u8
  alpha_compare_ref0: u8
  alpha_compare_ref1: u8
  z_mode_flags: u8
  texture_flags: u8
  texture_index_anim_key_count: u8
  texture_index: u8
  color_flags: u8
  prm_color_anim_key_count: u8
  env_color_anim_key_count: u8
  color_reg_anim_max_frame: s16
  prm_color: RGBAu8
  env_color: RGBAu8
  anim_random: u8
  color_anim_random_mask: u8
  texture_anim_random_mask: u8
  _padding: u24
  
  texture_init_translation: Vec2float = field(manual_read=True, default_factory=Vec2float)
  texture_init_scale      : Vec2float = field(manual_read=True, default_factory=Vec2float)
  texture_init_rotate     : f32       = field(manual_read=True, default=0.0)
  texture_inc_translation : Vec2float = field(manual_read=True, default_factory=Vec2float)
  texture_inc_scale       : Vec2float = field(manual_read=True, default_factory=Vec2float)
  texture_inc_rotate      : f32       = field(manual_read=True, default=0.0)
  
  texture_index_anim_keys: list[u8] = field(manual_read=True, default_factory=list)
  prm_color_anim_keys: list[ColorAnimationKeyframe] = field(manual_read=True, default_factory=list)
  env_color_anim_keys: list[ColorAnimationKeyframe] = field(manual_read=True, default_factory=list)
  
  def read_chunk_specific_data(self):
    offset = 0x34
    
    if ((self.flags >> 24) & 1) != 0: # Enable texture scroll anim
      self.texture_init_translation = self.read_value(Vec2float, offset)
      offset += self.get_byte_size(Vec2float)
      self.texture_init_scale = self.read_value(Vec2float, offset)
      offset += self.get_byte_size(Vec2float)
      self.texture_init_rotate = self.read_value(f32, offset)
      offset += self.get_byte_size(f32)
      self.texture_inc_translation = self.read_value(Vec2float, offset)
      offset += self.get_byte_size(Vec2float)
      self.texture_inc_scale = self.read_value(Vec2float, offset)
      offset += self.get_byte_size(Vec2float)
      self.texture_inc_rotate = self.read_value(f32, offset)
      offset += self.get_byte_size(f32)
    
    self.texture_index_anim_keys = []
    for i in range(self.texture_index_anim_key_count):
      tex_idx = fs.read_u8(self.data, offset)
      self.texture_index_anim_keys.append(tex_idx)
      offset += 1
    
    offset = self.prm_color_anim_offset
    self.prm_color_anim_keys = []
    for i in range(self.prm_color_anim_key_count):
      keyframe = ColorAnimationKeyframe(self.data)
      self.prm_color_anim_keys.append(keyframe)
      offset = keyframe.read(offset)
    
    offset = self.env_color_anim_offset
    self.env_color_anim_keys = []
    for i in range(self.env_color_anim_key_count):
      keyframe = ColorAnimationKeyframe(self.data)
      self.env_color_anim_keys.append(keyframe)
      offset = keyframe.read(offset)
  
  def save_chunk_specific_data(self):
    offset = 0x34
    self.data.truncate(offset)
    
    if ((self.flags >> 24) & 1) != 0: # Enable texture scroll anim
      self.save_value(Vec2float, offset, self.texture_init_translation)
      offset += self.get_byte_size(Vec2float)
      self.save_value(Vec2float, offset, self.texture_init_scale)
      offset += self.get_byte_size(Vec2float)
      self.save_value(f32, offset, self.texture_init_rotate)
      offset += self.get_byte_size(f32)
      self.save_value(Vec2float, offset, self.texture_inc_translation)
      offset += self.get_byte_size(Vec2float)
      self.save_value(Vec2float, offset, self.texture_inc_scale)
      offset += self.get_byte_size(Vec2float)
      self.save_value(f32, offset, self.texture_inc_rotate)
      offset += self.get_byte_size(f32)
    
    if len(self.texture_index_anim_keys) > 0:
      self.texture_index_anim_key_count = len(self.texture_index_anim_keys)
      for tex_idx in self.texture_index_anim_keys:
        fs.write_u8(self.data, offset, tex_idx)
        offset += 1
    else:
      self.texture_index_anim_keys = []
      self.texture_index_anim_key_count = 0
    offset = fs.align_data_and_pad_offset(self.data, offset, 4, padding_bytes=b'\0')
    
    if len(self.prm_color_anim_keys) > 0:
      self.prm_color_anim_key_count = len(self.prm_color_anim_keys)
      self.prm_color_anim_offset = offset
      for keyframe in self.prm_color_anim_keys:
        offset = keyframe.save(offset)
      offset = fs.align_data_and_pad_offset(self.data, offset, 4, padding_bytes=b'\0')
    else:
      self.prm_color_anim_key_count = 0
      self.prm_color_anim_offset = 0
    
    if len(self.env_color_anim_keys) > 0:
      self.env_color_anim_key_count = len(self.env_color_anim_keys)
      self.env_color_anim_offset = offset
      for keyframe in self.env_color_anim_keys:
        offset = keyframe.save(offset)
      offset = fs.align_data_and_pad_offset(self.data, offset, 4, padding_bytes=b'\0')
    else:
      self.env_color_anim_key_count = 0
      self.env_color_anim_offset = 0
    
    self.save_value(s16, 0x0C, self.prm_color_anim_offset)
    self.save_value(s16, 0x0E, self.env_color_anim_offset)
    self.save_value(u8, 0x1F, self.texture_index_anim_key_count)
    self.save_value(u8, 0x22, self.prm_color_anim_key_count)
    self.save_value(u8, 0x23, self.env_color_anim_key_count)
