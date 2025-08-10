
from gclib import fs_helpers as fs
from gclib.jchunk import JPAChunk
from gclib.jpa_enums import JPACVersion
from gclib.fs_helpers import u32, u24, u16, u8, s32, s16, s8, f32, u16Rot, FixedStr, MagicStr
from gclib.bunfoe import BUNFOE, bunfoe, field
from gclib.bunfoe_types import Vec2float, Vec3float, Matrix2x3, Matrix4x4, RGBAu8, RGBAs16, Vec3u16Rot

class ColorAnimationKeyframe:
  def __init__(self, time, color):
    self.time = time
    self.color = color

class BSP1(JPAChunk):
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
  
  def read_color_table(self, color_data_offset, color_data_count):
    color_table = []
    for i in range(color_data_count):
      keyframe_time = fs.read_u16(self.data, color_data_offset+i*6 + 0)
      r = fs.read_u8(self.data, color_data_offset+i*6 + 2)
      g = fs.read_u8(self.data, color_data_offset+i*6 + 3)
      b = fs.read_u8(self.data, color_data_offset+i*6 + 4)
      a = fs.read_u8(self.data, color_data_offset+i*6 + 5)
      color_table.append(ColorAnimationKeyframe(keyframe_time, (r, g, b, a)))
    
    return color_table
  
  def save_color_table(self, color_table, color_data_offset):
    for i, keyframe in enumerate(color_table):
      r, g, b, a = keyframe.color
      fs.write_u16(self.data, color_data_offset+i*6 + 0, keyframe.time)
      fs.write_u8(self.data, color_data_offset+i*6 + 2, r)
      fs.write_u8(self.data, color_data_offset+i*6 + 3, g)
      fs.write_u8(self.data, color_data_offset+i*6 + 4, b)
      fs.write_u8(self.data, color_data_offset+i*6 + 5, a)

@bunfoe
class BSP1_JPC100(BSP1): # JPABaseShape
  DATA_SIZE = JPAChunk.HEADER_SIZE + 4 + 0x54
  
  unused_jpachunk_field: u32 = field(default=0, assert_default=True)

  flags: u32
  prm_color_anim_data_offset: s16
  env_color_anim_data_offset: s16
  base_size: Vec2float
  loop_offset: s16
  blend_mode_flags: u16
  alpha_compare_flags: u8
  alpha_compare_ref0: u8
  alpha_compare_ref1: u8
  z_mode_flags: u8
  texture_flags: u8
  texture_anim_key_count: u8
  texture_index: u8
  color_flags: u8
  prm_color_anim_key_count: u8
  env_color_anim_key_count: u8
  color_reg_anim_max_frame: s16
  prm_color: RGBAu8
  env_color: RGBAu8
  tiling: Vec2float
  texture_static_translation: Vec2float
  texture_static_scale: Vec2float
  texture_scroll_translation: Vec2float
  texture_scroll_scale: Vec2float
  texture_scroll_rotate: f32
  
  def read_chunk_specific_data(self):
    self.prm_color_anim_keys = []
    if self.color_flags & 0x02 != 0:
      self.prm_color_anim_keys = self.read_color_table(self.prm_color_anim_data_offset, self.prm_color_anim_key_count)
    
    self.env_color_anim_keys = []
    if self.color_flags & 0x08 != 0:
      self.env_color_anim_keys = self.read_color_table(self.env_color_anim_data_offset, self.env_color_anim_key_count)
  
  def save_chunk_specific_data(self):
    if self.color_flags & 0x02 != 0:
      # Changing size not yet implemented.
      assert len(self.prm_color_anim_keys) == self.prm_color_anim_key_count
      self.save_color_table(self.prm_color_anim_keys, self.prm_color_anim_data_offset)
    
    if self.color_flags & 0x08 != 0:
      # Changing size not yet implemented.
      assert len(self.env_color_anim_keys) == self.env_color_anim_key_count
      self.save_color_table(self.env_color_anim_keys, self.env_color_anim_data_offset)

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
  texture_anim_count: u8
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
  
  def read_chunk_specific_data(self):
    self.prm_color_anim_keys = []
    if self.color_flags & 0x02 != 0:
      self.prm_color_anim_keys = self.read_color_table(self.prm_color_anim_offset, self.prm_color_anim_key_count)
    
    self.env_color_anim_keys = []
    if self.color_flags & 0x08 != 0:
      self.env_color_anim_keys = self.read_color_table(self.env_color_anim_offset, self.env_color_anim_key_count)
  
  def save_chunk_specific_data(self):
    if self.color_flags & 0x02 != 0:
      # Changing size not yet implemented.
      assert len(self.prm_color_anim_keys) == self.prm_color_anim_key_count
      self.save_color_table(self.prm_color_anim_keys, self.prm_color_anim_offset)
    
    if self.color_flags & 0x08 != 0:
      # Changing size not yet implemented.
      assert len(self.env_color_anim_keys) == self.env_color_anim_key_count
      self.save_color_table(self.env_color_anim_keys, self.env_color_anim_offset)
