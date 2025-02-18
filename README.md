# Smallest counter

In this repository, you'll find everything I did to try and make the smallest possible ELF executable in x86 that can count up to 10000.

At first when I heard about this challenge, I didn't think much of it. But it turns out it's a great way to learn more about elf file structure, assembly and low level in general (I recommend you try it on your own if this is something you'd like to learn more about).

## [Coding in assembly](/01_Assembly/)

The first thing to determine when starting this challenge is obviously the language you'll work with. C being one of the lighter programming language, it could be an option to consider :

```console
$ cat hello.c 
#include <stdio.h>
int main() {
   printf("Hello World!\n");
   return 0;
}

$ gcc hello.c -o hello && ./hello
Hello World!

$ wc -c hello
16616 hello
```

But as we can see, even a `Hello World` in C already takes up more than 16000 bytes. When I was first told about this challenge, the goal was to at least beat 500 bytes. So obviously C won't do. Which means we'll have to go even lower-level with Assembly using [this code](/01_Assembly/counter.asm) :

```asm
section .text
    global _start

_start:
    ; Initializing variables
    mov rax, r8
    mov rcx, 10
    lea rdi, [nbr+6]
    dec rdi
    mov byte [rdi], 0xa

.convert:
    ; Converting the current number to a string
    xor rdx, rdx
    div rcx
    add dl, "0"
    dec rdi
    mov [rdi], dl
    test rax, rax
    jnz .convert

    ; Write the string to stdout
    mov rax, 1
    mov rdi, 1
    mov rsi, nbr
    mov rdx, 6
    syscall

    ; Incrementing counter
    inc r8
    cmp r8, 10001
    jnz _start

    ; Exit
    mov rax, 0x3c
    syscall

section .data
nbr:
    db  0, 0, 0, 0, 0, 0;
```

In this program, `r8` contains the current number we're looking to print, which gets converted to a string using an euclidean division inside the `.convert` loop. We'll then print the resulting string using a `write` syscall, increment `r8`, and loop through this program until `r8` reaches 10001. When it does, we can just `exit`.

Another thing worth mentioning is that we're adding a line break at every string : `mov byte [rdi], 0xa`. Just like the `exit` syscall at then end, it's not really necessary and we could cut it out to shorten the code, but it's cleaner that way so we'll keep it.

Finally, we can compile our code and run it using [this script](/01_Assembly/run.sh) :

```console
$ ./run.sh > out.txt
```

Our code works just fine as you can see [here](/01_Assembly/out.txt). But the [binary](/01_Assembly/counter.bin) produced is weirdly very big :

```console
$ wc -c counter.bin 
8872 counter.bin
```

Our binary is 8000 bytes big. If you've ever done low-level before, this will immediatly seem very strange to you. Because even if we're being generous, the code we wrote couldn't possible be more than a few hundred bytes. Which means we'll have to go deeper and see what's going on inside our binary.

## [Remove unnecessary sections](/02_Remove_sections/)

When looking at our [binary](/01_Assembly/counter.bin) using `xxd`, it becomes very obvious something's wrong :

```hex
000000f0: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000100: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000110: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000120: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000130: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000140: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000150: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000160: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000170: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000180: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000190: 0000 0000 0000 0000 0000 0000 0000 0000  ................
000001a0: 0000 0000 0000 0000 0000 0000 0000 0000  ................
000001b0: 0000 0000 0000 0000 0000 0000 0000 0000  ................
000001c0: 0000 0000 0000 0000 0000 0000 0000 0000  ................
000001d0: 0000 0000 0000 0000 0000 0000 0000 0000  ................
000001e0: 0000 0000 0000 0000 0000 0000 0000 0000  ................
000001f0: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000200: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000210: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000220: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000230: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000240: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000250: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000260: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000270: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000280: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000290: 0000 0000 0000 0000 0000 0000 0000 0000  ................
```

Our program is filled with huge sections of null bytes and unnecessary data that our binary doesn't need. Those are added to executables by default when they're compiled, but to execute itself our program only needs two sections :

- the program headers containing information that the operation system will use to determine that this is an ELF executable. It contains informations such as the magic number (a signature to identify the file type), and the entry point (a pointer to the memory address where execution should start).

- `.text` : the section containing our code.

Let's extract these two sections and build a new binary using Python :

```python3
if __name__ == "__main__":
    with open("counter.bin", "rb") as f:
        data = f.read()

    # Extracting headers and code
    headers = data[:0x78]
    code = data[0x1000:0x105f]
    binary = list(headers + code)

    binary = bytes(binary)
    with open("counter.bin", "wb") as f:
        f.write(binary)
```

```console
$ python3 minimize.py

$ wc -c counter.bin 
214 counter.bin

$ xxd counter.bin
00000000: 7f45 4c46 0201 0100 0000 0000 0000 0000  .ELF............
00000010: 0200 3e00 0100 0000 0010 4000 0000 0000  ..>.......@.....
00000020: 4000 0000 0000 0000 2821 0000 0000 0000  @.......(!......
00000030: 0000 0000 4000 3800 0300 4000 0600 0500  ....@.8...@.....
00000040: 0100 0000 0400 0000 0000 0000 0000 0000  ................
00000050: 0000 4000 0000 0000 0000 4000 0000 0000  ..@.......@.....
00000060: e800 0000 0000 0000 e800 0000 0000 0000  ................
00000070: 0010 0000 0000 0000 4c89 c0b9 0a00 0000  ........L.......
00000080: 488d 3c25 0620 4000 48ff cfc6 070a 4831  H.<%. @.H.....H1
00000090: d248 f7f1 80c2 3048 ffcf 8817 4885 c075  .H....0H....H..u
000000a0: edb8 0100 0000 bf01 0000 0048 be00 2040  ...........H.. @
000000b0: 0000 0000 00ba 0600 0000 0f05 49ff c049  ............I..I
000000c0: 81f8 1127 0000 75b0 b83c 0000 000f 0500  ...'..u..<......
000000d0: 0000 0000 0000                           ......

$ ./counter.bin 
bash: ./counter.bin: cannot execute binary file: Exec format error
```

By doing so we get a much smaller binary, but we can't execute it. Let's investigate :

```console
$ readelf -a counter.bin 
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              EXEC (Executable file)
  Machine:                           Advanced Micro Devices X86-64
  Version:                           0x1
  Entry point address:               0x401000
  Start of program headers:          64 (bytes into file)
  Start of section headers:          8488 (bytes into file)
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Size of program headers:           56 (bytes)
  Number of program headers:         3
  Size of section headers:           64 (bytes)
  Number of section headers:         6
  Section header string table index: 5
readelf: Error: Reading 384 bytes extends past end of file for section headers
readelf: Error: Section headers are not available!
readelf: Error: Reading 168 bytes extends past end of file for program headers

There is no dynamic section in this file.
readelf: Error: Reading 168 bytes extends past end of file for program headers
```

We can see a lot errors, which should have been anticipated. We changed the binary drastically, without changing anything in the headers : all of the information it contains such as the number of section, or the entry point is now invalid. To make this binary executale we'll need to fix the headers :

```python
def fix_headers(binary: list) -> list:    
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
```

Another issue was some of the hardcoded pointers inside the binary that need to be fixed. But putting all of this together in [this script](/02_Remove_sections/minimize.py), we get :

```
$ cat run.sh 
#!/bin/sh

nasm -f elf64 counter.asm 
ld -m elf_x86_64 counter.o -o counter.bin
rm counter.o
python3 minimize.py
./counter.bin

$ ./run.sh > out.txt

$ wc -c counter.bin 
214 counter.bin
```

As you can see [here](/02_Remove_sections/out.txt), our program still works and we got it down to 214 bytes. This is already very small, and we could call it a day, but there is still many ways to make it smaller.

## [Optimizing register usage](/03_Optimize/)


