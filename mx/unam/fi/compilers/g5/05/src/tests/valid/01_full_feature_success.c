int square(int x) {
    return x * x;
}

int clamp(int value, int low, int high) {
    if (value < low) {
        return low;
    } else {
        if (value > high) {
            return high;
        } else {
            return value;
        }
    }
}

int mix(int a, int b, int c) {
    int temp = ((a + b * c) - (a % 3) + 12) / 2;
    return temp;
}

int main() {
    int a = 7;
    int b = 3;
    int nums[4] = {1, 2, 3, 4};
    int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};

    int total = square(a) + clamp(matrix[1][2], 0, 10) + mix(a, b, nums[1]);
    int i = 0;
    int acc = 0;

    while (i < 6) {
        i = i + 1;
        if (i == 2) {
            continue;
        }
        if (i > 4) {
            break;
        }
        acc = acc + i;
    }

    for (int j = 0; j < 5; j++) {
        if (j == 1) {
            continue;
        }
        acc = acc + j;
    }

    switch (a % 3) {
        case 0: {
            acc = acc + 100;
            break;
        }
        case 1: {
            acc = acc + nums[2];
            break;
        }
        case 2: {
            acc = acc + matrix[0][1];
            break;
        }
        default: {
            acc = acc + 999;
        }
    }

    bool flag = (acc > 0) && !(a == b) || false;
    char letter = 'A';

    printf("acc=%d total=%d flag=%b letter=%c", acc, total, flag, letter);
    print(acc + total);
    return acc + total;
}
