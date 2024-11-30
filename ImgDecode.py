import struct
import os
import sys
from io import BytesIO
from CommonImageLib import CommonImageLib

SaveAniAsGif = True

imglib = CommonImageLib(sys.argv[1])
no_of_imgs = imglib.GetNumberOfImages()
print(f"{no_of_imgs} images")
for a in range(no_of_imgs):
	print(f"Image {a+1}: Offset {hex(imglib.my_imgOffset[a])}")
	valid = imglib.IsValid(a)
	if valid == True:
		imglib.PrintImageInfo(a)
		imglib.Decode(a)
		imglib.Save(sys.argv[2], SaveAniAsGif)