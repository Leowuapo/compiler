int x = 1;
int y = 4;

switch (x) {
    case 1: {
        break;
    }

    case 2: {
        break;
    }

    case 3: {
        break;
    }

    case 4: {
        break;
    }

    case 5: {
        if (x > 0) {
            y = 3;
        }
        break;
    }

    default: {
        int y = 2;
    }
}