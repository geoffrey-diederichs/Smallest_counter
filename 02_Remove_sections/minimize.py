def correct_headers(binary: list) -> list:    
    # Permissions
    binary[0x44] = 0x7

    # Entry point
    binary[0x18] = 0x78
    binary[0x19] = 0

    # Start of section headers
    binary[0x29] = 0
    binary[0x28] = 0

    # Size of section headers
    binary[0x3a] = 0

    # Number of section headers
    binary[0x3c] = 0

    # String table index
    binary[0x3e] = 0

    return binary

if __name__ == "__main__":
    with open("counter.bin", "rb") as f:
        data = f.read()

    # Extracting headers and code
    headers = data[:0x78]
    code = data[0x1000:0x105f]
    binary = list(headers + code)

    # Modifying headers
    binary = correct_headers(binary)

    # Modifying pointers to nbr
    binary[0x85] = 0
    binary[0x84] = 0xd7
    binary[0xb0] = 0
    binary[0xaf] = 0xd1

    binary = bytes(binary)
    with open("counter.bin", "wb") as f:
        f.write(binary)
