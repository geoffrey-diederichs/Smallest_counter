section .text
    global _start

_start:
    inc rdi

.init:
    mov ax, bx
    mov cl, 10
    mov ebp, 0x400045
    mov byte [ebp], 0xa

.convert:
    xor dl, dl
    div cx
    add dl, "0"
    dec ebp
    mov [ebp], dl
    test al, al
    jnz .convert

    mov ax, 1
    mov esi, ebp
    mov dl, 6
    syscall

    inc bx
    cmp bx, 0x2711
    jnz .init

    mov al, 0x3c
    syscall
