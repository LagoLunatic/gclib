
from gclib import fs_helpers as fs
from gclib.jchunk import JPAChunk
from gclib.jpa_enums import JPACVersion
from gclib.fs_helpers import u32, u24, u16, u8, s32, s16, s8, f32, u16Rot, FixedStr, MagicStr
from gclib.bunfoe import BUNFOE, bunfoe, field
from gclib.bunfoe_types import Vec2float, Vec3float, Matrix2x3, Matrix4x4, RGBAu8, RGBAs16, Vec3u16Rot

class BEM1(JPAChunk):
  def __new__(cls, *args, **kwargs):
    if cls != BEM1:
      return super().__new__(cls)
    data, version = args
    if version == JPACVersion.JPAC1_00:
      return BEM1_JPC100(data, version)
    elif version == JPACVersion.JPAC2_10:
      return BEM1_JPC210(data, version)
    return super().__new__(cls)

@bunfoe
class BEM1_JPC100(BEM1): # JPADynamicsBlock
  DATA_SIZE = JPAChunk.HEADER_SIZE + 0x80
  
  flag: u32
  volume_sweep: f32
  volume_min_rad: f32
  volume_size: u16
  div_number: u16
  rate: f32
  rate_random: f32
  rate_step: u8
  unknown_1: u8
  max_frame: s16
  start_frame: s16
  life_time: s16
  life_time_random: f32
  init_vel_omni: f32
  init_vel_axis: f32
  init_vel_random: f32
  init_vel_dir: f32
  init_vel_ratio: f32
  spread: f32
  air_resist: f32
  air_resist_random: f32
  moment: f32
  moment_random: f32
  accel: f32
  accel_random: f32
  emitter_scale: Vec3float
  emitter_translation: Vec3float
  emitter_direction: Vec3float
  emitter_rotation: Vec3u16Rot
  _padding: u16

@bunfoe
class BEM1_JPC210(BEM1): # JPADynamicsBlock
  DATA_SIZE = JPAChunk.HEADER_SIZE + 0x74

  flags: u32
  res_user_work: u32
  emitter_scale: Vec3float
  emitter_translation: Vec3float
  emitter_direction: Vec3float
  initial_vel_omni: f32
  initial_vel_axis: f32
  initial_vel_random: f32
  initial_vel_dir: f32
  spread: f32
  initial_vel_ratio: f32
  rate: f32
  rate_random: f32
  life_time_random: f32
  volume_sweep: f32
  volume_min_rad: f32
  air_resist: f32
  moment: f32
  emitter_rotation: Vec3u16Rot
  max_frame: s16
  start_frame: s16
  life_time: s16
  volume_size: u16
  div_number: u16
  rate_step: u8
  _padding: u24
