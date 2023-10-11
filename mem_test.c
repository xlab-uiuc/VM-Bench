#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <sys/mman.h>

int main()
{
    void * addr_start = (void *) 0x400000000001;
    size_t len = (1ULL << 30); /* 1GB */
    uint32_t step = 0x1000;
    
    volatile uint8_t *a = mmap(addr_start, len, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);

    if (a == MAP_FAILED) {
        perror("mmap failed");
        return 1;
    }
    uint64_t sum = 0;
    printf("n mem refs =%lx\n", len / step);
    printf("a at %llx\n", (unsigned long long) a);
    for (int i = 0; i < len ; i += step) {
        a[i + 5] = 5;
        a[i] = 0;
    }

    for (int i = 0; i < len ; i += step) {
        a[i + 128] = 64;
    }
    
    for (int j = 0; j < 1000; j++) {
        for (int i = 0; i < len - step ; i += step) {
            // sum += a[i] * a[i + step];
            sum += a[i] + a[i + step + 5];
        }
    }

    printf("sum=%lx\n", sum);
    return 0;
}
