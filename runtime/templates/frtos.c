#include <stdarg.h>
#include <stdio.h>
#include "FreeRTOS.h"
#include "task.h"

#include "utils.h"
#include "isp_utils.h"

void main_task(void*);
void main_task(void *argument)
{
  unsigned long result;

  result = (unsigned long)isp_main();
  vTaskDelay(1);

  printf_uart("\nMain task has completed with code: 0x%08x\n", result);
  for( ;; );

  // this may need changes to portable layer
  vTaskEndScheduler();
}

int main(void)
{
  xTaskCreate(main_task, "Main task", 1000, NULL, 1, NULL);
  
  vTaskStartScheduler();

  // never reached
  return 0;
}

/* ---------------------------- stuff to make FreeRTOS work ---------------------- */

/* 
 * This function must return uS timestamp with an order of magnitude
 * more resolution than FreeRTOS tick
 */
extern uint32_t uiPortGetWallTimestampUs(void);

unsigned long sys_GetWallTimestampUs(void);
unsigned long sys_GetWallTimestampUs(void)
{
    /* TBD on real FPGA hw */
  return uiPortGetWallTimestampUs();
}

void printk(const char*, ...);
void printk(const char* s, ...)
{
  va_list vl;

  va_start(vl, s);
  printf_uart(s, vl);
  va_end(vl);
}

int t_printf(const char *s, ...)
{
  va_list vl;

  va_start(vl, s);
  vprintf_uart(s, vl);
  va_end(vl);

  return 0;
}


void vApplicationMallocFailedHook( void );
void vApplicationMallocFailedHook( void )
{
  printf_uart("ERROR: Out of memory\n");
  taskDISABLE_INTERRUPTS();
  for( ;; );
}

void vApplicationStackOverflowHook( TaskHandle_t pxTask, char *pcTaskName );
void vApplicationStackOverflowHook( TaskHandle_t pxTask, char *pcTaskName )
{
  ( void ) pcTaskName;
  ( void ) pxTask;
  printf_uart("ERROR: Stack Overflow\n");
  taskDISABLE_INTERRUPTS();
  for( ;; );
}

void vApplicationTickHook( void );
void vApplicationTickHook( void ) { }
void vApplicationIdleHook( void );
void vApplicationIdleHook( void ) { }
