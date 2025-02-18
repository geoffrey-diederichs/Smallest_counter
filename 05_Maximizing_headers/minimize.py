def correct_headers(binary: list) -> list:    
    # Permissions
    binary[0x44] = 0x7

    # Entry point
    binary[0x18] = 0x70 #0x78 #0x70
    binary[0x19] = 0

    # Start of program headers
    binary[0x20] = 0x38 #0x40 #x38

    # Start of section headers
    binary[0x29] = 0
    binary[0x28] = 0

    # Number of program headers
    binary[0x38] = 0x1

    # Size of section headers
    binary[0x3a] = 0

    # Number of section headers
    binary[0x3c] = 0

    # String table index
    binary[0x3e] = 0

    # Overlapping headers
    binary = binary[:0x38] + binary[0x40:]

    return binary

def create_jump(binary: list, instr_ptr:int, sect_ptr:int, size:int) -> list:
    binary[sect_ptr:sect_ptr+size] = binary[instr_ptr:instr_ptr+size] # Copying the instructions into the header
    binary = binary[:sect_ptr+size] + [ 0xeb, instr_ptr-sect_ptr-size ] + binary[sect_ptr+size+2:] # Jump from the header to the code
    binary = binary[:instr_ptr] + [ 0xeb, 254-instr_ptr+sect_ptr ] + binary[instr_ptr+size:] # Jump from the code to the header

    return binary
    
if __name__ == "__main__":
    with open("counter.bin", "rb") as f:
        data = f.read()

    # Extracting headers and code
    headers = data[:0x78]
    code = data[0x1000:0x103c]
    binary = list(headers + code)

    # Modifying headers
    binary = correct_headers(binary)

    # Inserting code in the header section that can be modified + replacing them with jumps
    binary = create_jump(binary, 0x76, 0x7, 7) # Winning 5 bytes
    binary = create_jump(binary, 0x84-5, 0x28, 12) # Winning 10 bytes
    binary = create_jump(binary, 0x98-15, 0x50, 6) # Winning 4 bytes
    binary = create_jump(binary, 0xa6-19, 0x68, 6) # Winning 4 bytes

    # Correcting the program's hardcoded jumps
    binary[0x84] = 0xf8
    binary[0x69] = 0xa

    binary = bytes(binary)
    with open("counter.bin", "wb") as f:
        f.write(binary)
