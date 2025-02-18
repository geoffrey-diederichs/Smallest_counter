# Smallest counter

In this repository, you'll find everything I did to try and make the smallest possible elf program in x86 that can count up to 10 000.

At first when I heard about this challenge, I didn't think much of it. But it turns out it's a great way to learn more about elf file structure, assembly and low level in general (I recommend you try it on your own if this is something you'd like to learn more about).

## Coding in assembly

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

But as we can see, even a `Hello World` in C already takes up more than 16K bytes. When I was first told about this challenge, the goal was to at least beat 500 bytes. So obviously C won't do. Which means we'll have to go even lower-level with Assembly using [this code](/01_Assembly/counter.asm) :

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

If you've ever done low-level before, this will immediatly seem very strange to you. Because even if we're being generous, the code we wrote couldn't possible be more than a few hundred bytes. Which means we'll have to go deeper and see what's going on inside our binary.

## Remove unnecessary sections


