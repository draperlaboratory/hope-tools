#include <stdio.h>
#include <stdarg.h>
#include "platform.h"
#include "isp_utils.h"

#define SIFIVE_TEST_ADDR 0x100000

#define SIFIVE_TEST_FAIL 0x3333
#define SIFIVE_TEST_PASS 0x5555

void isp_test_device_pass(void)
{
  volatile uint32_t *test_device = (uint32_t *)SIFIVE_TEST_ADDR;
  *test_device = SIFIVE_TEST_PASS;
}

void isp_test_device_fail(void)
{
  volatile uint32_t *test_device = (uint32_t *)SIFIVE_TEST_ADDR;
  *test_device = SIFIVE_TEST_FAIL;
}

uint32_t isp_get_time_usec()
{
  return (uint32_t)get_timer_value();
}

uint32_t isp_get_timer_freq()
{
  return (uint32_t)get_timer_freq();
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

