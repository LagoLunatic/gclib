
from typing import Optional
from io import BytesIO
import os
import glob

from gclib import fs_helpers as fs
from gclib.jchunk import JPAChunk
from gclib.jpa_enums import JPACVersion
from gclib.jpa_chunks import CHUNK_TYPES
from gclib.jpa_chunks.bsp1 import BSP1
from gclib.jpa_chunks.ssp1 import SSP1
from gclib.jpa_chunks.tdb1 import TDB1
from gclib.jpa_chunks.tex1 import TEX1

PARTICLE_LIST_OFFSET = {
  JPACVersion.JPAC1_00: 0x20,
  JPACVersion.JPAC2_10: 0x10,
}
PARTICLE_HEADER_SIZE = {
  JPACVersion.JPAC1_00: 0x20,
  JPACVersion.JPAC2_10: 0x8,
}

class JPC:
  tex1: TEX1
  
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
    
    self.particles: list[JParticle] = []
    self.particles_by_id: dict[int, JParticle] = {}
    offset = PARTICLE_LIST_OFFSET[self.version]
    for particle_index in range(self.num_particles):
      particle = JParticle(self.data, offset, self.version)
      self.particles.append(particle)
      
      if particle.particle_id in self.particles_by_id:
        raise Exception("Duplicate particle ID: %04X" % particle.particle_id)
      self.particles_by_id[particle.particle_id] = particle
      
      # The particle's size field is inaccurate in some rare cases.
      # So we instead add the size of the particle's header and each invididual chunk's size because those are accurate.
      offset += PARTICLE_HEADER_SIZE[self.version]
      for chunk in particle.chunks:
        offset += chunk.size
    
    self.textures: list[TEX1] = []
    self.textures_by_filename: dict[str, TEX1] = {}
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
    texture_id = [tex.filename for tex in self.textures].index(texture.filename)
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
        jpa_data = BytesIO(f.read())
      particle = JParticle(jpa_data, 0, self.version)
      new_particles.append(particle)
      new_textures_for_particle_id[particle.particle_id] = []
      
      # Read the textures.
      offset = fs.data_len(particle.data)
      while True:
        if offset == fs.data_len(jpa_data):
          break
        size = fs.read_u32(jpa_data, offset+4)
        chunk_data = fs.read_sub_data(jpa_data, offset, size)
        texture = TEX1(chunk_data, self.version)
        texture.read(0)
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
        texture_id = [tex.filename for tex in self.textures].index(texture_filename)
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

class JParticle:
  # bem1: BEM1
  bsp1: BSP1
  # esp1: Optional[ESP1]
  # etx1: Optional[ETX1]
  ssp1: Optional[SSP1]
  # fld1: list[FLD1] # TODO: properly handle lists of fields
  # kfa1: list[KFA1]
  tdb1: Optional[TDB1]
  
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
    self.chunks: list[JPAChunk] = []
    self.chunk_by_type: dict[str, JPAChunk] = {}
    chunk_offset = particle_offset + PARTICLE_HEADER_SIZE[self.version]
    for chunk_index in range(0, self.num_chunks):
      chunk_magic = fs.read_str(jpc_data, chunk_offset, 4)
      chunk_class = CHUNK_TYPES.get(chunk_magic, JPAChunk)
      
      size = fs.read_u32(jpc_data, chunk_offset+4)
      chunk_data = fs.read_sub_data(jpc_data, chunk_offset, size)
      chunk = chunk_class(chunk_data, self.version)
      chunk.read(0)
      
      self.chunks.append(chunk)
      self.chunk_by_type[chunk.magic] = chunk
      
      if chunk.magic in CHUNK_TYPES:
        setattr(self, chunk.magic.lower(), chunk)
      
      chunk_offset += chunk.size
    
    self.tdb1.read_texture_ids(self.num_textures)
  
    # self.verify_valid_chunks()
    
    true_size = (chunk_offset - particle_offset)
    return true_size
  
  def verify_valid_chunks(self):
    class_attrs = type(self).__annotations__
    for chunk_magic, chunk_class in CHUNK_TYPES.items():
      chunk_attr = chunk_magic.lower()
      if chunk_attr in class_attrs:
        if class_attrs[chunk_attr] == chunk_class:
          assert getattr(self, chunk_attr) is not None
  
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
