#ifndef ISP_UTILS_H
#define ISP_UTILS_H

#include <stdint.h>

int t_printf(const char *s, ...);
int isp_main(void);
uint32_t isp_get_time_usec(void);

#endif // ISP_UTILS_H
