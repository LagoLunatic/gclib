from enum import Enum
from io import BytesIO
import re

from gclib import fs_helpers as fs
from gclib.bfn import BFN

class BMG:
  def __init__(self, file_entry):
    self.file_entry = file_entry
    data = self.file_entry.data
    
    self.magic = fs.read_str(data, 0, 8)
    assert self.magic == "MESGbmg1"
    self.length = fs.read_u32(data, 8)
    self.num_sections = fs.read_u32(data, 0x0C)
    
    self.sections = []
    offset = 0x20
    for section_index in range(self.num_sections):
      section = BMGSection(data, offset, self)
      self.sections.append(section)
      
      if section.magic == "INF1":
        self.inf1 = section
      elif section.magic == "DAT1":
        self.dat1 = section
      
      offset += section.size
    
    assert self.inf1
    assert self.dat1
    
    for message in self.messages:
      message.read_string()
  
  def save_changes(self):
    data = self.file_entry.data
    
    # Cut off the section data first since we're replacing this data entirely.
    data.truncate(0x20)
    data.seek(0x20)
    
    for section in self.sections:
      section.save_changes()
      
      section.data.seek(0)
      section_data = section.data.read()
      data.write(section_data)
  
  @property
  def messages(self):
    return self.inf1.messages
  
  @messages.setter
  def messages(self, value):
    self.inf1.messages = value
  
  @property
  def messages_by_id(self):
    return self.inf1.messages_by_id
  
  @messages_by_id.setter
  def messages_by_id(self, value):
    self.inf1.messages_by_id = value
  
  @property
  def add_new_message(self):
    return self.inf1.add_new_message

class BMGSection:
  def __init__(self, bmg_data, section_offset, bmg):
    self.bmg = bmg
    
    self.magic = fs.read_str(bmg_data, section_offset, 4)
    self.size = fs.read_u32(bmg_data, section_offset+4)
    
    bmg_data.seek(section_offset)
    self.data = BytesIO(bmg_data.read(self.size))
    
    if self.magic == "INF1":
      self.read_inf1()
  
  def save_changes(self):
    if self.magic == "INF1":
      self.save_inf1()
    
    # Pad the size of this section to the next 0x20 bytes.
    fs.align_data_to_nearest(self.data, 0x20)
    
    self.size = fs.data_len(self.data)
    fs.write_magic_str(self.data, 0, self.magic, 4)
    fs.write_u32(self.data, 4, self.size)
  
  def read_inf1(self):
    self.messages: list[Message] = []
    self.messages_by_id: dict[int, Message] = {}
    
    num_messages = fs.read_u16(self.data, 8)
    message_length = fs.read_u16(self.data, 0x0A)
    for message_index in range(num_messages):
      message = Message(self.data, self.bmg)
      message.read(0x10+message_index*message_length)
      self.messages.append(message)
      self.messages_by_id[message.message_id] = message
  
  def save_inf1(self):
    num_messages = len(self.messages)
    fs.write_u16(self.data, 8, num_messages)
    
    message_length = fs.read_u16(self.data, 0x0A)
    next_message_offset = 0x10
    next_string_offset = 9
    self.data.truncate(next_message_offset)
    self.data.seek(next_message_offset)
    self.bmg.dat1.data.truncate(next_string_offset)
    self.bmg.dat1.data.seek(next_string_offset)
    for message in self.messages:
      message.offset = next_message_offset
      message.string_offset = next_string_offset
      message.save_changes()
      
      next_message_offset += message_length
      next_string_offset += message.encoded_string_length
  
  def add_new_message(self, message_id):
    if message_id in self.messages_by_id:
      raise Exception("Tried to add a new message with ID %d, but a message with that ID already exists" % message_id)
    
    message = Message(self.data, self.bmg)
    message.message_id = message_id
    
    self.messages.append(message)
    self.messages_by_id[message.message_id] = message
    
    return message

