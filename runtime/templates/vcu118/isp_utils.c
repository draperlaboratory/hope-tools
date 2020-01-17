#include <stdio.h>
#include <stdarg.h>
#include "isp_utils.h"

#define VCU118_TEST_ADDR 0x50000000

#define VCU118_TEST_FAIL 0x3333
#define VCU118_TEST_PASS 0x5555

void isp_test_device_pass(void)
{
  volatile uint32_t *test_device = (uint32_t *)VCU118_TEST_ADDR;
  *test_device = VCU118_TEST_PASS;
}

void isp_test_device_fail(void)
{
  volatile uint32_t *test_device = (uint32_t *)VCU118_TEST_ADDR;
  *test_device = VCU118_TEST_FAIL;
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

