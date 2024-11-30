import struct
import typing
import io
from enum import Enum
import construct
import re
#import ImageRLE
#import ImageLZB

DEBUG = False

COORD = construct.Int16sl  

SIZE = construct.Struct(
	"xWidth" / COORD,
	"yHeight" / COORD
)

BITMAP_HEADER = construct.Struct(
	# abID: 4 bytes (array of bytes)
	"abID" / construct.Array(4, construct.Byte),
	
	# Size: SIZE structure (contains xWidth and yHeight)
	"Size" / SIZE,
	
	# xWidth: COORD (2 bytes)
	"xWidth" / COORD,
	
	# nBitsPerPixel: INT8 (1 byte unsigned)
	"nBitsPerPixel" / construct.Int8ul,
	
	# fPalette: BOOL (1 byte, represented as Byte here)
	"fPalette" / construct.Byte,
	
	# TransparentColor: WORD (2 bytes unsigned, little-endian)
	"TransparentColor" / construct.Int16ul,
	
	# yStart: COORD (2 bytes)
	"yStart" / COORD,
	
	# Reserved area: 32 bytes (array of bytes)
	"abReserved" / construct.Array(32, construct.Byte)
)

ANIMATION_HEADER = construct.Struct(
	# nFrame: WORD (2 bytes unsigned, little-endian), stored as 1 byte
	"nFrame" / construct.Int16ul,

	# awDelayTime: 100 bytes (array of WORDs)
	"awDelayTime" / construct.Array(50, construct.Int16ul),
	
	# Reserved area: 2 bytes (array of bytes) (animations are stored with this padding word)
	"abReserved" / construct.Array(2, construct.Byte),
)

my_imgSrcData = bytes()
my_imgOffset = list()
my_imgArray = list()

class CommonImageLib_Types(Enum):
	TYPE_UNKNOWN = 0
	TYPE_IMAGE = 1
	TYPE_ANIMATION = 2

class CommonImageLib_PackTypes(Enum):
	PTYPE_UNKNOWN = 0
	PTYPE_RAW = 1
	PTYPE_RLE = 2
	PTYPE_LZB = 3
		
def find_image_offsets(data: bytes) -> list:
	pattern = rb'(?:IMG|ANI|XMG|XNI|ZMG|ZNI)\x00'
	
	matches = [(match.group(), match.start()) for match in re.finditer(pattern, data)]
	
	return [offset for _, offset in matches]

