
from gclib import fs_helpers as fs
from gclib.jchunk import JPAChunk
from gclib.jpa_enums import JPACVersion, JPAIndTexMtxID, JPAIndirectTextureMode
from gclib.fs_helpers import u32, u24, u16, u8, s32, s16, s8, f32, u16Rot, FixedStr, MagicStr
from gclib.bunfoe import BUNFOE, bunfoe, field
from gclib.bunfoe_types import Vec2float, Vec3float, Matrix2x3, Matrix4x4, RGBAu8, RGBAs16, Vec3u16Rot

class ETX1(JPAChunk):
  def __new__(cls, *args, **kwargs):
    if cls != ETX1:
      return super().__new__(cls)
    data, version = args
    if version == JPACVersion.JPAC1_00:
      return ETX1_JPC100(data, version)
    elif version == JPACVersion.JPAC2_10:
      return ETX1_JPC210(data, version)
    return super().__new__(cls)

@bunfoe
class ETX1_JPC100(ETX1): # JPAExTexShape
  DATA_SIZE = JPAChunk.HEADER_SIZE + 4 + 0x24
  
  unused_jpachunk_field: u32 = field(default=0, assert_default=True)
  
  flags: u32 = field(bitfield=True)
  indirect_texture_mode: JPAIndirectTextureMode = field(bits=2)
  indirect_texture_matrix_id: JPAIndTexMtxID = field(bits=2)
  unknown_1: u8 = field(bits=4, default=0, assert_default=True)
  enable_second_texture: bool = field(bits=1)
  indirect_texture_matrix: Matrix2x3
  matrix_scale_exponent: s8
  _padding_1: u24
  indirect_texture_index: u8
  sub_texture_index: u8
  second_texture_index: u8
  _padding_2: u8

@bunfoe
class ETX1_JPC210(ETX1): # JPAExTexShape
  DATA_SIZE = JPAChunk.HEADER_SIZE + 0x20

  flags: u32 = field(bitfield=True)
  indirect_texture_mode: JPAIndirectTextureMode = field(bits=1)
  unknown_1: u8 = field(bits=7, default=0, assert_default=True)
  enable_second_texture: bool = field(bits=1)
  indirect_texture_matrix: Matrix2x3
  matrix_scale_exponent: s8
  indirect_texture_index: s8
  second_texture_index: s8
  _padding: u8
