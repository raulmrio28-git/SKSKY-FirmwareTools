import struct
import io

def LZBDecompress(cdata) -> bytes:
	osize = struct.unpack("<L", cdata[0:4])[0]
	cdata_index = 4

	matchBits, offsetBits = struct.unpack("<HH", cdata[cdata_index:cdata_index+4])
	cdata_index += 4

	opos = 0
	rbits = 32
	rdata = struct.unpack("<L", cdata[cdata_index:cdata_index+4])[0]
	odata = bytearray(osize)

	while opos < osize:
		if rbits == 0:
			cdata_index += 4
			rdata = struct.unpack("<L", cdata[cdata_index:cdata_index+4])[0]
			rbits = 32

		header = (rdata >> 31) & 0x1
		rdata = (rdata << 1) & 0xFFFFFFFF
		rbits -= 1
		
		#1 = single
		if header == 1:
			if rbits == 0:
				cdata_index += 4
				rdata = struct.unpack("<L", cdata[cdata_index:cdata_index+4])[0]
				single = (rdata >> 24) & 0xFF
				rdata = (rdata << 8) & 0xFFFFFFFF
				rbits = 24
			elif rbits < 8:
				single = (rdata >> 24) & 0xFF
				cdata_index += 4
				rdata = struct.unpack("<L", cdata[cdata_index:cdata_index+4])[0]
				single |= (rdata >> (32 - (8 - rbits))) & 0xFF
				rdata = (rdata << (8 - rbits)) & 0xFFFFFFFF
				rbits = 32 - (8 - rbits)
			else:
				single = (rdata >> 24) & 0xFF
				rdata = (rdata << 8) & 0xFFFFFFFF
				rbits -= 8

			odata[opos] = single
			opos += 1
		else:
			if rbits == 0:
				cdata_index += 4
				rdata = struct.unpack("<L", cdata[cdata_index:cdata_index+4])[0]
				offset = (rdata >> (32 - offsetBits)) & ((1 << offsetBits) - 1)
				rdata = (rdata << offsetBits) & 0xFFFFFFFF
				rbits = 32 - offsetBits
			elif rbits < offsetBits:
				offset = (rdata >> (32 - offsetBits)) & ((1 << offsetBits) - 1)
				cdata_index += 4
				rdata = struct.unpack("<L", cdata[cdata_index:cdata_index+4])[0]
				offset |= (rdata >> (32 - (offsetBits - rbits))) & ((1 << (offsetBits - rbits)) - 1)
				rdata = (rdata << (offsetBits - rbits)) & 0xFFFFFFFF
				rbits = 32 - (offsetBits - rbits)
			else:
				offset = (rdata >> (32 - offsetBits)) & ((1 << offsetBits) - 1)
				rdata = (rdata << offsetBits) & 0xFFFFFFFF
				rbits -= offsetBits

			if rbits == 0:
				cdata_index += 4
				rdata = struct.unpack("<L", cdata[cdata_index:cdata_index+4])[0]
				match = (rdata >> (32 - matchBits)) & ((1 << matchBits) - 1)
				rdata = (rdata << matchBits) & 0xFFFFFFFF
				rbits = 32 - matchBits
			elif rbits < matchBits:
				match = (rdata >> (32 - matchBits)) & ((1 << matchBits) - 1)
				cdata_index += 4
				rdata = struct.unpack("<L", cdata[cdata_index:cdata_index+4])[0]
				match |= (rdata >> (32 - (matchBits - rbits))) & ((1 << (matchBits - rbits)) - 1)
				rdata = (rdata << (matchBits - rbits)) & 0xFFFFFFFF
				rbits = 32 - (matchBits - rbits)
			else:
				match = (rdata >> (32 - matchBits)) & ((1 << matchBits) - 1)
				rdata = (rdata << matchBits) & 0xFFFFFFFF
				rbits -= matchBits

			while match > 0 and opos<osize:
				odata[opos] = odata[opos - offset]
				opos += 1
				match -= 1
				
	return odata

if __name__ == '__main__':
	import sys
	import struct
	import os
	
	data = open(sys.argv[1], "rb").read()
	udata = LZBDecompress(data)
	open(sys.argv[2], "wb").write(udata)