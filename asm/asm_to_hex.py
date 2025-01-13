def asm_to_hex(in_file: str, out_file: str):
	with open(in_file, "rb") as read_file:
		with open(out_file, "w") as write_file:
			while True:
				word = read_file.read(4)[::-1]
				if not word:
					break
				write_file.write(word.hex())
				write_file.write("\n")