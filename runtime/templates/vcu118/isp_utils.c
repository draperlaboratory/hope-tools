#include <stdio.h>
#include <stdarg.h>
#include "isp_utils.h"

#define CPU_CLOCK_HZ 50000000

extern volatile uint64_t tohost;

void write_tohost(uint64_t val)
{
  tohost = val;
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

/**
 * Capture the current 64-bit cycle count.
 */
uint64_t isp_get_cycle_count(uint32_t *result_hi, uint32_t *result_lo)
{
#if __riscv_xlen == 64
	return read_csr(mcycle);
#else
	uint32_t cycle_lo, cycle_hi;
	asm volatile(
		"%=:\n\t"
		"csrr %1, mcycleh\n\t"
		"csrr %0, mcycle\n\t"
		"csrr t1, mcycleh\n\t"
		"bne  %1, t1, %=b"
		: "=r"(cycle_lo), "=r"(cycle_hi)
		: // No inputs.
		: "t1");

   // XXX: pass back hi/lo to get around unreliable 64-bit intrinsics
   if(result_hi != NULL) {
     *result_hi = cycle_hi;
   }
   if(result_lo != NULL) {
     *result_lo = cycle_lo;
   }
	 return (((uint64_t)cycle_hi) << 32) | (uint64_t)cycle_lo;
#endif
}

/**
 * Use `mcycle` counter to get usec resolution.
 * On RV32 only, reads of the mcycle CSR return the low 32 bits,
 * while reads of the mcycleh CSR return bits 63–32 of the corresponding
 * counter.
 * We convert the 64-bit read into usec. The counter overflows in roughly an hour
 * and 20 minutes. Probably not a big issue though.
 * At 50HMz clock rate, 1 us = 50 ticks
 */
uint32_t isp_get_time_usec(void)
{
	return (uint32_t)(isp_get_cycle_count(NULL, NULL) / (CPU_CLOCK_HZ / 1000000));
}

uint32_t isp_get_timer_freq()
{
  return CPU_CLOCK_HZ;
}

int t_printf(const char *s, ...)
{
  va_list vl;

  va_start(vl, s);
  printf(s, vl);
  va_end(vl);

  return 0;
}

