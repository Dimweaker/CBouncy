static int g1 = 1;
int g2 = 2, g3[1];

typedef int myint;

int func(int p1);

int main() {
    const volatile int* const * l1 = &g1;
    int ***l2 = &l1;
    if (g1=1) {
        int if1;
    }
    else {
        int else1;
    }
    for (int i=0; ;) {
        int for1;
    }
}

int func(int p1) {
    return 1;
}