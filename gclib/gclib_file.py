
from typing import Union
from io import BytesIO

from gclib.yaz0 import Yaz0

class GCLibFileEntry:
  data: BytesIO
  
  def __init__(self):
    self.data = BytesIO()
  
  def decompress_data_if_necessary(self) -> bool:
    if Yaz0.check_is_compressed(self.data):
      self.data = Yaz0.decompress(self.data)
      return True
    return False

class GCLibFile:
  """A generic parent class to handle initializing from multiple possible data sources.
  It can handle receiving binary data from a FileEntry (e.g. from inside of a RARC), from a BytesIO,
  or not receiving any initial data, instead creating a new file from scratch."""
  
  def __init__(self, file_entry_or_data: Union[GCLibFileEntry, BytesIO, None] = None):
    if isinstance(file_entry_or_data, GCLibFileEntry):
      self.file_entry = file_entry_or_data
      self.file_entry.decompress_data_if_necessary()
      self.data = self.file_entry.data
    elif isinstance(file_entry_or_data, BytesIO):
      self.data = file_entry_or_data
      if Yaz0.check_is_compressed(self.data):
        self.data = Yaz0.decompress(self.data)
      self.file_entry = None
    else:
      self.data = BytesIO()
      self.file_entry = None
