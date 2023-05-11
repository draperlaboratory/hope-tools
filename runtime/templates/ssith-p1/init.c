#include <stdint.h>
#include "uart.h"

extern int main(void);

#define write_csr(reg, val) \
  asm volatile ("csrw " #reg ", %0" :: "r"(val))

#define read_csr(reg) ({ unsigned long __tmp;               \
            asm volatile ("csrr %0, " #reg : "=r"(__tmp));  \
            __tmp; })

void bad_trap(){
  unsigned long mepc, mtval, mcause;
  asm volatile("csrr %0, mcause" : "=r"(mcause));
  asm volatile("csrr %0, mtval" : "=r"(mtval));
  asm volatile("csrr %0, mepc" : "=r"(mepc));
  printf("\n FAILURE: \n mcause=0x%lx\n, mepc=0x%lx \n, mtval=0x%lx \n", mcause, mepc, mtval);
}

void _init(void)
{
  int result;

  uart0_init();

  // set up a bad trap handler
  write_csr(mtvec, ((uintptr_t)&bad_trap));

  // set up floating point computation
  uintptr_t misa, mstatus;
  asm volatile("csrr %0, misa" : "=r"(misa));
  if (misa & (1 << ('f' - 'a'))) {
    asm volatile("csrr %0, mstatus" : "=r"(mstatus));
    mstatus |= 0x6000;
    asm volatile("csrw mstatus, %0; csrw frm, 0" :: "r"(mstatus));
  }

  result = main();

  // isp_run_app should exit upon seeing this message
  printf("Program exited with code: %d\n", result);

  for(;;);
}
