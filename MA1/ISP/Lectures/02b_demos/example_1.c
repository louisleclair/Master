#include <stdio.h>

int main()
{
  struct { /* use struct to be sure that variables
	      are stored side by side */
    char name[40];  
    long is_admin; 
  } info;

  info.is_admin=0; /* we are not admin (yet) */
  
  printf("Name:\n");
  scanf("%s",info.name); /* copy user input into name buffer */
  printf(info.name); 
  
  if (info.is_admin) 
    printf("\n Congrats  %s! you are now admin.\n",info.name);
  else
    printf("\n Sorry %s, your are not admin.\n",info.name);

}
