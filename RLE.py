import struct
import io

def UnpackRLE(source: bytes, line_byte: int) -> bytes:
	count_in_line = 0
	read_byte = 0
	
	dest = bytearray(line_byte)
	
	while count_in_line < line_byte:
		# Get a key byte
		key = source[read_byte]
		read_byte += 1
		
		# Check if it's a run of bytes field
		if (key & 0xC0) == 0xC0:
			# Clear the high bits
			repeat_count = key & ~0xC0
			
			# Get the run byte
			key = source[read_byte]
			read_byte += 1
			
			# Run the byte
			while repeat_count > 0 and count_in_line < line_byte:
				dest[count_in_line] = ~key & 0xFF
				count_in_line += 1
				repeat_count -= 1
		else:
			# Just store it
			dest[count_in_line] = ~key & 0xFF
			count_in_line += 1
			
	return dest
	
def UnpackRLE16(source: bytes, line_byte: int) -> bytes:
	count_in_line = 0
	read_byte = 0
	
	dest = bytearray(line_byte)
	
	while count_in_line * 2 < line_byte:
		# Get a key byte
		key = source[read_byte]
		read_byte += 1
		
		if key > 128:
			key = 128
			
		read_data = (source[read_byte] << 8) + source[read_byte + 1]
		read_byte += 2
		
		while key > 0:
			# Store as 16-bit word
			dest[count_in_line * 2] = (read_data >> 8) & 0xFF
			dest[count_in_line * 2 + 1] = read_data & 0xFF
			count_in_line += 1
			key -= 1
			
	return dest