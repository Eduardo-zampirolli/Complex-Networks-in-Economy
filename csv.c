#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "csv_utils.h"

// Count lines in the file
static int count_lines(const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (!fp) return -1;
    int lines = 0; char buf[4096];
    while (fgets(buf, sizeof(buf), fp)) lines++;
    fclose(fp);
    return lines;
}

// Read a square matrix CSV (no header, comma-separated, n x n)
double **read_csv_matrix(const char *filename, int *n_out) {
    int n = count_lines(filename);
    if (n <= 0) return NULL;
    double **matrix = malloc(n * sizeof(double*));
    for (int i = 0; i < n; i++) matrix[i] = malloc(n * sizeof(double));

    FILE *fp = fopen(filename, "r");
    if (!fp) return NULL;

    char line[65536];
    for (int i = 0; i < n; i++) {
        if (!fgets(line, sizeof(line), fp)) break;
        char *ptr = strtok(line, ",\n");
        for (int j = 0; j < n && ptr; j++) {
            matrix[i][j] = atof(ptr);
            ptr = strtok(NULL, ",\n");
        }
    }
    fclose(fp);
    if (n_out) *n_out = n;
    return matrix;
}
