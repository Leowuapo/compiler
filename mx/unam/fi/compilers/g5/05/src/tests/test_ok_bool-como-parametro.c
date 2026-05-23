int elegir(bool activo, int a, int b) {
    if (activo) {
        return a;
    }

    return b;
}

int main() {
    int x = elegir(true, 10, 20);
    return x;
}