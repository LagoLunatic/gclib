from enum import Enum
from gclib.fs_helpers import u32, u8

class GXAttr(u32, Enum):
  PositionMatrixIndex   = 0x00
  Tex0MatrixIndex       = 0x01
  Tex1MatrixIndex       = 0x02
  Tex2MatrixIndex       = 0x03
  Tex3MatrixIndex       = 0x04
  Tex4MatrixIndex       = 0x05
  Tex5MatrixIndex       = 0x06
  Tex6MatrixIndex       = 0x07
  Tex7MatrixIndex       = 0x08
  Position              = 0x09
  Normal                = 0x0A
  Color0                = 0x0B
  Color1                = 0x0C
  Tex0                  = 0x0D
  Tex1                  = 0x0E
  Tex2                  = 0x0F
  Tex3                  = 0x10
  Tex4                  = 0x11
  Tex5                  = 0x12
  Tex6                  = 0x13
  Tex7                  = 0x14
  PositionMatrixArray   = 0x15
  NormalMatrixArray     = 0x16
  TextureMatrixArray    = 0x17
  LitMatrixArray        = 0x18
  NormalBinormalTangent = 0x19
  NULL                  = 0xFF

class GXComponentCount(u32, Enum):
  Position_XY  = 0x00
  Position_XYZ = 0x01

  Normal_XYZ  = 0x00
  Normal_NBT  = 0x01
  Normal_NBT3 = 0x02

  Color_RGB  = 0x00
  Color_RGBA = 0x01

  TexCoord_S  = 0x00
  TexCoord_ST = 0x01

class CompType(u32, Enum):
  Unsigned8  = 0x00
  Signed8    = 0x01
  Unsigned16 = 0x02
  Signed16   = 0x03
  Float32    = 0x04
  
  RGB565 = 0x00
  RGB8   = 0x01
  RGBX8  = 0x02
  RGBA4  = 0x03
  RGBA6  = 0x04
  RGBA8  = 0x05

class CompareType(u8, Enum):
  Never         = 0
  Less          = 1
  Equal         = 2
  Less_Equal    = 3
  Greater       = 4
  Not_Equal     = 5
  Greater_Equal = 6
  Always        = 7

class BlendMode(u8, Enum):
  None_    = 0x00
  Blend    = 0x01
  Logic    = 0x02
  Subtract = 0x03

class BlendFactor(u8, Enum):
  Zero                      = 0x00
  One                       = 0x01
  Source_Color              = 0x02
  Inverse_Source_Color      = 0x03
  Source_Alpha              = 0x04
  Inverse_Source_Alpha      = 0x05
  Destination_Alpha         = 0x06
  Inverse_Destination_Alpha = 0x07

class LogicOp(u8, Enum):
  CLEAR   = 0x00
  AND     = 0x01
  REVAND  = 0x02
  COPY    = 0x03
  INVAND  = 0x04
  NOOP    = 0x05
  XOR     = 0x06
  OR      = 0x07
  NOR     = 0x08
  EQUIV   = 0x09
  INV     = 0x0A
  REVOR   = 0x0B
  INVCOPY = 0x0C
  INVOR   = 0x0D
  NAND    = 0x0E
  SET     = 0x0F

class TexCoordID(u8, Enum):
  TEXCOORD0     = 0x00
  TEXCOORD1     = 0x01
  TEXCOORD2     = 0x02
  TEXCOORD3     = 0x03
  TEXCOORD4     = 0x04
  TEXCOORD5     = 0x05
  TEXCOORD6     = 0x06
  TEXCOORD7     = 0x07
  TEXCOORD_NULL = 0xFF

class TexMapID(u8, Enum):
  TEXMAP0     = 0x00
  TEXMAP1     = 0x01
  TEXMAP2     = 0x02
  TEXMAP3     = 0x03
  TEXMAP4     = 0x04
  TEXMAP5     = 0x05
  TEXMAP6     = 0x06
  TEXMAP7     = 0x07
  TEXMAP_NULL = 0xFF

class IndirectTexScale(u8, Enum):
  _1   = 0x00
  _2   = 0x01
  _4   = 0x02
  _8   = 0x03
  _16  = 0x04
  _32  = 0x05
  _64  = 0x06
  _128 = 0x07
  _256 = 0x08

class IndTexStageID(u8, Enum):
  STAGE0 = 0
  STAGE1 = 1
  STAGE2 = 2
  STAGE3 = 3

