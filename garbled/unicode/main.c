#include <stdio.h>
#include <locale.h>
#include <getopt.h>
#include <string.h>
#include <stdlib.h>

int main(int argc , char **argv)
{
  static const struct option options[] = {
    {"char-set", 1, NULL, 'c'},
    {"help", 0, NULL, 'h'},
    {}
  };
  int option;
  char char_set[32]={0,};
  char buffer[256]={0,};
  wchar_t wcs[256]={0,};
  char *temp=NULL;
  int i;
  /*  TODO* fix*/
  while (1) {
    option = getopt_long_only(argc, argv, "c:",
			      options, NULL);
    if (option == -1)
      break;
    switch(option) {
    case 'c':
      strncpy(char_set,optarg,32);
      break;
    case 'h':
      printf("test-internal-unicode program"
	     "Usage:\n"
	     " --help\n"
	     " --char-set\n"
	     );
      return 0;
      break;
    default:
      printf("test-internal-unicode program"
	     "Usage:\n"
	     " --help\n"
	     " --char-set\n"
	     );
      return -1;
    }
  }
    
  if (!setlocale(LC_CTYPE, char_set)) {
    fprintf(stderr, "Can't set the specified locale! "
	    "Check LANG, LC_CTYPE, LC_ALL.\n");
    return 1;
  }
  
  /*get string from stdin get char*/
  if(!fgets(buffer,255,stdin))
  {
    fprintf(stderr,"input error\n");
    return 1;
  }
  temp = strchr(buffer,'\n');
  if(temp)
    *temp = '\0';
  /*transform to unicode or utf8 or not to try to transform*/
  mbstowcs(wcs, buffer, 255);
  /*print out string which I got */
  wcs[1]='\0';
  /*ls means print wide charactor*/
  printf("WIDE CHARACTOR:%ls\n",wcs);
  /*convert to utf8 */
  
  /*not convert to utf8*/
  /*not support to other char-set*/
  /*print the first charactor*/
  
  i=0;
  /*ensure is 11xx;xxxx*/
  if ((buffer[0] & 0x80) && (buffer[0] & 0x40)) {
    /*if (buffer[0] >=  0xc0U) { */
    /*char is a signed int*/
    do {
      i++;
      /*ensuse is 1xxxxxxx and x0xxxxxxx*/
      /*so means byte's started with 10xx;xxxx*/
      /*means char > 0x80*/
    }while((buffer[i] & 0x80) && !(buffer[i] & 0x40) );
  }
  else
    i=1;
  buffer[i]='\0';
  printf("narrow utf8:%s\n", buffer);
  return 0;
}