class TextBoxType(Enum):
  DIALOG          = 0x0
  SPECIAL         = 0x1
  WOOD            = 0x2
  UNKNOWN_3       = 0x3
  UNKNOWN_4       = 0x4
  NONE            = 0x5
  STONE           = 0x6
  PARCHMENT       = 0x7
  UNKNOWN_8       = 0x8
  ITEM_GET        = 0x9
  HINT            = 0xA
  UNKNOWN_11      = 0xB
  UNKNOWN_12      = 0xC
  CENTERED_TEXT   = 0xD
  WIND_WAKER_SONG = 0xE

# Specify the wordwrap width of each type of text box.
# There's a switch statement on the box type at 80214048 that decides which function to call.
# The functions then hardcode what the maximum line length will be.
TEXT_BOX_TYPE_TO_MAX_LINE_LENGTH = {
  TextBoxType.DIALOG         : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.SPECIAL        : 419, # dMsg_ScreenDataValueInitItem
  TextBoxType.WOOD           : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.UNKNOWN_3      : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.UNKNOWN_4      : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.NONE           : 503, # dMsg_ScreenDataValueInitDemo
  TextBoxType.STONE          : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.PARCHMENT      : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.UNKNOWN_8      : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.ITEM_GET       : 419, # dMsg_ScreenDataValueInitItem
  TextBoxType.HINT           : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.UNKNOWN_11     : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.UNKNOWN_12     : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.CENTERED_TEXT  : 503, # dMsg_ScreenDataValueInitTalk
  TextBoxType.WIND_WAKER_SONG: 419, # dMsg_ScreenDataValueInitTact
}

