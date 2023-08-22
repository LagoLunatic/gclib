
from gclib.fs_helpers import u32, u16, u8, s32, s16, s8, u16Rot, FixedStr, MagicStr
from gclib.bunfoe import bunfoe, BUNFOE, Field

class Vector(BUNFOE):
  pass

@bunfoe
class Vec2float(Vector):
  x: float
  y: float
  
  @property
  def xy(self):
    return (self.x, self.y)

@bunfoe
class Vec3float(Vector):
  x: float
  y: float
  z: float
  
  @property
  def xyz(self):
    return (self.x, self.y, self.z)

@bunfoe
class Vec3u16Rot(Vector):
  x: u16Rot
  y: u16Rot
  z: u16Rot
  
  @property
  def xyz(self):
    return (self.x, self.y, self.z)

class Matrix(BUNFOE):
  pass

@bunfoe
class Matrix2x3(Matrix):
  r0: list[(float,)*3]
  r1: list[(float,)*3]

@bunfoe
class Matrix4x4(Matrix):
  r0: list[(float,)*4]
  r1: list[(float,)*4]
  r2: list[(float,)*4]
  r3: list[(float,)*4]

class RGBA(BUNFOE):
  pass

@bunfoe
class RGBAu8(RGBA):
  r: u8
  g: u8
  b: u8
  a: u8

@bunfoe
class RGBAs16(RGBA):
  r: s16
  g: s16
  b: s16
  a: s16
