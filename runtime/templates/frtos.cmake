cmake_minimum_required(VERSION 3.5) # or other version

set(USE_CLANG 1)

if (DEFINED ENV{ISP_PREFIX})
  set(ISP_PREFIX $ENV{ISP_PREFIX})
else()
  set(ISP_PREFIX "/opt/isp/")
endif()

if (DEFINED ENV{FREE_RTOS_DIR})
  set(FREE_RTOS_DIR $ENV{FREE_RTOS_DIR})
else()
  set(FREE_RTOS_DIR "${ISP_PREFIX}/FreeRTOS")
endif()

if (NOT DEFINED CMAKE_TOOLCHAIN_FILE)
   set(CMAKE_TOOLCHAIN_FILE "${FREE_RTOS_DIR}/Demo/RISCV_DOVER_GCC/riscv.cmake")
 endif()

if (NOT DEFINED CMAKE_BUILD_TYPE)
   set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

project (FreeRTOS C ASM)

set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -T ${FREE_RTOS_DIR}/Demo/RISCV_DOVER_GCC/soc/link.ld -nostartfiles")

set(WARNINGS "-Wall -Wextra -Wshadow -Wpointer-arith -Wbad-function-cast -Wcast-align -Wsign-compare")
set(WARNINGS "${WARNINGS} -Waggregate-return -Wstrict-prototypes -Wmissing-prototypes -Wmissing-declarations -Wunused")

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -D__gracefulExit ${WARNINGS} -Os -DNDEBUG -g")
#set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -D__gracefulExit ${WARNINGS}")

include_directories("${DOVER_SOURCES}/isp-headers")
include_directories("${FREE_RTOS_DIR}/Source/include")
include_directories("${FREE_RTOS_DIR}/Source/portable/GCC/RISCV")
include_directories("${FREE_RTOS_DIR}/Demo/RISCV_DOVER_GCC/arch")
include_directories("${FREE_RTOS_DIR}/Demo/RISCV_DOVER_GCC/conf")
include_directories("${FREE_RTOS_DIR}/Demo/RISCV_DOVER_GCC/soc/include")

add_library(free-rtos ${FREE_RTOS_DIR}/Source/tasks.c
		      ${FREE_RTOS_DIR}/Source/croutine.c
		      ${FREE_RTOS_DIR}/Source/queue.c
		      ${FREE_RTOS_DIR}/Source/timers.c
		      ${FREE_RTOS_DIR}/Source/event_groups.c
		      ${FREE_RTOS_DIR}/Source/list.c
		      ${FREE_RTOS_DIR}/Source/portable/MemMang/dover_heap_2.c
		      ${FREE_RTOS_DIR}/Source/portable/GCC/RISCV/port.c
		      ${FREE_RTOS_DIR}/Source/portable/GCC/RISCV/portasm.S
		      ${FREE_RTOS_DIR}/Demo/RISCV_DOVER_GCC/arch/syscall.c
		      ${FREE_RTOS_DIR}/Demo/RISCV_DOVER_GCC/arch/utils.c
		      ${FREE_RTOS_DIR}/Demo/RISCV_DOVER_GCC/arch/boot.S)

add_library(free-rtos-dover
  ${FREE_RTOS_DIR}/Demo/RISCV_DOVER_GCC/soc/src/ns16550.c
  ${FREE_RTOS_DIR}/Demo/RISCV_DOVER_GCC/arch/utils.c)
