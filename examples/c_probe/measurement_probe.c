/*
 * Tiny C-side measurement producer example.
 * Compile: gcc -O2 measurement_probe.c -o measurement_probe
 * Run:     ./measurement_probe > c_probe_measurements.csv
 *
 * The point is interoperability: embedded/C code emits measurements that the
 * Python validation pipeline can ingest unchanged.
 */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double rand01(void) { return (double)rand() / (double)RAND_MAX; }

int main(void) {
    srand(42);
    puts("run_id,timestamp,bench,device,test_name,signal,value,lower_bound,upper_bound,duration_ms,temperature_c,supply_v");
    for (int i = 0; i < 24; ++i) {
        double temp = (i % 3 == 0) ? 85.0 : 25.0;
        double supply = (i % 4 == 0) ? 3.0 : 3.3;
        double value = 3.30 + (temp - 25.0) * 0.0003 + (supply - 3.3) * 0.04 + (rand01() - 0.5) * 0.035;
        printf("C%03d,2026-01-01T%02d:00:00Z,c-bench,dut-c,adc_reference,vref,%.6f,3.20,3.40,%.3f,%.1f,%.1f\n",
               i, i % 24, value, 10.0 + rand01() * 4.0, temp, supply);
    }
    return 0;
}