class CommonImageLib():
	def __init__(self, filename: str):
		self.my_imgSrcData = bytes()
		self.my_imgOffset = list()
		
		with open(filename, 'rb') as f:
			self.my_imgSrcData = f.read()
		
		self.my_imgOffset = find_image_offsets(self.my_imgSrcData)
		if DEBUG:
			for a in range(self.GetNumberOfImages()):
				print(f"Found an {self.my_imgSrcData[self.my_imgOffset[a]:self.my_imgOffset[a]+4].decode()} at offset: {self.my_imgOffset[a]}")
	
	def GetNumberOfImages(self) -> int:
		return len(self.my_imgOffset)
	
	def GetPackType(self, data: bytes):
		if data[0] == 'X':
			self.my_imgPack = CommonImageLib_PackTypes.PTYPE_RLE
		else:
			if data[0] == 'Z':
				self.my_imgPack = CommonImageLib_PackTypes.PTYPE_LZB
			else:
					self.my_imgPack = CommonImageLib_PackTypes.PTYPE_RAW

	def GetType(self, data: bytes):
		if data[1] == 'N' and data[2] == 'I':
			self.my_imgType = CommonImageLib_Types.TYPE_ANIMATION
		else:
			self.my_imgType = CommonImageLib_Types.TYPE_IMAGE

	def IsValid(self, image: int) -> bool:
		if (image >= len(self.my_imgOffset)):
			print(f"Image over range - you've chosen image {image+1} but there are {len(self.my_imgOffset)} images")
			return False
		img_hdr = BITMAP_HEADER.parse(self.my_imgSrcData[self.my_imgOffset[image]:])

		magic = "".join(chr(b) for b in img_hdr.abID[:3])
		valid_magic = {"IMG", "ANI", "XMG", "XNI", "ZMG", "ZNI"}
		if magic not in valid_magic:
			print(f"Invalid magic: {magic}")
			return False
		
		if img_hdr.nBitsPerPixel not in {1, 2, 8, 16}:
			print(f"Invalid bits per pixel: {img_hdr.nBitsPerPixel}")
			return False
		
		if not (0 < img_hdr.xWidth <= 240 and 0 < img_hdr.Size.yHeight <= 320):
			print(f"Invalid dimensions: {img_hdr.xWidth}x{img_hdr.Size.yHeight}")
			return False
		
		self.GetType(magic)
		
		if self.my_imgType == CommonImageLib_Types.TYPE_ANIMATION:
			anim_hdr = ANIMATION_HEADER.parse(self.my_imgSrcData[self.my_imgOffset[image]+BITMAP_HEADER.sizeof():])
			if not (0 < anim_hdr.nFrame <= 255):
				print(f"Invalid frame count: {anim_hdr.nFrame}")
				return False
		
		return True
	
	def PrintImageInfo(self, image: int):
		work_offset = self.my_imgOffset[image]
		
		if (image >= len(self.my_imgOffset)):
			print(f"Image over range - you've chosen image {image+1} but there are {len(self.my_imgOffset)} images")
			return
		img_hdr = BITMAP_HEADER.parse(self.my_imgSrcData[work_offset:])
		magic = "".join(chr(b) for b in img_hdr.abID[:3])
		
		self.GetPackType(magic)
		
		if self.my_imgPack == CommonImageLib_PackTypes.PTYPE_RLE:
			fmt_string = "RLE "
		else:
			if self.my_imgPack == CommonImageLib_PackTypes.PTYPE_LZB:
				fmt_string = "LZB "
			else:
				if self.my_imgPack == CommonImageLib_PackTypes.PTYPE_RAW:
					fmt_string = "Raw "
		
		self.GetType(magic)
		
		if self.my_imgType == CommonImageLib_Types.TYPE_ANIMATION:
			fmt_string += "animation"
		else:
			if self.my_imgType == CommonImageLib_Types.TYPE_IMAGE:
				fmt_string += "image"
			
		print(f"{fmt_string}, Size: {img_hdr.xWidth}x{img_hdr.Size.yHeight}, {img_hdr.nBitsPerPixel}bpp")
		work_offset += BITMAP_HEADER.sizeof()
		if self.my_imgType == CommonImageLib_Types.TYPE_ANIMATION:
			anim_hdr = ANIMATION_HEADER.parse(self.my_imgSrcData[work_offset:])
			print(f"{anim_hdr.nFrame} frames")
			for i in range(anim_hdr.nFrame):
				print(f"Frame {i} delay: {anim_hdr.awDelayTime[i]}ms")
			work_offset += ANIMATION_HEADER.sizeof()
		data_offset = struct.unpack("<L", self.my_imgSrcData[work_offset:work_offset+4])
		
	def Get(self, image: int):
		work_offset = self.my_imgOffset[image]
		
		if (image >= len(self.my_imgOffset)):
			print(f"Image over range - you've chosen image {image+1} but there are {len(self.my_imgOffset)} images")
			return
		img_hdr = BITMAP_HEADER.parse(self.my_imgSrcData[work_offset:])
		magic = "".join(chr(b) for b in img_hdr.abID[:3])
		
		self.GetPackType(magic)
		self.GetType(magic)
			
		work_offset += BITMAP_HEADER.sizeof()
		if self.my_imgType == CommonImageLib_Types.TYPE_ANIMATION:
			anim_hdr = ANIMATION_HEADER.parse(self.my_imgSrcData[work_offset:])
			frames = animhdr.nFrame
			work_offset += ANIMATION_HEADER.sizeof()
		else:
			frames = 1
		data_offset = struct.unpack("<L", self.my_imgSrcData[work_offset:work_offset+4])