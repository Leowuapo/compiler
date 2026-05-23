int x = 0;

while (x < 10) {
    switch (x) {
        case 1: {
            continue;
        }

        default: {
            x = x + 1;
        }
    }

    x = x + 1;
}