class Message:
  def __init__(self, data, bmg):
    self.data = data
    self.bmg = bmg
    
    self.string_offset = None
    self.message_id = None
    self.item_price = 0
    self.next_message_id = 0
    
    self.unknown_1 = 0x60
    
    self.text_box_type = TextBoxType.DIALOG
    self.initial_draw_type = 0
    self.text_box_position = 3
    self.display_item_id = 0xFF
    self.text_alignment = 0
    
    self.initial_sound = 0
    self.initial_camera_behavior = 0
    self.initial_speaker_anim = 0
    
    self.unknown_3 = 0
    
    self.num_lines_per_box = 4
    
    self.unknown_4 = 0
  
  def read(self, offset):
    self.offset = offset
    
    data = self.data
    
    self.string_offset = fs.read_u32(data, offset)
    self.message_id = fs.read_u16(data, offset+4)
    self.item_price = fs.read_u16(data, offset+6)
    self.next_message_id = fs.read_u16(data, offset+8)
    self.unknown_1 = fs.read_u16(data, offset+0x0A)
    
    self.text_box_type = TextBoxType(fs.read_u8(data, offset+0x0C))
    self.initial_draw_type = fs.read_u8(data, offset+0x0D)
    self.text_box_position = fs.read_u8(data, offset+0x0E)
    self.display_item_id = fs.read_u8(data, offset+0x0F)
    
    self.text_alignment = fs.read_u8(data, offset+0x10)
    self.initial_sound = fs.read_u8(data, offset+0x11)
    self.initial_camera_behavior = fs.read_u8(data, offset+0x12)
    self.initial_speaker_anim = fs.read_u8(data, offset+0x13)
    
    self.unknown_3 = fs.read_u8(data, offset+0x14)
    self.num_lines_per_box = fs.read_u16(data, offset+0x15)
    self.unknown_4 = fs.read_u8(data, offset+0x17)
    
    self.string = None # Will be set after all messages are read.
  
  def save_changes(self):
    data = self.data
    
    fs.write_u32(data, self.offset, self.string_offset)
    fs.write_u16(data, self.offset+4, self.message_id)
    fs.write_u16(data, self.offset+6, self.item_price)
    fs.write_u16(data, self.offset+8, self.next_message_id)
    fs.write_u16(data, self.offset+0x0A, self.unknown_1)
    
    fs.write_u8(data, self.offset+0x0C, self.text_box_type.value)
    fs.write_u8(data, self.offset+0x0D, self.initial_draw_type)
    fs.write_u8(data, self.offset+0x0E, self.text_box_position)
    fs.write_u8(data, self.offset+0x0F, self.display_item_id)
    
    fs.write_u8(data, self.offset+0x10, self.text_alignment)
    fs.write_u8(data, self.offset+0x11, self.initial_sound)
    fs.write_u8(data, self.offset+0x12, self.initial_camera_behavior)
    fs.write_u8(data, self.offset+0x13, self.initial_speaker_anim)
    
    fs.write_u8(data, self.offset+0x14, self.unknown_3)
    fs.write_u16(data, self.offset+0x15, self.num_lines_per_box)
    fs.write_u8(data, self.offset+0x17, self.unknown_4)
    
    self.write_string()
  
  def read_string(self):
    string_pool_data = self.bmg.dat1.data
    
    self.string = ""
    initial_byte_offset = 8 + self.string_offset
    byte_offset = initial_byte_offset
    
    byte = fs.read_u8(string_pool_data, byte_offset)
    byte_offset += 1
    while byte != 0:
      if byte == 0x1A:
        # Control code.
        control_code_size = fs.read_u8(string_pool_data, byte_offset)
        byte_offset += 1
        
        self.string += "\\{%02X %02X" % (byte, control_code_size)
        
        for i in range(control_code_size-2):
          control_code_data_byte = fs.read_u8(string_pool_data, byte_offset)
          byte_offset += 1
          self.string += " %02X" % control_code_data_byte
        self.string += "}"
      else:
        # Normal character.
        self.string += chr(byte)
      
      byte = fs.read_u8(string_pool_data, byte_offset)
      byte_offset += 1
    
    self.encoded_string_length = byte_offset - initial_byte_offset
  
  def write_string(self):
    is_escaped_char = False
    index_in_str = 0
    bytes_to_write = []
    while index_in_str < len(self.string):
      char = self.string[index_in_str]
      if char == "\\":
        is_escaped_char = True
        index_in_str += 1
        continue
      
      if is_escaped_char and char == "{":
        substr = self.string[index_in_str:]
        control_code_str_len = substr.index("}") - 1
        substr = substr[1:control_code_str_len+1]
        
        control_code_byte_strs = re.findall(r"[0-9a-f]+", substr, re.IGNORECASE)
        for control_code_byte_str in control_code_byte_strs:
          byte = int(control_code_byte_str, 16)
          assert 0 <= byte <= 255
          bytes_to_write.append(byte)
        
        index_in_str += (2 + control_code_str_len)
        continue
      
      byte = ord(char)
      bytes_to_write.append(byte)
      
      index_in_str += 1
    bytes_to_write.append(0)
    
    self.encoded_string_length = len(bytes_to_write)
    
    string_pool_data = self.bmg.dat1.data
    str_start_offset = 8 + self.string_offset
    fs.write_and_pack_bytes(string_pool_data, str_start_offset, bytes_to_write, "B"*len(bytes_to_write))
  
  def word_wrap_string_part(self, font: BFN, string: str, extra_line_length=0):
    max_line_length = TEXT_BOX_TYPE_TO_MAX_LINE_LENGTH[self.text_box_type]
    max_line_length += extra_line_length
    return font.word_wrap_string(string, max_line_length)
  
  def word_wrap_string(self, font: BFN, extra_line_length=0):
    self.string = self.word_wrap_string_part(font, self.string, extra_line_length)
  
  def pad_string_to_next_4_lines(self, string: str):
    lines = string.split("\n")
    padding_lines_needed = (4 - len(lines) % 4) % 4
    for i in range(padding_lines_needed):
      lines.append("")
    return "\n".join(lines) + "\n"
  
  def construct_string_from_parts(self, font: BFN,  parts: list[str], extra_line_length=0):
    """Constructs a new string from a list of parts.
    Each part will be guaranteed to take up at least one entire text box (4 lines).
    """
    self.string = ""
    for part in parts:
      part = self.word_wrap_string_part(font, part, extra_line_length)
      part = self.pad_string_to_next_4_lines(part)
      self.string += part

try:
  from gclib.rarc import RARC
  RARC.FILE_EXT_TO_CLASS[".bmg"] = BMG
except ImportError:
  print(f"Could not register file extension with RARC in file {__file__}")
