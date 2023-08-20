
from io import BytesIO
import os
import glob
from enum import Enum

from gclib import fs_helpers as fs

from gclib.bti import BTI
from gclib.j3d import J3DChunk

IMPLEMENTED_CHUNK_TYPES = [
  "BSP1",
  "SSP1",
  "TDB1",
  "TEX1",
]

class JPACVersion(str, Enum):
  # JEFFjpa1 = "JEFFjpa1"
  JPAC1_00 = "JPAC1-00"
  JPAC2_10 = "JPAC2-10"

PARTICLE_LIST_OFFSET = {
  JPACVersion.JPAC1_00: 0x20,
  JPACVersion.JPAC2_10: 0x10,
}
PARTICLE_HEADER_SIZE = {
  JPACVersion.JPAC1_00: 0x20,
  JPACVersion.JPAC2_10: 0x8,
}
TDB1_ID_LIST_OFFSET = {
  JPACVersion.JPAC1_00: 0xC,
  JPACVersion.JPAC2_10: 0x8,
}

class JPC:
  def __init__(self, data):
    self.data = data
    self.version: JPACVersion
    self.read()
  
  def read(self):
    self.magic = fs.read_str(self.data, 0, 8)
    self.version = JPACVersion(self.magic)
    self.num_particles = fs.read_u16(self.data, 8)
    self.num_textures = fs.read_u16(self.data, 0xA)
    if self.version == JPACVersion.JPAC2_10:
      self.tex_offset = fs.read_u32(self.data, 0xC)
    
    self.particles = []
    self.particles_by_id = {}
    offset = PARTICLE_LIST_OFFSET[self.version]
    for particle_index in range(self.num_particles):
      particle = Particle(self.data, offset, self.version)
      self.particles.append(particle)
      
      if particle.particle_id in self.particles_by_id:
        raise Exception("Duplicate particle ID: %04X" % particle.particle_id)
      self.particles_by_id[particle.particle_id] = particle
      
      # The particle's size field is inaccurate in some rare cases.
      # So we instead add the size of the particle's header and each invididual chunk's size because those are accurate.
      offset += PARTICLE_HEADER_SIZE[self.version]
      for chunk in particle.chunks:
        offset += chunk.size
    
    self.textures = []
    self.textures_by_filename = {}
    if self.version == JPACVersion.JPAC2_10:
      offset = self.tex_offset
    for texture_index in range(self.num_textures):
      chunk_magic = fs.read_str(self.data, offset, 4)
      assert chunk_magic == "TEX1"
      
      size = fs.read_u32(self.data, offset+4)
      chunk_data = fs.read_sub_data(self.data, offset, size)
      texture = TEX1(chunk_data, self.version)
      texture.read(0)
      
      self.textures.append(texture)
      
      if texture.filename in self.textures_by_filename:
        raise Exception("Duplicate texture filename: %s" % texture.filename)
      self.textures_by_filename[texture.filename] = texture
      
      offset += texture.size
    
    # Populate the particle TDB1 texture filename lists.
    for particle in self.particles:
      for texture_id in particle.tdb1.texture_ids:
        texture = self.textures[texture_id]
        particle.tdb1.texture_filenames.append(texture.filename)
  
  def add_particle(self, particle):
    if particle.particle_id in self.particles_by_id:
      raise Exception("Cannot add a particle with the same name as an existing one: %04X" % particle.particle_id)
    self.particles.append(particle)
    self.particles_by_id[particle.particle_id] = particle
  
  def replace_particle(self, particle):
    if particle.particle_id not in self.particles_by_id:
      raise Exception("Cannot replace a particle that does not already exist: %04X" % particle.particle_id)
    existing_particle = self.particles_by_id[particle.particle_id]
    particle_index = self.particles.index(existing_particle)
    self.particles[particle_index] = particle
    self.particles_by_id[particle.particle_id] = particle
  
  def add_texture(self, texture):
    if texture.filename in self.textures_by_filename:
      raise Exception("Cannot add a texture with the same name as an existing one: %s" % texture.filename)
    self.textures.append(texture)
    self.textures_by_filename[texture.filename] = texture
  
  def replace_texture(self, texture):
    if texture.filename not in self.textures_by_filename:
      raise Exception("Cannot replace a texture that does not already exist: %s" % texture.filename)
    existing_texture = self.textures_by_filename[texture.filename]
    texture_id = self.textures.index(existing_texture)
    self.textures[texture_id] = texture
    self.textures_by_filename[texture.filename] = texture
  
  def extract_all_particles_to_disk(self, output_directory):
    if not os.path.isdir(output_directory):
      os.mkdir(output_directory)
    
    for particle in self.particles:
      file_name = "%04X.jpa" % particle.particle_id
      particle_path = os.path.join(output_directory, file_name)
      with open(particle_path, "wb") as f:
        particle.data.seek(0)
        f.write(particle.data.read())
        
        for texture_id in particle.tdb1.texture_ids:
          texture = self.textures[texture_id]
          texture.data.seek(0)
          f.write(texture.data.read())
  
  def import_particles_from_disk(self, input_directory):
    all_jpa_file_paths = glob.glob(glob.escape(input_directory) + "/*.jpa")
    new_particles = []
    new_textures = []
    new_textures_for_particle_id = {}
    for jpa_path in all_jpa_file_paths:
      # Read the particle itself.
      with open(jpa_path, "rb") as f:
        data = BytesIO(f.read())
      particle = Particle(data, 0)
      new_particles.append(particle)
      new_textures_for_particle_id[particle.particle_id] = []
      
      # Read the textures.
      offset = fs.data_len(particle.data)
      while True:
        if offset == fs.data_len(data):
          break
        texture = TEX1()
        texture.read(data, offset)
        new_textures.append(texture)
        new_textures_for_particle_id[particle.particle_id].append(texture)
        offset += texture.size
    
    num_particles_added = 0
    num_particles_overwritten = 0
    num_textures_added = 0
    num_textures_overwritten = 0
    
    for particle in new_particles:
      if particle.particle_id in self.particles_by_id:
        self.replace_particle(particle)
        num_particles_overwritten += 1
      else:
        num_particles_added += 1
        self.add_particle(particle)
      
      # Populate the particle's TDB1 texture filename list.
      particle.tdb1.texture_filenames = []
      for texture in new_textures_for_particle_id[particle.particle_id]:
        particle.tdb1.texture_filenames.append(texture.filename)
    
    for texture in new_textures:
      if texture.filename in self.textures_by_filename:
        self.replace_texture(texture)
        num_textures_overwritten += 1
      else:
        self.add_texture(texture)
        num_textures_added += 1
    
    return (num_particles_added, num_particles_overwritten, num_textures_added, num_textures_overwritten)
  
  def save(self):
    self.num_particles = len(self.particles)
    self.num_textures = len(self.textures)
    fs.write_magic_str(self.data, 0, self.magic, 8)
    fs.write_u16(self.data, 8, self.num_particles)
    fs.write_u16(self.data, 0xA, self.num_textures)
    if self.version == JPACVersion.JPAC2_10:
      fs.write_u32(self.data, 0xC, self.tex_offset)
    
    # Cut off the particle list and texture list since we're replacing this data entirely.
    self.data.truncate(PARTICLE_LIST_OFFSET[self.version])
    self.data.seek(PARTICLE_LIST_OFFSET[self.version])
    
    for particle in self.particles:
      # First regenerate this particle's TDB1 texture ID list based off the filenames.
      particle.tdb1.texture_ids = []
      for texture_filename in particle.tdb1.texture_filenames:
        texture = self.textures_by_filename[texture_filename]
        texture_id = self.textures.index(texture)
        particle.tdb1.texture_ids.append(texture_id)
      
      particle.save()
      
      particle.data.seek(0)
      particle_data = particle.data.read()
      self.data.write(particle_data)
    
    fs.align_data_to_nearest(self.data, 0x20, padding_bytes=b'\0')
    
    for texture in self.textures:
      texture.save()
      
      texture.data.seek(0)
      texture_data = texture.data.read()
      self.data.write(texture_data)
    
    fs.align_data_to_nearest(self.data, 0x20, padding_bytes=b'\0')

