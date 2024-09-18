int main ()
{
    int g=0;
    int l1[1];
    int *l2 = &g;
    int i;
    for (i=0; i<1; i++)
        l1[i] = 1;
    for (g=0; g; ++g)
    {
        int *l3[1] = {&l1[0]};
    }
    *l2 = *l1;
b:
    for (i=0; i<2; ++i)
    { 
        if (i)
            goto b;
        if (g)
            continue;
    }
    return 0;
}