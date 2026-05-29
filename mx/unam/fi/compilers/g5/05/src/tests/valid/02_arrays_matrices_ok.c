int main() {
    int vector[5] = {2, 4, 6, 8, 10};
    int grid[2][2] = {{1, 3}, {5, 7}};

    vector[3] = vector[0] + grid[1][1] * 2;
    grid[0][1] = vector[3] - grid[1][0];

    int result = vector[3] + grid[0][1] + grid[1][0];
    printf("array-matrix=%d", result);
    return result;
}
