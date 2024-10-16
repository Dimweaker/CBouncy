static int g1 = 1;
int g2 = 2, g3[1];

struct a{
    int a1;
    int a2;
};

typedef int myint;

int func(int p1);

int main() {
    volatile int* l1 = &g1;
    int *const*l2 = &l1;
    (**l2)++;
    if (g1=1) {
        int if1;
    }
    else {
        int else1;
    }
    for (int i=0; i;) {
        int for1;
    }
}

int func(int p1) {
    label1:
    goto label1;
    return 1;
}