__all__ = [
  "animation",
  "bfn",
  "bmg",
  "bti",
  "bunfoe",
  "bunfoe_types",
  "dol",
  "fs_helpers",
  "gclib_file",
  "gcm",
  "gx_enums",
  "jchunk",
  "j3d",
  "jpc",
  "rarc",
  "rel",
  "texture_utils",
  "yaz0",
]

import os
import glob
for module_path in glob.glob(glob.escape(os.path.dirname(__file__)) + "/*.py"):
  module_name, file_ext = os.path.splitext(os.path.basename(module_path))
  assert file_ext == ".py"
  if module_name == "__init__":
    continue
  assert module_name in __all__, f"{module_name} missing from __init__"

from . import *
