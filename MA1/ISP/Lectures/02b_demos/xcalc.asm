; runs ///usr/bin/xcalc -display :0
				; by making a system call to excecve
				; exceve expects three parameters in rdi, rsi and rdx
	; 
section .text
    global _start

_start:

	;; get ourselves a zero
	xor 	rdx, rdx
	;; push zero
	push 	rdx
	;; push ///user/bin/xcalc  extra // to make multiple of 8 bytes
	mov 	rax,  0x636c6163782f6e69 ;in/xcalc
	push 	rax  
	mov 	rax,  0x622f7273752f2f2f ;///usr/b
	push 	rax
	;; save address in rdi
	mov 	rdi, rsp
	;; push zero
	push 	rdx
	;; push -display
	mov 	rax,  0x79616c707369642d ; -display
	push 	rax
	;; save address in rsi
	mov 	rsi, rsp
	;; push zero
	push 	rdx
	;; push :0000000  extra 0s to make multiple of 8 bytes
	mov 	rax,  0x303030303030303a ; :0000000
	push 	rax
	;; save address in rax
	mov 	rax, rsp
	;; put array of strings on the stack:
	;; push zero
	push 	rdx 		; 0
	;; push the addresses of the strings
	push 	rax		; address of ":0"
	push 	rsi		; address of "-display"
	push 	rdi		; address of "///usr/bin/xcalc
	;; put the address of the array into rsi
	mov 	rsi, rsp
	;; call execve syscall
	xor 	rax, rax
	mov	al, 0x3b
	syscall	