class Particle:
  def __init__(self, jpc_data, particle_offset, jpac_version: JPACVersion):
    self.version = jpac_version
    self.num_textures = None # TODO
    
    if self.version == JPACVersion.JPAC1_00:
      self.read_header_jpc100(jpc_data, particle_offset)
    elif self.version == JPACVersion.JPAC2_10:
      self.read_header_jpc210(jpc_data, particle_offset)
    true_size = self.read_chunks(jpc_data, particle_offset)
    
    jpc_data.seek(particle_offset)
    self.data = BytesIO(jpc_data.read(true_size))
  
  def read_header_jpc100(self, jpc_data, particle_offset):
    self.magic = fs.read_str(jpc_data, particle_offset, 8)
    assert self.magic == "JEFFjpa1"
    
    self.unknown_1 = fs.read_u32(jpc_data, particle_offset+8)
    self.num_chunks = fs.read_u32(jpc_data, particle_offset+0xC)
    self.size = fs.read_u32(jpc_data, particle_offset+0x10) # Not accurate in some rare cases
    
    self.num_kfa1_chunks = fs.read_u8(jpc_data, particle_offset+0x14)
    self.num_fld1_chunks = fs.read_u8(jpc_data, particle_offset+0x15)
    self.num_textures = fs.read_u8(jpc_data, particle_offset+0x16)
    self.unknown_5 = fs.read_u8(jpc_data, particle_offset+0x17)
    
    self.particle_id = fs.read_u16(jpc_data, particle_offset+0x18)
    
    self.unknown_6 = fs.read_bytes(jpc_data, particle_offset+0x1A, 6)
  
  def read_header_jpc210(self, jpc_data, particle_offset):
    self.particle_id = fs.read_u16(jpc_data, particle_offset + 0x0)
    self.num_chunks = fs.read_u16(jpc_data, particle_offset + 0x2)
    self.num_fld1_chunks = fs.read_u8(jpc_data, particle_offset + 0x4)
    self.num_kfa1_chunks = fs.read_u8(jpc_data, particle_offset + 0x5)
    self.num_tdb_chunks = fs.read_u8(jpc_data, particle_offset + 0x6)
    self.unknown_7 = fs.read_u8(jpc_data, particle_offset + 0x7)
  
  def read_chunks(self, jpc_data, particle_offset):
    self.chunks = []
    self.chunk_by_type = {}
    chunk_offset = particle_offset + PARTICLE_HEADER_SIZE[self.version]
    for chunk_index in range(0, self.num_chunks):
      chunk_magic = fs.read_str(jpc_data, chunk_offset, 4)
      if chunk_magic in IMPLEMENTED_CHUNK_TYPES:
        chunk_class = globals().get(chunk_magic, None)
      else:
        chunk_class = JPAChunk
      
      size = fs.read_u32(jpc_data, chunk_offset+4)
      chunk_data = fs.read_sub_data(jpc_data, chunk_offset, size)
      chunk = chunk_class(chunk_data, self.version)
      chunk.read(0)
      
      self.chunks.append(chunk)
      self.chunk_by_type[chunk.magic] = chunk
      
      if chunk.magic in IMPLEMENTED_CHUNK_TYPES:
        setattr(self, chunk.magic.lower(), chunk)
      
      chunk_offset += chunk.size
    
    self.tdb1.read_texture_ids(self.num_textures)
    
    true_size = (chunk_offset - particle_offset)
    return true_size
  
  def save(self):
    # Cut off the chunk data first since we're replacing this data entirely.
    self.data.truncate(PARTICLE_HEADER_SIZE[self.version])
    self.data.seek(PARTICLE_HEADER_SIZE[self.version])
    
    self.num_textures = len(self.tdb1.texture_ids)
    
    for chunk in self.chunks:
      chunk.save()
      
      chunk.data.seek(0)
      chunk_data = chunk.data.read()
      self.data.write(chunk_data)
    
    if self.version == JPACVersion.JPAC1_00:
      # We don't recalculate this size field, since this is inaccurate anyway. It's probably not even used.
      #self.size = fs.data_len(self.data)
      
      fs.write_magic_str(self.data, 0, self.magic, 8)
      fs.write_u32(self.data, 0x10, self.size)
      
      # TODO: write back all header changes.

