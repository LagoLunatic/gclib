
from gclib import fs_helpers as fs
from gclib.jchunk import JPAChunk
from gclib.jpa_enums import DirType, JPACVersion, JPAShapeType, PlaneType, RotType
from gclib.fs_helpers import u32, u24, u16, u8, s32, s16, s8, u16Rot, FixedStr, MagicStr
from gclib.bunfoe import BUNFOE, bunfoe, field
from gclib.bunfoe_types import Vec2float, Vec3float, Matrix2x3, Matrix4x4, RGBAu8, RGBAs16

class SSP1(JPAChunk):
  def __new__(cls, *args, **kwargs):
    if cls != SSP1:
      return super().__new__(cls)
    data, version = args
    if version == JPACVersion.JPAC1_00:
      return SSP1_JPC100(data, version)
    elif version == JPACVersion.JPAC2_10:
      return SSP1_JPC210(data, version)
    return super().__new__(cls)

@bunfoe
class SSP1_JPC100(SSP1): # JPASweepShape
  DATA_SIZE = JPAChunk.HEADER_SIZE + 4 + 0x48
  
  unused_jpachunk_field: u32 = field(default=0, assert_default=True)
  
  flags: u32 = field(bitfield=True)
  shape_type: JPAShapeType = field(bits=4)
  dir_type: DirType = field(bits=3)
  rot_type: RotType = field(bits=3)
  base_plane_type: PlaneType = field(bits=1)
  unknown_1: u8 = field(bits=5, default=0, assert_default=True)
  enable_inherit_scale: bool = field(bits=1)
  enable_inherit_alpha: bool = field(bits=1)
  enable_inherit_rgb: bool = field(bits=1)
  draw_parent: bool = field(bits=1) # Should be equal to NOT bsp1.no_draw_parent
  enable_clip: bool = field(bits=1)
  enable_field: bool = field(bits=1)
  enable_scale_out: bool = field(bits=1)
  enable_alpha_out: bool = field(bits=1)
  enable_rotate: bool = field(bits=1)
  position_random: float
  base_velocity: float
  base_velocity_random: float
  velocity_inf_rate: float
  gravity: float
  timing: float
  lifetime: s16
  rate: s16
  step: u8
  _padding_1: u24
  scale: Vec2float
  rotate_speed: float
  inherit_scale: float
  inherit_alpha: float
  inherit_rgb: float
  prm_color: RGBAu8
  env_color: RGBAu8
  texture_index: u8
  _padding_2: u24

@bunfoe
class SSP1_JPC210(SSP1): # JPAChildShape
  DATA_SIZE = JPAChunk.HEADER_SIZE + 0x40
  
  flags: u32 = field(bitfield=True)
  shape_type: JPAShapeType = field(bits=4)
  dir_type: DirType = field(bits=3)
  rot_type: RotType = field(bits=3)
  base_plane_type: PlaneType = field(bits=1)
  unknown_1: u8 = field(bits=5, default=0, assert_default=True)
  enable_inherit_scale: bool = field(bits=1)
  enable_inherit_alpha: bool = field(bits=1)
  enable_inherit_rgb: bool = field(bits=1)
  unknown_2: u8 = field(bits=2) # Seems to never be read, but is sometimes nonzero. Is this leftover draw_parent and enable_clip?
  enable_field: bool = field(bits=1)
  enable_scale_out: bool = field(bits=1)
  enable_alpha_out: bool = field(bits=1)
  enable_rotate: bool = field(bits=1)
  position_random: float
  base_velocity: float
  base_velocity_random: float
  velocity_inf_rate: float
  gravity: float
  scale: Vec2float
  inherit_scale: float
  inherit_alpha: float
  inherit_rgb: float
  prm_color: RGBAu8
  env_color: RGBAu8
  timing: float
  lifetime: s16
  rate: s16
  step: u8
  texture_index: u8
  rotate_speed: s16
