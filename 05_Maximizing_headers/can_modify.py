def correct_headers(binary: list) -> list:    
    # Permissions
    binary[0x44] = 0x7

    # Entry point
    binary[0x18] = 0x70
    binary[0x19] = 0

    # Start of program headers
    binary[0x20] = 0x38

    # Start of section headers
    binary[0x29] = 0
    binary[0x28] = 0

    # Size of section headers
    binary[0x3a] = 0

    # Number of section headers
    binary[0x3c] = 0

    # String table index
    binary[0x3e] = 0

    # Overlaping headers
    binary = binary[:0x38] + binary[0x40:]

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

    for i in range(9):
        binary[0x7+i] = 0xff
    for i in range(4):
        binary[0x14+i] = 0xff

    for i in range(14):
        binary[0x28+i] = 0xff

    for i in range(4):
        binary[0x3c+i] = 0xff

    for i in range(8):
        binary[0x50+i] = 0xff

    for i in range(4):
        binary[0x60+i] = 0xff

    for i in range(8):
        binary[0x68+i] = 0xff

    binary = bytes(binary)
    with open("can_modify.bin", "wb") as f:
        f.write(binary)
