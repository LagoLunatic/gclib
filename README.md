
## About

Python implementations of several file formats used by various GameCube games intended for use in ROM hacking.

## Supported formats

Some of the formats are fully supported, but many are incomplete and only have partial support for editing certain attributes of the format, or for reading the format without writing it.

Below is a table of what is supported for each format. A '~' indicates partial support.

| Format | Read | Edit| Create | Description |
| ---    | :-: | :-: | :-: | --- |
| GCM    | ✓ | ✓ | ✕ | GameCube DVD images |
| DOL    | ✓ | ✓ | ✕ | Executable |
| REL    | ✓ | ✓ | ✓ | Relocatable object files |
| RARC   | ✓ | ✓ | ✓ | Archives |
| Yaz0   | ✓ | ✓ | ✓ | RLE compression |
| Yay0   | ✓ | ✓ | ✓ | RLE compression |
| BTI    | ✓ | ✓ | ✓ | Images |
| J3D    | ~ | ~ | ✕ | Container for various 3D formats |
| JPC    | ~ | ~ | ✕ | Particle effect archives |
| BMG    | ~ | ~ | ✕ | Message archives |
| BFN    | ✓ | ✕ | ✕ | Fonts |

## Installation

To install just the pure Python implementation, run:  
`pip install "gclib @ git+https://github.com/LagoLunatic/gclib.git"`

To install a faster version of certain functions written in C (such as compressing Yaz0/Yay0), instead run:  
`pip install "gclib[speedups] @ git+https://github.com/LagoLunatic/gclib.git"`
