section .text
    global _start

_start:
    mov rax, r8
    mov rcx, 10
    lea rbp, [nbr+6]
    dec rbp
    mov byte [rbp], 0xa

.convert:
    xor rdx, rdx
    div rcx
    add dl, "0"
    dec rbp
    mov [rbp], dl
    test rax, rax
    jnz .convert

    mov rax, 1
    mov rdi, 1
    mov rsi, nbr
    mov rdx, 6
    syscall

    inc r8
    cmp r8, 10001
    jnz _start

    mov rax, 0x3c
    syscall

nbr:
    db  0, 0, 0, 0, 0, 0;