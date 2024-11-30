import struct
import typing
import io
from enum import Enum
import construct
import re
import RLE
import LZB
import Converter
from PIL import Image
import os

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
my_imgFrames = int()

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
		
		self.my_imgArray = []
		self.my_imgOffset = find_image_offsets(self.my_imgSrcData)
		self.isAnimation = False
		self.decImage = 0
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
		work_offset = self.my_imgOffset[image]
		
		if (image >= len(self.my_imgOffset)):
			print(f"Image over range - you've chosen image {image+1} but there are {len(self.my_imgOffset)} images")
			return False
		img_hdr = BITMAP_HEADER.parse(self.my_imgSrcData[work_offset:])

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
		work_offset += BITMAP_HEADER.sizeof()
		
		if self.my_imgType == CommonImageLib_Types.TYPE_ANIMATION:
			anim_hdr = ANIMATION_HEADER.parse(self.my_imgSrcData[work_offset:])
			if not (0 < anim_hdr.nFrame <= 255):
				print(f"Invalid frame count: {anim_hdr.nFrame}")
				return False
			work_offset += ANIMATION_HEADER.sizeof()
		data_offset = struct.unpack("<L", self.my_imgSrcData[work_offset:work_offset+4])[0]

		if data_offset == 0:
			print(f"Invalid offset")
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
		
	def Decode(self, image: int):
		work_offset = self.my_imgOffset[image]
		
		if (image >= len(self.my_imgOffset)):
			print(f"Image over range - you've chosen image {image+1} but there are {len(self.my_imgOffset)} images")
			return
		self.decImage = image
		img_hdr = BITMAP_HEADER.parse(self.my_imgSrcData[work_offset:])
		magic = "".join(chr(b) for b in img_hdr.abID[:3])
		
		self.GetPackType(magic)
		self.GetType(magic)
			
		work_offset += BITMAP_HEADER.sizeof()
		if self.my_imgType == CommonImageLib_Types.TYPE_ANIMATION:
			anim_hdr = ANIMATION_HEADER.parse(self.my_imgSrcData[work_offset:])
			self.my_imgFrames = anim_hdr.nFrame
			self.my_imgDelay = anim_hdr.awDelayTime
			work_offset += ANIMATION_HEADER.sizeof()
			self.isAnimation = True
		else:
			self.my_imgFrames = 1
			self.isAnimation = False
		data_offset = struct.unpack("<L", self.my_imgSrcData[work_offset:work_offset+4])[0]
		
		work_data = self.my_imgSrcData[data_offset:]
		frame_size = int((img_hdr.Size.xWidth*img_hdr.Size.yHeight*img_hdr.nBitsPerPixel)/8)
		frame_data = bytearray(frame_size)
		self.my_imgArray = []
		print(f"Decoding image {image}")
		for _ in range(self.my_imgFrames):
			if self.my_imgPack == CommonImageLib_PackTypes.PTYPE_RLE:
				data_size = struct.unpack(">H", work_data[0:2])[0]
				work_data = work_data[2:]
				if img_hdr.nBitsPerPixel <= 8:
					dec_data = RLE.UnpackRLE(work_data[:data_size], frame_size)
				else:
					dec_data = RLE.UnpackRLE16(work_data[:data_size], frame_size)
			else:
				if self.my_imgPack == CommonImageLib_PackTypes.PTYPE_LZB:
					data_size = struct.unpack(">H", work_data[0:2])[0]
					work_data = work_data[2:]
					if struct.unpack(">H", work_data[0:2])[0] == 0:
						work_data = work_data[2:]
					dec_data = LZB.LZBDecompress(work_data[:data_size+4])
				else:
					data_size = frame_size
					dec_data = work_data[:frame_size]
			dec_data = Converter.convert_image(dec_data, img_hdr.Size.xWidth, img_hdr.Size.yHeight, img_hdr.xWidth, img_hdr.nBitsPerPixel)
			dec_frame = Image.frombytes("RGB", (img_hdr.xWidth, img_hdr.Size.yHeight), bytes(dec_data),"raw", "BGR;16")
			self.my_imgArray.append(dec_frame)
			work_data = work_data[data_size:]
	
	def Save(self, fn, ani_is_gif: bool):
		if self.isAnimation == False:
			self.my_imgArray[0].save(f"{os.path.splitext(fn)[0]}_{self.decImage}{os.path.splitext(fn)[1]}")
		else:
			if ani_is_gif == True:
				self.my_imgArray[0].save(f"{os.path.splitext(fn)[0]}_{self.decImage}.gif", save_all=True, append_images=self.my_imgArray[1:], optimize=False, duration=self.my_imgDelay, loop=0, disposal=False)	
			else:
				for b in range(self.my_imgFrames):
					self.my_imgArray[b].save(f"{os.path.splitext(fn)[0]}_{self.decImage}_{b}{os.path.splitext(fn)[1]}")