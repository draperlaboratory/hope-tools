#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>
#include "isp_utils.h"

extern volatile uint64_t tohost;

void write_tohost(uint64_t val)
{
  tohost = val;
  while (1);
}

void tohost_exit(uint64_t val)
{
  write_tohost(val << 1 | 1);
}

void isp_test_device_pass(void)
{
  tohost_exit(0);
}

void isp_test_device_fail(void)
{
  tohost_exit(0x10);
}

uint32_t isp_get_time_usec()
{
  return 0;
}

uint32_t isp_get_timer_freq()
{
  return 32768;
}

int t_printf(const char *s, ...)
{
  va_list vl;

  va_start(vl, s);
  printf(s, vl);
  va_end(vl);

  return 0;
}

