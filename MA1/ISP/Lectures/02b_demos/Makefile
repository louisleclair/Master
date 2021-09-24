# compile the assembler code:
#  nasm -f elf64 xcalc.asm
#
# extract hex values of machine code:
# objdump -d xcalc.o | awk -v RS="[ \t]" '/^[0-9a-f]{2}$/{ printf "\\%s", $0}'

all: 	example_1 example_2 example_3

# shellcode for xcalc
%.shellcode: %.asm
	nasm -f elf64 $*.asm
	objdump -d $*.o | awk -v RS="[ \t]" '/^[0-9a-f]{2}$$/{ printf "\\x%s", $$0}' > $*.shellcode

# executables
example_1:	example_1.c
	gcc -g -o example_1 example_1.c

example_2:	example_2.c
	gcc -g -o example_2 example_2.c -fno-stack-protector

example_3:	example_3.c
	gcc -g -o example_3 example_3.c -fno-stack-protector -z execstack


# for testing shellcode
run_shellcode:	run_shellcode.c
	gcc -z execstack -o run_shellcode run_shellcode.c
