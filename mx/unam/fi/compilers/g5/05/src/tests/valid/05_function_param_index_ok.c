int pick(int index) {
    int data[3] = {8, 13, 21};
    return data[index];
}

int main() {
    int selected = pick(1);
    print(selected);
    return selected;
}
