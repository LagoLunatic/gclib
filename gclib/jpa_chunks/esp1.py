
from gclib import fs_helpers as fs
from gclib.jchunk import JPAChunk
from gclib.jpa_enums import JPACVersion
from gclib.fs_helpers import u32, u24, u16, u8, s32, s16, s8, f32, u16Rot, FixedStr, MagicStr
from gclib.bunfoe import BUNFOE, bunfoe, field
from gclib.bunfoe_types import Vec2float, Vec3float, Matrix2x3, Matrix4x4, RGBAu8, RGBAs16

class ESP1(JPAChunk):
  def __new__(cls, *args, **kwargs):
    if cls != ESP1:
      return super().__new__(cls)
    data, version = args
    if version == JPACVersion.JPAC1_00:
      return ESP1_JPC100(data, version)
    elif version == JPACVersion.JPAC2_10:
      return ESP1_JPC210(data, version)
    return super().__new__(cls)

@bunfoe
class ESP1_JPC100(ESP1): # JPAExtraShape
  DATA_SIZE = JPAChunk.HEADER_SIZE + 0x60
  
  flags: u32
  unknown_1: u32
  alpha_in_timing: f32
  alpha_out_timing: f32
  alpha_in_value: f32
  alpha_base_value: f32
  alpha_out_value: f32
  alpha_wave_param1: f32
  alpha_wave_param2: f32
  alpha_wave_param3: f32
  alpha_wave_random: f32
  scale_in_timing: f32
  scale_out_timing: f32
  scale_in_value_x: f32
  scale_out_value_x: f32
  scale_in_value_y: f32
  scale_out_value_y: f32
  random_scale: f32
  anm_cycle_x: s16
  anm_cycle_y: s16
  rotate_angle: f32
  rotate_speed: f32
  rotate_angle_random: f32
  rotate_speed_random: f32
  rotate_direction: f32

@bunfoe
class ESP1_JPC210(ESP1): # JPAExtraShape
  DATA_SIZE = JPAChunk.HEADER_SIZE + 0x58

  flags: u32
  scale_in_timing: f32
  scale_out_timing: f32
  scale_in_value_x: f32
  scale_out_value_x: f32
  scale_in_value_y: f32
  scale_out_value_y: f32
  scale_out_random: f32
  scale_anm_cycle_x: s16
  scale_anm_cycle_y: s16
  alpha_in_timing: f32
  alpha_out_timing: f32
  alpha_in_value: f32
  alpha_base_value: f32
  alpha_out_value: f32
  alpha_wave_frequency: f32
  alpha_wave_freq_random: f32
  alpha_wave_amplitude: f32
  rotate_angle: f32
  rotate_angle_random: f32
  rotate_speed: f32
  rotate_speed_random: f32
  rotate_direction: f32
