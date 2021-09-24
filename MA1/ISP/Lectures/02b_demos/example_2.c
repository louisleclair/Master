#include <stdio.h>
#include <string.h>

/* compile with
   gcc -o example_2 example_2.c -fno-stack-protector
*/


#define	PADDING "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" \
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
		
#define GET_SECRET "\x55\x47\x55\x55\x55\x55"

#define EXPLOIT PADDING GET_SECRET


int say_hello() {
  char name[64];
  printf("Name:");
  fgets (name,128,stdin);
  printf("\nhello ");
  printf(name);
}

int get_secret() {
  printf("The secret key is: xyzzy\n");
}

int main() {
  // printf ("%p",get_secret); // use to find address of get_secret
  say_hello();
}

