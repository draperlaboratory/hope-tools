#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include "isp_utils.h"

#define CPU_CLOCK_HZ 50000000

void isp_test_device_pass(void)
{
  exit(0);
}

void isp_test_device_fail(void)
{
  exit(0x10);
}

/**
 * Capture the current 64-bit cycle count.
 */
uint64_t isp_get_cycle_count(uint32_t *result_hi, uint32_t *result_lo)
{
  uint64_t cycle;
  uint32_t cycle_lo, cycle_hi;
#if __riscv_xlen == 64
	asm volatile("rdcycle %0" : "=r"(cycle));
  cycle_hi = cycle >> 32;
  cycle_lo = cycle & 0xFFFFFFFFU;
#else
	uint32_t cycle_lo, cycle_hi, temp_hi;
        // Loop outside of the inline assembly to avoid issues with LLVM
        // policies that don't tag inline assembly
        do {
            asm volatile(
                    "csrr %1, mcycleh\n\t"
                    "csrr %0, mcycle\n\t"
                    "csrr %2, mcycleh\n\t"
                    : "=r"(cycle_lo), "=r"(cycle_hi), "=r" (temp_hi)
                    : // No inputs.
                    : // No temps
                    );
        } while (temp_hi != cycle_hi);

   // XXX: pass back hi/lo to get around unreliable 64-bit intrinsics
   if(result_hi != NULL) {
     *result_hi = cycle_hi;
   }
   if(result_lo != NULL) {
     *result_lo = cycle_lo;
   }
	 return (((uint64_t)cycle_hi) << 32) | (uint64_t)cycle_lo;
#endif
  // XXX: pass back hi/lo to get around unreliable 64-bit intrinsics
  if(result_hi != NULL) {
    *result_hi = cycle_hi;
  }
  if(result_lo != NULL) {
    *result_lo = cycle_lo;
  }
	return cycle;
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