class IndTexFormat(u8, Enum):
  _8 = 0 # 8-bit texture offset
  _5 = 1 # 5-bit texture offset
  _4 = 2 # 4-bit texture offset
  _3 = 3 # 3-bit texture offset

class IndTexBiasSel(u8, Enum):
  NONE = 0
  S    = 1
  T    = 2
  ST   = 3
  U    = 4
  SU   = 5
  TU   = 6
  STU  = 7

class IndTexAlphaSel(u8, Enum):
  OFF = 0
  S   = 1
  T   = 2
  U   = 3

class IndTexMtxID(u8, Enum):
  OFF = 0
  _0  = 1
  _1  = 2
  _2  = 3
  S0  = 5
  S1  = 6
  S2  = 7
  T0  = 9
  T1  = 10
  T2  = 11

class IndTexWrap(u8, Enum):
  OFF  = 0
  _256 = 1
  _128 = 2
  _64  = 3
  _32  = 4
  _16  = 5
  _0   = 6

class ColorChannelID (u8, Enum):
  COLOR0       = 0x00
  COLOR1       = 0x01
  ALPHA0       = 0x02
  ALPHA1       = 0x03
  COLOR0A0     = 0x04
  COLOR1A1     = 0x05
  COLOR_ZERO   = 0x06
  ALPHA_BUMP   = 0x07
  ALPHA_BUMP_N = 0x08
  COLOR_NULL   = 0xFF

class CombineColor(u8, Enum):
  CPREV = 0x00 # Use the color value from previous TEV stage
  APREV = 0x01 # Use the alpha value from previous TEV stage
  C0    = 0x02 # Use the color value from the color/output register 0
  A0    = 0x03 # Use the alpha value from the color/output register 0
  C1    = 0x04 # Use the color value from the color/output register 1
  A1    = 0x05 # Use the alpha value from the color/output register 1
  C2    = 0x06 # Use the color value from the color/output register 2
  A2    = 0x07 # Use the alpha value from the color/output register 2
  TEXC  = 0x08 # Use the color value from texture
  TEXA  = 0x09 # Use the alpha value from texture
  RASC  = 0x0A # Use the color value from rasterizer
  RASA  = 0x0B # Use the alpha value from rasterizer
  ONE   = 0x0C
  HALF  = 0x0D
  KONST = 0x0E
  ZERO  = 0x0F # Use to pass zero value

class CombineAlpha(u8, Enum):
  APREV = 0x00 # Use the alpha value from previous TEV stage
  A0    = 0x01 # Use the alpha value from the color/output register 0
  A1    = 0x02 # Use the alpha value from the color/output register 1
  A2    = 0x03 # Use the alpha value from the color/output register 2
  TEXA  = 0x04 # Use the alpha value from texture
  RASA  = 0x05 # Use the alpha value from rasterizer
  KONST = 0x06
  ZERO  = 0x07 # Use to pass zero value

class TevOp(u8, Enum):
  ADD           = 0x00
  SUB           = 0x01
  COMP_R8_GT    = 0x08
  COMP_R8_EQ    = 0x09
  COMP_GR16_GT  = 0x0A
  COMP_GR16_EQ  = 0x0B
  COMP_BGR24_GT = 0x0C
  COMP_BGR24_EQ = 0x0D
  COMP_RGB8_GT  = 0x0E
  COMP_RGB8_EQ  = 0x0F
  COMP_A8_GT    = COMP_RGB8_GT
  COMP_A8_EQ    = COMP_RGB8_EQ

class TevBias(u8, Enum):
  ZERO        = 0x00
  ADDHALF     = 0x01
  SUBHALF     = 0x02
  
  # Used to denote the compare ops to the HW.
  HWB_COMPARE = 0x03

class TevScale(u8, Enum):
  SCALE_1   = 0x00
  SCALE_2   = 0x01
  SCALE_4   = 0x02
  DIVIDE_2  = 0x03

  # Used to denote the width of the compare op.
  HWB_R8    = 0x00
  HWB_GR16  = 0x01
  HWB_BGR24 = 0x02
  HWB_RGB8  = 0x03

class Register(u8, Enum):
  PREV = 0x00
  REG0 = 0x01
  REG1 = 0x02
  REG2 = 0x03

class TexGenType(u8, Enum):
  MTX3x4 = 0x00
  MTX2x4 = 0x01
  BUMP0  = 0x02
  BUMP1  = 0x03
  BUMP2  = 0x04
  BUMP3  = 0x05
  BUMP4  = 0x06
  BUMP5  = 0x07
  BUMP6  = 0x08
  BUMP7  = 0x09
  SRTG   = 0x0A

