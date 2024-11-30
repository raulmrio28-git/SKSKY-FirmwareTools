def RGB565(r, g, b):
	return ((r>>3)<<11) | ((g>>2)<<5) | (b>>3)

def convert_image(img_data, img_swidth, img_height, img_awidth, bpp):
	output_size = img_awidth * img_height * 2
	output = bytearray(output_size)
	
	if bpp == 1:
		colors = [RGB565(255,255,255), RGB565(0,0,0)]
	elif bpp == 2:
		colors = [RGB565(0,0,0), RGB565(128,128,128), 
				 RGB565(192,192,192), RGB565(255,255,255)]
	elif bpp == 4:
		colors = [
			RGB565(0,0,0),		# BLACK
			RGB565(0,0,255),	# BLUE
			RGB565(0,255,0),	# GREEN
			RGB565(0,255,255),	# CYAN
			RGB565(255,0,0),	# RED
			RGB565(255,0,255),	# MAGENTA
			RGB565(128,0,0),	# BROWN
			RGB565(128,128,128),# GRAY
			RGB565(192,192,192),# LIGHTGRAY
			RGB565(64,64,255),	# LIGHTBLUE
			RGB565(64,255,64),	# LIGHTGREEN
			RGB565(64,255,255), # LIGHTCYAN
			RGB565(255,64,64),	# LIGHTRED
			RGB565(255,64,255), # LIGHTMAGENTA
			RGB565(255,255,0),	# YELLOW
			RGB565(255,255,255) # WHITE
		]

	for y in range(img_height):
		if bpp < 8:
			bytes_per_row = (img_swidth * bpp) // 8
			row_start = y * bytes_per_row
			
			for x in range(img_awidth):
				bit_offset = x * bpp
				byte_offset = bit_offset // 8
				bit_position = 8 - (bit_offset % 8) - bpp
				
				if row_start + byte_offset >= len(img_data):
					continue
					
				pixel_value = (img_data[row_start + byte_offset] >> bit_position) & ((1 << bpp) - 1)
				rgb565 = colors[pixel_value]
				
				out_pos = (y * img_awidth + x) * 2
				output[out_pos] = rgb565 >> 8
				output[out_pos + 1] = rgb565 & 0xFF
				
		elif bpp == 8:
			for x in range(img_awidth):
				if y * img_swidth + x >= len(img_data):
					continue
					
				pixel = img_data[y * img_swidth + x]
				r = ((pixel>>5)&0x7)<<5
				g = ((pixel>>2)&0x7)<<5
				b = (pixel&0x3)<<6
				
				rgb565 = RGB565(r,g,b)
				
				out_pos = (y * img_awidth + x) * 2
				output[out_pos] = rgb565 & 0xff
				output[out_pos + 1] = (rgb565>>8) & 0xff
				
		elif bpp == 16:
			for x in range(img_awidth):
				src_pos = (y * img_swidth + x) * 2
				if src_pos + 1 >= len(img_data):
					continue
					
				dst_pos = (y * img_awidth + x) * 2
				output[dst_pos] = img_data[src_pos]
				output[dst_pos + 1] = img_data[src_pos + 1]
	
	return output