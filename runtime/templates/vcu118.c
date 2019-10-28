#include <stdio.h>
#include <stdarg.h>
#include "isp_utils.h"

int t_printf(const char *s, ...)
{
  va_start(vl, s);
  printf(s, vl);
  va_end(vl);

  return 0;
}

int main(void)
{
  isp_main();

  return 0;
}
