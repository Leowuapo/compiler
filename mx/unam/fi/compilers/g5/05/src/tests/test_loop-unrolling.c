int BasicLoopUnrolling() {
    int total = 0;

    for (int i = 0; i < 3; i++) {
        total = total + i;
    }

    return total;
}

int LargeLoopUnrolling() {
    int total = 0;

    for (int i = 0; i < 20; i++) {
        total = total + i;
    }

    return total;
}

int LoopWithContinue() {
    int total = 0;

    for (int i = 0; i < 3; i++) {
        if (i == 1) {
            continue;
        }

        total = total + i;
    }

    return total;
}