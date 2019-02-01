#include <stdio.h>
#include <stdarg.h>
#include "platform.h"
#include "isp_utils.h"

uint32_t get_usec_time()
{
  return (uint32_t)get_timer_value();
}

uint32_t get_inst_ret()
{
  uint64_t instret;
  asm volatile ("csrr %0, 0xc02 " : "=r"(instret));
  return instret;
}

uint32_t uiPortGetWallTimestampUs()
{
  return (uint32_t)get_timer_value();
}

int t_printf(const char *s, ...)
{
  char buf[128];
  va_list vl;

  const char *p = &buf[0];

  va_start(vl, s);
  vsnprintf(buf, sizeof buf, s, vl);
  va_end(vl);

  puts(p);

  return 0;
}

int main(void)
{
  isp_main();

  return 0;
}