class JPAChunk(J3DChunk):
  def __init__(self, data, version: JPACVersion):
    super().__init__(data)
    self.version = version
  
  @property
  def padding_alignment_size(self) -> int:
    if self.version == JPACVersion.JPAC1_00:
      return 0x20
    elif self.version == JPACVersion.JPAC2_10:
      return 0x4
  
  @property
  def padding_bytes(self) -> bytes:
    return b'\0'

class BSP1(JPAChunk):
  def read_chunk_specific_data(self):
    if self.version == JPACVersion.JPAC1_00:
      self.read_chunk_specific_data_jpc100()
    elif self.version == JPACVersion.JPAC2_10:
      self.read_chunk_specific_data_jpc210()
  
  def save_chunk_specific_data(self):
    if self.version == JPACVersion.JPAC1_00:
      self.save_chunk_specific_data_jpc100()
    elif self.version == JPACVersion.JPAC2_10:
      self.save_chunk_specific_data_jpc210()
    
  def read_chunk_specific_data_jpc100(self):
    self.color_flags = fs.read_u8(self.data, 0xC + 0x1B)
    
    r = fs.read_u8(self.data, 0xC + 0x20)
    g = fs.read_u8(self.data, 0xC + 0x21)
    b = fs.read_u8(self.data, 0xC + 0x22)
    a = fs.read_u8(self.data, 0xC + 0x23)
    self.color_prm = (r, g, b, a)
    r = fs.read_u8(self.data, 0xC + 0x24)
    g = fs.read_u8(self.data, 0xC + 0x25)
    b = fs.read_u8(self.data, 0xC + 0x26)
    a = fs.read_u8(self.data, 0xC + 0x27)
    self.color_env = (r, g, b, a)
    
    self.color_prm_anm_data_count = 0
    self.color_prm_anm_table = []
    if self.color_flags & 0x02 != 0:
      self.color_prm_anm_data_offset = fs.read_u16(self.data, 0xC + 0x4)
      self.color_prm_anm_data_count = fs.read_u8(self.data, 0xC + 0x1C)
      self.color_prm_anm_table = self.read_color_table(self.color_prm_anm_data_offset, self.color_prm_anm_data_count)
    
    self.color_env_anm_data_count = 0
    self.color_env_anm_table = []
    if self.color_flags & 0x08 != 0:
      self.color_env_anm_data_offset = fs.read_u16(self.data, 0xC + 0x6)
      self.color_env_anm_data_count = fs.read_u8(self.data, 0xC + 0x1D)
      self.color_env_anm_table = self.read_color_table(self.color_env_anm_data_offset, self.color_env_anm_data_count)
  
  def read_chunk_specific_data_jpc210(self):
    self.color_flags = fs.read_u8(self.data, 0x21)
    
    r = fs.read_u8(self.data, 0x26)
    g = fs.read_u8(self.data, 0x27)
    b = fs.read_u8(self.data, 0x28)
    a = fs.read_u8(self.data, 0x29)
    self.color_prm = (r, g, b, a)
    r = fs.read_u8(self.data, 0x2A)
    g = fs.read_u8(self.data, 0x2B)
    b = fs.read_u8(self.data, 0x2C)
    a = fs.read_u8(self.data, 0x2D)
    self.color_env = (r, g, b, a)
    
    self.color_prm_anm_data_count = 0
    self.color_prm_anm_table = []
    if self.color_flags & 0x02 != 0:
      self.color_prm_anm_data_offset = fs.read_u16(self.data, 0xC)
      self.color_prm_anm_data_count = fs.read_u8(self.data, 0x22)
      self.color_prm_anm_table = self.read_color_table(self.color_prm_anm_data_offset, self.color_prm_anm_data_count)
    
    self.color_env_anm_data_count = 0
    self.color_env_anm_table = []
    if self.color_flags & 0x08 != 0:
      self.color_env_anm_data_offset = fs.read_u16(self.data, 0xE)
      self.color_env_anm_data_count = fs.read_u8(self.data, 0x23)
      self.color_env_anm_table = self.read_color_table(self.color_env_anm_data_offset, self.color_env_anm_data_count)
  
  def save_chunk_specific_data_jpc100(self):
    fs.write_u8(self.data, 0xC + 0x1B, self.color_flags)
    
    r, g, b, a = self.color_prm
    fs.write_u8(self.data, 0xC + 0x20, r)
    fs.write_u8(self.data, 0xC + 0x21, g)
    fs.write_u8(self.data, 0xC + 0x22, b)
    fs.write_u8(self.data, 0xC + 0x23, a)
    r, g, b, a = self.color_env
    fs.write_u8(self.data, 0xC + 0x24, r)
    fs.write_u8(self.data, 0xC + 0x25, g)
    fs.write_u8(self.data, 0xC + 0x26, b)
    fs.write_u8(self.data, 0xC + 0x27, a)
    
    if self.color_flags & 0x02 != 0:
      # Changing size not implemented.
      assert len(self.color_prm_anm_table) == self.color_prm_anm_data_count
      self.save_color_table(self.color_prm_anm_table, self.color_prm_anm_data_offset)
    
    if self.color_flags & 0x08 != 0:
      # Changing size not implemented.
      assert len(self.color_env_anm_table) == self.color_env_anm_data_count
      self.save_color_table(self.color_env_anm_table, self.color_env_anm_data_offset)
  
  def save_chunk_specific_data_jpc210(self):
    fs.write_u8(self.data, 0x21, self.color_flags)
    
    r, g, b, a = self.color_prm
    fs.write_u8(self.data, 0x26, r)
    fs.write_u8(self.data, 0x27, g)
    fs.write_u8(self.data, 0x28, b)
    fs.write_u8(self.data, 0x29, a)
    r, g, b, a = self.color_env
    fs.write_u8(self.data, 0x2A, r)
    fs.write_u8(self.data, 0x2B, g)
    fs.write_u8(self.data, 0x2C, b)
    fs.write_u8(self.data, 0x2D, a)
    
    if self.color_flags & 0x02 != 0:
      # Changing size not implemented.
      assert len(self.color_prm_anm_table) == self.color_prm_anm_data_count
      self.save_color_table(self.color_prm_anm_table, self.color_prm_anm_data_offset)
    
    if self.color_flags & 0x08 != 0:
      # Changing size not implemented.
      assert len(self.color_env_anm_table) == self.color_env_anm_data_count
      self.save_color_table(self.color_env_anm_table, self.color_env_anm_data_offset)
  
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

