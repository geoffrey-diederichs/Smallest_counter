# Smallest counter

In this repository, you'll find everything I did to try and make the smallest possible ELF executable in x86 that can count up to 10000.

At first when I heard about this challenge, I didn't think much of it. But it turns out it's a great way to learn more about ELF file structure, assembly and low level in general (I recommend you try it on your own if this is something you'd like to learn more about).

## Content

- [Coding in assembly](#coding-in-assembly)
- [Remove unnecessary sections](#remove-unnecessary-sections)
- [Optimizing the code](#optimizing-the-code)
- [Headers overlap](#headers-overlap)
- [Maximizing headers space](#maximizing-headers-space)

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

- the program headers containing information that the operating system will use to determine that this is an ELF executable. It contains informations such as the magic number (a signature to identify the file type), and the entry point (a pointer to the memory address where execution should start).

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

## [Optimizing the code](/03_Optimize/)

By analysing our disassembled code, we can see that instructions each have their own opcodes and are different numbers of bytes long :

```console
$ objdump -d 01_Assembly/counter.bin 

01_Assembly/counter.bin:     file format elf64-x86-64


Disassembly of section .text:

0000000000401000 <_start>:
  401000:	4c 89 c0             	mov    %r8,%rax
  401003:	b9 0a 00 00 00       	mov    $0xa,%ecx
  401008:	48 8d 3c 25 06 20 40 	lea    0x402006,%rdi
  40100f:	00 
  401010:	48 ff cf             	dec    %rdi
  401013:	c6 07 0a             	movb   $0xa,(%rdi)

0000000000401016 <_start.convert>:
  401016:	48 31 d2             	xor    %rdx,%rdx
  401019:	48 f7 f1             	div    %rcx
  40101c:	80 c2 30             	add    $0x30,%dl
  40101f:	48 ff cf             	dec    %rdi
  401022:	88 17                	mov    %dl,(%rdi)
  401024:	48 85 c0             	test   %rax,%rax
  401027:	75 ed                	jne    401016 <_start.convert>
  401029:	b8 01 00 00 00       	mov    $0x1,%eax
  40102e:	bf 01 00 00 00       	mov    $0x1,%edi
  401033:	48 be 00 20 40 00 00 	movabs $0x402000,%rsi
  40103a:	00 00 00 
  40103d:	ba 06 00 00 00       	mov    $0x6,%edx
  401042:	0f 05                	syscall
  401044:	49 ff c0             	inc    %r8
  401047:	49 81 f8 11 27 00 00 	cmp    $0x2711,%r8
  40104e:	75 b0                	jne    401000 <_start>
  401050:	b8 3c 00 00 00       	mov    $0x3c,%eax
  401055:	0f 05                	syscall
```

The main source of optimization during this step, was to use partial registers. As you can see with thoses two `mov` instructions :

```console
401000:	4c 89 c0             	mov    %r8,%rax
401022:	88 17                	mov    %dl,(%rdi)
```

The second move is one byte smaller then the first one because we only used `dl`, which is the lower byte of `rdx`. Using partial register we can go down to 4, 2 or 1 byte long registers.

We can also optimize the instructions used. For example  `bf 01 00 00 00   mov $0x1,%edi` is 5 bytes long, while `49 ff c0  inc %r8` is only 3 bytes long. So if `edi` is null, and we could use `inc %edi`, we'd cut 2 bytes off our binary.

Finally, we can try and optimize as much as possible the algorithm used to limit the number of instructions called. By doing all of this, we get [this code](/03_Optimize/counter.asm), which gives us :

```console
$ ./run.sh > out.txt

$ wc -c counter.bin 
180 counter.bin
```

You can see [here](/03_Optimize/out.txt) that our code worked. Our binary is now 180 bytes big, and with this step we've cut 34 bytes from it. But we're not done yet.

## [Headers overlap](/04_Headers_overlap/)

I didn't go into much details about it, but this binary actually has 2 headers :

- the program header that tells the operating system how to create the process image.

- the section header that describes the sections within the executable.

And one trick to try and cut some bytes, is to overlap these two headers. We could use some bytes that will both act as the end of the program header, and the beginning of the section header. We can do so using [this script](/04_Headers_overlap/minimize.py) :

```console
$ ./run.sh > out.txt

$ wc -c counter.bin 
172 counter.bin
```

As you can see [here](/04_Headers_overlap/out.txt), our program still works while we've cut it done to 172 bytes. But there's one last way to make it smaller.

## [Maximizing headers space](/05_Maximizing_headers/)

If we take a look at our headers :

```console
$ xxd 04_Headers_overlap/counter.bin 
00000000: 7f45 4c46 0201 0100 0000 0000 0000 0000  .ELF............
00000010: 0200 3e00 0100 0000 7000 4000 0000 0000  ..>.....p.@.....
00000020: 3800 0000 0000 0000 0000 0000 0000 0000  8...............
00000030: 0000 0000 4000 3800 0100 0000 0700 0000  ....@.8.........
00000040: 0000 0000 0000 0000 0000 4000 0000 0000  ..........@.....
00000050: 0000 4000 0000 0000 b000 0000 0000 0000  ..@.............
00000060: b000 0000 0000 0000 0010 0000 0000 0000  ................
00000070: 48ff c766 89d8 b10a bd45 0040 0067 c645  H..f.....E.@.g.E
00000080: 000a 30d2 66f7 f180 c230 ffcd 6788 5500  ..0.f....0..g.U.
00000090: 84c0 75ee 66b8 0100 89ee b206 0f05 66ff  ..u.f.........f.
000000a0: c366 81fb 1127 75cb b03c 0f05            .f...'u..<..
```

They still contain a lot of null bytes. We could wonder, are we able to use any of those ?

By modifying them, and trying to run the program afterwards I found out that we could use quite a few of them :

```console
$ cat run.sh 
#!/bin/sh

nasm -f elf64 counter.asm 
ld -m elf_x86_64 counter.o -o counter.bin
rm counter.o
python3 can_modify.py
#python3 minimize.py
#./counter.bin

$ ./run.sh 

$ xxd can_modify.bin 
00000000: 7f45 4c46 0201 01ff ffff ffff ffff ffff  .ELF............
00000010: 0200 3e00 ffff ffff 7000 4000 0000 0000  ..>.....p.@.....
00000020: 3800 0000 0000 0000 ffff ffff ffff ffff  8...............
00000030: ffff ffff ffff 3800 0100 0000 ffff ffff  ......8.........
00000040: 0000 0000 0000 0000 0000 4000 0000 0000  ..........@.....
00000050: ffff ffff ffff ffff b000 0000 0000 0000  ................
00000060: ffff ffff 0000 0000 ffff ffff ffff ffff  ................
00000070: 48ff c766 89d8 b10a bd45 0040 0067 c645  H..f.....E.@.g.E
00000080: 000a 30d2 66f7 f180 c230 ffcd 6788 5500  ..0.f....0..g.U.
00000090: 84c0 75ee 66b8 0100 89ee b206 0f05 66ff  ..u.f.........f.
000000a0: c366 81fb 1127 75cb b03c 0f05            .f...'u..<..

$ chmod +x can_modify.bin

$ ./can_modify.bin > out2.txt
```

[can_modify.py](/05_Maximizing_headers/can_modify.py) replaces some bytes with `0xff` and writes it in [can_modify.bin](/05_Maximizing_headers/can_modify.bin). As you can see [here](/05_Maximizing_headers/out2.txt), our code is still working even with these bytes being modified. Meaning that we can replace these with snipets from our code, jump from our code to these and back afterwards.

This step was by far the longest as you couldn't debug the binary. Since the last step where we overlapped the headers, most programs as GDB don't recognize the file as an ELF executable :

```gdb
gef➤  file 04_Headers_overlap/counter.bin 
"/home/geoffrey/Documents/Smallest_counter/04_Headers_overlap/counter.bin": not in executable format: file format not recognized
```

This made it pretty painfull. Also since you need to 2 bytes for `jmp` instructions, only the sections of the header that we can modify longer than 4 bytes are worth using. So by using [this script](/05_Maximizing_headers/minimize.py) that's inserting code inside the headers, adding the required `jmp` instructions and modifying some of the hardcoded values that needs to be (since we're modifying the execution code), we get :

```console
$ cat run.sh 
#!/bin/sh

nasm -f elf64 counter.asm 
ld -m elf_x86_64 counter.o -o counter.bin
rm counter.o
#python3 can_modify.py
python3 minimize.py
./counter.bin

$ ./run.sh > out.txt

$ xxd counter.bin 
00000000: 7f45 4c46 0201 01b1 0abd 4500 4000 eb68  .ELF......E.@..h
00000010: 0200 3e00 0100 0000 7000 4000 0000 0000  ..>.....p.@.....
00000020: 3800 0000 0000 0000 66f7 f180 c230 ffcd  8.......f....0..
00000030: 6788 5500 eb4b 3800 0100 0000 0700 0000  g.U..K8.........
00000040: 0000 0000 0000 0000 0000 4000 0000 0000  ..........@.....
00000050: 89ee b206 0f05 eb33 b000 0000 0000 0000  .......3........
00000060: b000 0000 0000 0000 750a b03c 0f05 eb25  ........u..<...%
00000070: 48ff c766 89d8 eb8f 67c6 4500 0a30 d2eb  H..f....g.E..0..
00000080: a784 c075 f866 b801 00eb c566 ffc3 6681  ...u.f.....f..f.
00000090: fb11 27eb d3                             ..'..
```

We used all the space in the headers that we could and our binary is still working as you can see [here](/05_Maximizing_headers/out.txt). All of this, to reach the final size of 149 bytes :

```console
$ wc -c counter.bin 
149 counter.bin
```
