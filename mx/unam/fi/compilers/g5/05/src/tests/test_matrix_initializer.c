int main() {
    int m[2][2] = {{1, 2}, {3, 4}};
    int total = m[0][0] + m[0][1] + m[1][0] + m[1][1];

    printf("matrix_total=%d", total);
    print(total);

    return total;
}
