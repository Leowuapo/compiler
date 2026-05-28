int main() {
    int x = ((2 + 3) * (4 - 1)) + (10 / 2) - (9 % 4);
    int y = x * 1 + 0;
    bool keep = (y > 10) && true;

    if (keep) {
        print(y);
    } else {
        print(0);
    }

    return y;
}
