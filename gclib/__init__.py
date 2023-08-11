
import os
import glob

__all__ = [
  "bfn",
  "bmg",
  "bti",
  "dol",
  "fs_helpers",
  "gclib_file",
  "gcm",
  "gx_enums",
  "j3d",
  "jpc",
  "rarc",
  "rel",
  "texture_utils",
  "yaz0",
]

for module_path in glob.glob(glob.escape(os.path.dirname(__file__)) + "/*.py"):
  module_name, file_ext = os.path.splitext(os.path.basename(module_path))
  assert file_ext == ".py"
  if module_name == "__init__":
    continue
  assert module_name in __all__, f"{module_name} missing from __init__"

# We need to import all the file types so that they register themselves with the RARC class.
from . import *
