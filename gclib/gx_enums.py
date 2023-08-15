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

class GXCompType(u32, Enum):
  pass

class GXCompTypeNumber(GXCompType):
  Unsigned8  = 0x00
  Signed8    = 0x01
  Unsigned16 = 0x02
  Signed16   = 0x03
  Float32    = 0x04
  
class GXCompTypeColor(GXCompType):
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