class SSP1(JPAChunk):
  def read_chunk_specific_data(self):
    if self.version == JPACVersion.JPAC1_00:
      self.read_chunk_specific_data_jpc100()
    elif self.version == JPACVersion.JPAC2_10:
      self.read_chunk_specific_data_jpc210()
  
  def save_chunk_specific_data(self):
    if self.version == JPACVersion.JPAC1_00:
      self.save_chunk_specific_data_jpc100()
    elif self.version == JPACVersion.JPAC2_10:
      self.save_chunk_specific_data_jpc210()
    
  def read_chunk_specific_data_jpc100(self):
    r = fs.read_u8(self.data, 0xC + 0x3C)
    g = fs.read_u8(self.data, 0xC + 0x3D)
    b = fs.read_u8(self.data, 0xC + 0x3E)
    a = fs.read_u8(self.data, 0xC + 0x3F)
    self.color_prm = (r, g, b, a)
    r = fs.read_u8(self.data, 0xC + 0x40)
    g = fs.read_u8(self.data, 0xC + 0x41)
    b = fs.read_u8(self.data, 0xC + 0x42)
    a = fs.read_u8(self.data, 0xC + 0x43)
    self.color_env = (r, g, b, a)
  
  def read_chunk_specific_data_jpc210(self):
    r = fs.read_u8(self.data, 0x34)
    g = fs.read_u8(self.data, 0x35)
    b = fs.read_u8(self.data, 0x36)
    a = fs.read_u8(self.data, 0x37)
    self.color_prm = (r, g, b, a)
    r = fs.read_u8(self.data, 0x38)
    g = fs.read_u8(self.data, 0x39)
    b = fs.read_u8(self.data, 0x3A)
    a = fs.read_u8(self.data, 0x3B)
    self.color_env = (r, g, b, a)
    
  def save_chunk_specific_data_jpc100(self):
    r, g, b, a = self.color_prm
    fs.write_u8(self.data, 0xC + 0x3C, r)
    fs.write_u8(self.data, 0xC + 0x3D, g)
    fs.write_u8(self.data, 0xC + 0x3E, b)
    fs.write_u8(self.data, 0xC + 0x3F, a)
    r, g, b, a = self.color_env
    fs.write_u8(self.data, 0xC + 0x40, r)
    fs.write_u8(self.data, 0xC + 0x41, g)
    fs.write_u8(self.data, 0xC + 0x42, b)
    fs.write_u8(self.data, 0xC + 0x43, a)
  
  def save_chunk_specific_data_jpc210(self):
    r, g, b, a = self.color_prm
    fs.write_u8(self.data, 0x34, r)
    fs.write_u8(self.data, 0x35, g)
    fs.write_u8(self.data, 0x36, b)
    fs.write_u8(self.data, 0x37, a)
    r, g, b, a = self.color_env
    fs.write_u8(self.data, 0x38, r)
    fs.write_u8(self.data, 0x39, g)
    fs.write_u8(self.data, 0x3A, b)
    fs.write_u8(self.data, 0x3B, a)
  
