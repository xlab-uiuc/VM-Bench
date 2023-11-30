#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>

static void enable_perf(int perf_ctl_fd, int perf_ack_fd)
{
    char ack[5];
    if (perf_ctl_fd != -1)
    {
        ssize_t bytes_written = write(perf_ctl_fd, "enable\n", 8);
        assert(bytes_written == 8);
    }
    if (perf_ack_fd != -1)
    {
        ssize_t bytes_read = read(perf_ack_fd, ack, 5);
        assert(bytes_read == 5 && strcmp(ack, "ack\n") == 0);
    }
    __asm__ volatile("xchgq %r10, %r10");
}

static void disable_perf(int perf_ctl_fd, int perf_ack_fd)
{
    char ack[5];
    __asm__ volatile("xchgq %r11, %r11");
    if (perf_ctl_fd != -1)
    {
        ssize_t bytes_written = write(perf_ctl_fd, "disable\n", 9);
        assert(bytes_written == 9);
    }

    if (perf_ack_fd != -1)
    {
        ssize_t bytes_read = read(perf_ack_fd, ack, 5);
        assert(bytes_read == 5 && strcmp(ack, "ack\n") == 0);
    }
}

int main()
{
    void * addr_start = (void *) 0x400000000001;
    size_t len = (1ULL << 20); /* 1GB */
    uint32_t step = 0x1000;

    int perf_ctl_fd = -1;
    int perf_ack_fd = -1;

    volatile uint8_t *a = mmap(addr_start, len, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);

    if (a == MAP_FAILED) {
        perror("mmap failed");
        return 1;
    }
    uint64_t sum = 0;
    printf("n mem refs =%lx\n", len / step);
    printf("a at %llx\n", (unsigned long long) a);
    for (int i = 0; i < len ; i += step) {
        a[i] = 0;
    }
    
    enable_perf(perf_ack_fd, perf_ack_fd);

    for (int i = 0; i < len ; i += step) {
        uint32_t* p = (uint32_t*) &a[i];
        *p = 64;
        sum += a[i];
    }
    disable_perf(perf_ack_fd, perf_ack_fd);

    printf("sum=%lx\n", sum);
    return 0;
}
