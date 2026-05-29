int sum(int a, int b) {
    return a + b;
}

int square(int x) {
    return x * x;
}

int clamp_score(int score) {
    if (score > 100) {
        return 100;
    } else {
        if (score < 0) {
            return 0;
        } else {
            return score;
        }
    }
}

bool is_passing(int score) {
    return score >= 70 && score <= 100;
}

int bonus_by_level(int level) {
    int bonus = 0;

    switch (level) {
        case 1: {
            bonus = 5;
            break;
        }
        case 2: {
            bonus = 10;
            break;
        }
        case 3: {
            bonus = 20;
            break;
        }
        default: {
            bonus = 1;
            break;
        }
    }

    return bonus;
}

int main() {
    int base = sum(30, 40);
    int power = square(3);
    int level = 3;
    int bonus = bonus_by_level(level);

    int scores[4] = {65, 72, 88, 91};
    int matrix[2][2];

    matrix[0][0] = scores[0] + bonus;
    matrix[0][1] = scores[1] + bonus;
    matrix[1][0] = scores[2] + bonus;
    matrix[1][1] = scores[3] + bonus;

    int total = 0;

    for (int i = 0; i < 4; i++) {
        if (i == 1) {
            continue;
        }

        total = total + scores[i];
    }

    int row = 0;
    int matrix_total = 0;

    while (row < 2) {
        int col = 0;

        while (col < 2) {
            matrix_total = matrix_total + matrix[row][col];
            col = col + 1;
        }

        row = row + 1;
    }

    int raw_score = base + power + bonus;
    int final_score = clamp_score(raw_score);
    bool passed = is_passing(final_score);

    printf("base=%d power=%d bonus=%d", base, power, bonus);
    printf("raw=%d final=%d", raw_score, final_score);
    printf("array_total=%d matrix_total=%d", total, matrix_total);

    if (passed) {
        printf("status=%s", "PASSED");
    } else {
        printf("status=%s", "FAILED");
    }

    print(final_score);

    return final_score;
}