class TDB1(JPAChunk):
  # Texture ID database (list of texture IDs in this JPC file used by this particle)
  
  def read_chunk_specific_data(self):
    self.texture_ids = None # Can't read these yet, we need the number of textures from the particle header.
    self.texture_filenames = [] # Leave this list empty for now, it will be populated after the texture list is read.
  
  def read_texture_ids(self, num_texture_ids):
    num_texture_ids_is_guessed = False
    if num_texture_ids is None:
      # Guess how many textures there are based on the size of the TDB1 chunk minus the header.
      num_texture_ids = ((self.size - TDB1_ID_LIST_OFFSET[self.version]) // 2)
      num_texture_ids_is_guessed = True
    
    self.texture_ids = []
    for texture_id_index in range(num_texture_ids):
      texture_id = fs.read_u16(self.data, TDB1_ID_LIST_OFFSET[self.version] + texture_id_index*2)
      self.texture_ids.append(texture_id)
    
    if num_texture_ids_is_guessed and self.texture_ids[-1] == 0 and len(self.texture_ids) % 2 == 0:
      # Sometimes there are 2 bytes of zero-padding at the end of this chunk that makes it look
      # like it has one more texture ID than it really does. Remove it.
      self.texture_ids = self.texture_ids[:-1]
  
  def save_chunk_specific_data(self):
    self.data.truncate(TDB1_ID_LIST_OFFSET[self.version])
    
    # Save the texture IDs (which were updated by the JPC's save function).
    for texture_id_index, texture_id in enumerate(self.texture_ids):
      fs.write_u16(self.data, TDB1_ID_LIST_OFFSET[self.version] + texture_id_index*2, texture_id)

class TEX1(JPAChunk):
  def read_chunk_specific_data(self):
    # This string is 0x14 bytes long, but sometimes there are random garbage bytes after the null byte.
    self.filename = fs.read_str_until_null_character(self.data, 0xC)
    
    bti_data = BytesIO(fs.read_bytes(self.data, 0x20, self.size - 0x20))
    self.bti = BTI(bti_data)
  
  def save_chunk_specific_data(self):
    self.data.seek(0x20)
    self.bti.save_header_changes()
    header_bytes = fs.read_bytes(self.bti.data, self.bti.header_offset, 0x20)
    self.data.write(header_bytes)
    
    self.bti.image_data.seek(0)
    self.data.write(self.bti.image_data.read())
    
    if self.bti.needs_palettes():
      self.bti.palette_data.seek(0)
      self.data.write(self.bti.palette_data.read())

class ColorAnimationKeyframe:
  def __init__(self, time, color):
    self.time = time
    self.color = color
