
from enum import Enum

class JPACVersion(str, Enum):
  # JEFFjpa1 = "JEFFjpa1"
  JPAC1_00 = "JPAC1-00"
  JPAC2_10 = "JPAC2-10"

class VolumeType(Enum):
  Cube     = 0x00
  Sphere   = 0x01
  Cylinder = 0x02
  Torus    = 0x03
  Point    = 0x04
  Circle   = 0x05
  Line     = 0x06

class JPAType(Enum):
  Point           = 0
  Line            = 1
  Billboard       = 2
  Direction       = 3
  Direction_Cross = 4
  Stripe          = 5
  Stripe_Cross    = 6
  Rotation        = 7
  Rotation_Cross  = 8
  Dir_Billboard   = 9
  Y_Billboard     = 10

class DirType(Enum):
  Vel       = 0
  Pos       = 1
  Pos_Inv   = 2
  Emtr_Dir  = 3
  Prev_Ptcl = 4
  None_     = 5 # TODO? not real...? check it out

class RotType(Enum):
  Y        = 0
  X        = 1
  Z        = 2
  XYZ      = 3
  Y_Jiggle = 4

class PlaneType(Enum):
  XY = 0
  XZ = 1

class TevColorArg(Enum):
  ZERO_TEXC_ONE_ZERO = 0
  ZERO_C0_TEXC_ZERO  = 1
  C0_ONE_TEXC_ZERO   = 2
  C1_C0_TEXC_ZERO    = 3
  ZERO_TEXC_C0_C1    = 4
  ZERO_ZERO_ZERO_C0  = 5

class TevAlphaArg(Enum):
  ZERO_TEXA_A0_ZERO = 0
  ZERO_ZERO_ZERO_A0 = 1

class JPABlendMode(Enum):
  None_ = 0
  Blend = 1
  Logic = 2

class JPABlendFactor(Enum):
  ZERO          = 0x00
  ONE           = 0x01
  SRC_COLOR     = 0x02
  INV_SRC_COLOR = 0x03
  DST_COLOR     = 0x04
  INV_DST_COLOR = 0x05
  SRC_ALPHA     = 0x06
  INV_SRC_ALPHA = 0x07
  DST_ALPHA     = 0x08
  INV_DST_ALPHA = 0x09

class JPALogicOp(Enum):
  CLEAR    = 0x00
  SET      = 0x01
  COPY     = 0x02
  INV_COPY = 0x03
  NOOP     = 0x04
  INV      = 0x05
  AND      = 0x06
  NAND     = 0x07
  OR       = 0x08
  NOR      = 0x09
  XOR      = 0x0A
  EQUIV    = 0x0B
  REV_AND  = 0x0C
  INV_AND  = 0x0D
  REV_OR   = 0x0E
  INV_OR   = 0x0F

class JPACompareType(Enum):
  NEVER   = 0
  LESS    = 1
  LEQUAL  = 2
  EQUAL   = 3
  NEQUAL  = 4
  GEQUAL  = 5
  GREATER = 6
  ALWAYS  = 7

class JPACalcType(Enum):
  Normal  = 0
  Repeat  = 1
  Reverse = 2
  Merge   = 3
  Random  = 4

class JPATiling(Enum):
  One = 0
  Two = 1

class AlphaWaveType(Enum):
  Nrm_Sin  = 0x00
  Add_Sin  = 0x01
  Mult_Sin = 0x02

class ScaleAnimType_JPC100(Enum):
  Repeat  = 0x00
  Reverse = 0x01

class ScaleAnimType_JPC210(Enum):
  Normal  = 0x00
  Repeat  = 0x01
  Reverse = 0x02

class JPAIndirectTextureMode(Enum):
  Off    = 0x00
  Normal = 0x01
  Sub    = 0x02

class JPAIndTexMtxID(Enum):
  ITM_0  = 0
  ITM_0_ = 1
  ITM_S0 = 2
  ITM_T0 = 3
