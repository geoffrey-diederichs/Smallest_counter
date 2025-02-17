#!/bin/sh

nasm -f elf64 counter.asm 
ld -m elf_x86_64 counter.o -o counter.bin
rm counter.o
python3 minimize.py
./counter.bin
