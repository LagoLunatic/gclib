from enum import Enum

from gclib import fs_helpers as fs
from gclib.fs_helpers import u32, u24, u16, u8, s32, s16, s8, u16Rot, FixedStr, MagicStr
from gclib.jchunk import JChunk
from gclib.bunfoe import bunfoe, field, BUNFOE

class INF1NodeType(u16, Enum):
  FINISH      = 0x00
  OPEN_CHILD  = 0x01
  CLOSE_CHILD = 0x02
  JOINT       = 0x10
  MATERIAL    = 0x11
  SHAPE       = 0x12

@bunfoe
class INF1Node(BUNFOE):
  DATA_SIZE = 4
  
  type: INF1NodeType
  index: u16
  
  # TODO: hidden fields
  # parent: 'INF1Node' = field(ignore=True)
  # children: list['INF1Node'] = field(ignore=True)
  
  def read(self, offset):
    super().read(offset)
    self.parent = None
    self.children = []

class INF1(JChunk):
  # TODO: this does not properly read the hierarchy. test on tetra player model for an error.
  def read_chunk_specific_data(self):
    self.hierarchy_data_offset = fs.read_u32(self.data, 0x14)
    
    offset = self.hierarchy_data_offset
    self.flat_hierarchy = []
    self.hierarchy = []
    parent_node = None
    prev_node = None
    while True:
      if offset >= self.size:
        raise Exception("No INF1 end node found")
      
      node = INF1Node(self.data)
      node.read(offset)
      self.flat_hierarchy.append(node)
      offset += INF1Node.DATA_SIZE
      
      if node.type == INF1NodeType.FINISH:
        break
      elif node.type in [INF1NodeType.JOINT, INF1NodeType.MATERIAL, INF1NodeType.SHAPE]:
        node.parent = parent_node
        if parent_node:
          parent_node.children.append(node)
        else:
          self.hierarchy.append(node)
      elif node.type == INF1NodeType.OPEN_CHILD:
        parent_node = prev_node
      elif node.type == INF1NodeType.CLOSE_CHILD:
        parent_node = parent_node.parent
      
      prev_node = node
    
    #self.print_hierarchy_recursive(self.hierarchy)
  
  def print_hierarchy_recursive(self, nodes, indent=0):
    for node in nodes:
      print(("  "*indent) + "%s %X" % (node.type.name, node.index))
      self.print_hierarchy_recursive(node.children, indent=indent+1)
  
  def save_chunk_specific_data(self):
    offset = self.hierarchy_data_offset
    for node in self.flat_hierarchy:
      node.save(offset)
      offset += INF1Node.DATA_SIZE
