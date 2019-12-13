#include <stdio.h>
#include <stdarg.h>
#include "isp_utils.h"

void isp_test_device_pass(void)
{
  return;
}

void isp_test_device_fail(void)
{
  return;
}

uint32_t isp_get_time_usec()
{
  return 0;
}

int t_printf(const char *s, ...)
{
  va_list vl;

  va_start(vl, s);
  printf(s, vl);
  va_end(vl);

  return 0;
}

