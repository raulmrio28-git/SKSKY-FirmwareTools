import struct
import os
import sys
from io import BytesIO
import LZB

fd = open(sys.argv[1], "rb")
fd.seek(int(sys.argv[2], 16))

for i in range(int(sys.argv[3])):
	ring_off, ring_vol = struct.unpack("<LL", fd.read(8))
	p_offs = fd.tell()
	fd.seek(ring_off)
	print(f"Sound {i+1} offset: {hex(ring_off)}, volume: {ring_vol}")
	magic = fd.read(4)
	if magic == b"MMMD": # MMF found
		size = struct.unpack(">L", fd.read(4))[0] + 12
	else: #LZB compressed MMF found
		fd.seek(ring_off)
		size = struct.unpack("<L", fd.read(4))[0] + 0x10000
	fd.seek(ring_off)
	data = fd.read(size)
	if magic != b"MMMD":
		data = LZB.LZBDecompress(data)
	open(f"{os.path.splitext(sys.argv[4])[0]}_{i}_{hex(ring_off)}{os.path.splitext(sys.argv[4])[1]}", "wb").write(data)
	fd.seek(p_offs)