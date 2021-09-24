# Demos of the lecture 03b

These are the three programs from the lecture on buffer overflows and format
string vulnerabilities.

## Compiling

Example_2 must be compiled with `-fno-stack-protector` to prevent the use of
stack canaries to protect the stack. 

Example_3 must be compiled with `-fno-stack-protector` and `-z execstack` to
disable stack canaries and make the stack executable.

These setting will be applied automatically if you compile the programs with the
makefile. Just type 

    make

For example\_2 and example\_3 ASLR must be disabled with the following command:

    echo 0 | sudo tee /proc/sys/kernel/randomize_va_space

Do not forget to re-enable it later with

    echo 0 | sudo tee /proc/sys/kernel/randomize_va_space


## Exploits

You can run the exploits by redirecting the into the programs: 

    ./example1 < exploit_1
	./example1 < exploit_1.formatstring
    ./example2 < exploit_2
	./example2 < exploit_2.formatsring
	./example2 < exploit_3
	
When run the programs in gdb the stack is higher. You can use the gdb versions
of the exploits: 

	gdb> file example_1
	gdb> run < exploit_1
	gdb> run < exploit_1.formatstring.gdb

	gdb> file example_2  # addresses of functions don't change in gdb
	gdb> run < exploit_2 
	gdb> run < exploit_2.formatstring

	gdb> file example_3
	gdb> run < exploit_3.gdb
	
The formatstring exploits also work with stack canaries
enabled. `exploit_2.formatstring` must be adapted if you compile without
`f-no-stackprotection`. 

     gcc -g -o example_2 example_2.c
	 ./example_2 < exploit_2.formatstring.stackprotection


## Note

You stack addresses will most probably be different than on my machine. Thus the
addresses must be adapted, except for `exploit_1`, `exploit_2` and
`exploit_2.formatstring`.


# gdb shellcode

The assembler code for running xcalc is in xcalc.asm. It can be compiled to
ascii shellcode with the Makefile (`make xcalc.shellcode`). You can install
xcalc with `sudo apt install x11-apps`



