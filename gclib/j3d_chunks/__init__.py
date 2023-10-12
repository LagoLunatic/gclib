__all__ = [
  "drw1",
  "evp1",
  "inf1",
  "jnt1",
  "mat3",
  "mdl3",
  "shp1",
  "tex1",
  "trk1",
  "ttk1",
  "vtx1",
]

import os
import glob
for module_path in glob.glob(glob.escape(os.path.dirname(__file__)) + "/*.py"):
  module_name, file_ext = os.path.splitext(os.path.basename(module_path))
  assert file_ext == ".py"
  if module_name == "__init__":
    continue
  assert module_name in __all__, f"{module_name} missing from __init__"

import importlib
from typing import Type
from gclib.jchunk import JChunk
CHUNK_TYPES: dict[str, Type[JChunk]] = {}
for chunk_module_name in __all__:
  assert len(chunk_module_name) == 4, "J3D chunk names must be 4 characters long"
  chunk_module = importlib.import_module("." + chunk_module_name, __name__)
  chunk_class_name = chunk_module_name.upper()
  assert chunk_class_name in chunk_module.__dict__, f"Module {chunk_module_name} must contain class: {chunk_class_name}"
  CHUNK_TYPES[chunk_class_name] = chunk_module.__dict__[chunk_class_name]
