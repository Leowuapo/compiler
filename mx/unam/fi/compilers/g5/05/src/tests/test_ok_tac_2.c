int suma(int a, int b) {
    return a + b;
}

int cuadrado(int x) {
    return x * x;
}

int elegir(bool flag, int a, int b) {
    if (flag) {
        return a;
    } else {
        return b;
    }
}

void imprimir_numero(int x) {
    printf("numero=%d", x);
}

int main() {
    int x = 2 + 3 * 4;
    int y = cuadrado(x);
    int z = suma(x, y);

    int arr[4] = {1, 2, 3, 4};
    int m[2][2];

    m[0][0] = arr[0] + z;
    m[0][1] = arr[1] * 2;
    m[1][0] = arr[2] + arr[3];
    m[1][1] = m[0][0] - m[0][1];

    if (z > 20 && y != 0) {
        print(z);
        imprimir_numero(m[1][1]);
    } else {
        print(0);
    }

    int total = 0;

    for (int i = 0; i < 4; i++) {
        total = total + arr[i];

        if (i == 2) {
            continue;
        }

        if (total > 20) {
            break;
        }
    }

    int j = 0;

    while (j < 3) {
        total = total + j;

        switch (j) {
            case 0: {
                printf("case=%d", j);
                break;
            }

            case 1: {
                total = total + 10;
                break;
            }

            default: {
                total = total + 100;
                break;
            }
        }

        j = j + 1;
    }

    bool flag = total > 10 || x < y;
    int seleccionado = elegir(flag, total, z);

    printf("resultado=%d", seleccionado);

    return seleccionado;
}