class TexGenSrc(u8, Enum):
  POS       = 0x00
  NRM       = 0x01
  BINRM     = 0x02
  TANGENT   = 0x03
  TEX0      = 0x04
  TEX1      = 0x05
  TEX2      = 0x06
  TEX3      = 0x07
  TEX4      = 0x08
  TEX5      = 0x09
  TEX6      = 0x0A
  TEX7      = 0x0B
  TEXCOORD0 = 0x0C
  TEXCOORD1 = 0x0D
  TEXCOORD2 = 0x0E
  TEXCOORD3 = 0x0F
  TEXCOORD4 = 0x10
  TEXCOORD5 = 0x11
  TEXCOORD6 = 0x12
  COLOR0    = 0x13
  COLOR1    = 0x14

class TexGenMatrix(u8, Enum):
  IDENTITY = 60
  TEXMTX0  = 30
  TEXMTX1  = 33
  TEXMTX2  = 36
  TEXMTX3  = 39
  TEXMTX4  = 42
  TEXMTX5  = 45
  TEXMTX6  = 48
  TEXMTX7  = 51
  TEXMTX8  = 54
  TEXMTX9  = 57

  # Clever games can use PNMTX as inputs to texgen.
  PNMTX0   = 0
  PNMTX1   = 3
  PNMTX2   = 6
  PNMTX3   = 9
  PNMTX4   = 12
  PNMTX5   = 15
  PNMTX6   = 18
  PNMTX7   = 21
  PNMTX8   = 24
  PNMTX9   = 27

class KonstColorSel(u8, Enum):
  _1     = 0x00 # constant 1.0
  _7_8th = 0x01 # constant 7/8
  _6_8th = 0x02 # constant 6/8
  _5_8th = 0x03 # constant 5/8
  _4_8th = 0x04 # constant 4/8
  _3_8th = 0x05 # constant 3/8
  _2_8th = 0x06 # constant 2/8
  _1_8th = 0x07 # constant 1/8
  K0     = 0x0C # K0[RGB] register
  K1     = 0x0D # K1[RGB] register
  K2     = 0x0E # K2[RGB] register
  K3     = 0x0F # K3[RGB] register
  K0_R   = 0x10 # K0[RRR] register
  K1_R   = 0x11 # K1[RRR] register
  K2_R   = 0x12 # K2[RRR] register
  K3_R   = 0x13 # K3[RRR] register
  K0_G   = 0x14 # K0[GGG] register
  K1_G   = 0x15 # K1[GGG] register
  K2_G   = 0x16 # K2[GGG] register
  K3_G   = 0x17 # K3[GGG] register
  K0_B   = 0x18 # K0[BBB] register
  K1_B   = 0x19 # K1[BBB] register
  K2_B   = 0x1A # K2[BBB] register
  K3_B   = 0x1B # K3[RBB] register
  K0_A   = 0x1C # K0[AAA] register
  K1_A   = 0x1D # K1[AAA] register
  K2_A   = 0x1E # K2[AAA] register
  K3_A   = 0x1F # K3[AAA] register

class KonstAlphaSel(u8, Enum):
  _1     = 0x00 # constant 1.0
  _7_8th = 0x01 # constant 7/8
  _6_8th = 0x02 # constant 6/8
  _5_8th = 0x03 # constant 5/8
  _4_8th = 0x04 # constant 4/8
  _3_8th = 0x05 # constant 3/8
  _2_8th = 0x06 # constant 2/8
  _1_8th = 0x07 # constant 1/8
  K0_R   = 0x10 # K0[R] register
  K1_R   = 0x11 # K1[R] register
  K2_R   = 0x12 # K2[R] register
  K3_R   = 0x13 # K3[R] register
  K0_G   = 0x14 # K0[G] register
  K1_G   = 0x15 # K1[G] register
  K2_G   = 0x16 # K2[G] register
  K3_G   = 0x17 # K3[G] register
  K0_B   = 0x18 # K0[B] register
  K1_B   = 0x19 # K1[B] register
  K2_B   = 0x1A # K2[B] register
  K3_B   = 0x1B # K3[B] register
  K0_A   = 0x1C # K0[A] register
  K1_A   = 0x1D # K1[A] register
  K2_A   = 0x1E # K2[A] register
  K3_A   = 0x1F # K3[A] register
