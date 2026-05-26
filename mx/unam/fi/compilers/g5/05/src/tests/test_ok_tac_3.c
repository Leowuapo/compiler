int suma(int a, int b) {
    return a + b;
}

int abs_val(int x) {
    if (x < 0) {
        return -x;
    } else {
        return x;
    }
}

bool es_mayor(int a, int b) {
    return a > b;
}

int procesar_array(int base) {
    int arr[4] = {1, 2, 3, 4};
    int total = 0;

    for (int i = 0; i < 4; i++) {
        arr[i] = arr[i] + base;
        total = total + arr[i];

        if (total > 20) {
            break;
        }
    }

    return total;
}

int procesar_matriz() {
    int m[2][2];

    m[0][0] = 1;
    m[0][1] = 2;
    m[1][0] = 3;
    m[1][1] = 4;

    return m[0][0] + m[1][1];
}

void imprimir_valores(int x, int y, bool flag) {
    printf("x=%d y=%d flag=%b", x, y, flag);
    print(x + y);
}

int main() {
    int a = 10;
    int b = -3;
    int c = suma(a, abs_val(b));
    int d = procesar_array(c);
    int e = procesar_matriz();

    bool flag = es_mayor(d, e) && !(c == 0);

    imprimir_valores(d, e, flag);

    while (a > 0) {
        a = a - 1;

        if (a % 2 == 0) {
            continue;
        }

        if (a < 3) {
            break;
        }

        print(a);
    }

    switch (c) {
        case 1: {
            printf("case uno");
            break;
        }

        case 13: {
            printf("case trece");
            break;
        }

        default: {
            printf("case default");
            break;
        }
    }

    for (int i = 0; i < 3; i++) {
        int temp = +(i * 2) + -1;
        printf("temp=%d", temp);
    }

    return d + e;
}