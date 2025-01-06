def sign_extend(value: int, bits: int) -> int:
	mask = ((1 << 32) - 1) - ((1 << bits) - 1)
	msb = (1 << (bits - 1))
	if value & msb:
		return value | mask
	return value
	
def twos_complement_to_python(value: int, bits: int) -> int:
	if value & (1 << (bits - 1)):
		return value - (1 << bits)
	return value