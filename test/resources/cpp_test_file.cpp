#include <iostream>

struct my_struct {
    int bla;
    char *stuff;
};


struct my_struct do_stuff(int my_arg, char *second_arg)
{
    int my_local = my_arg + 2;
    int i;

    for (i = 0; i < my_local; ++i)
        std::cout << "i = " << i << std::endl;

    struct my_struct a = {.bla=5, .stuff="5"};
    return a;
}


int main()
{
    do_stuff(2, "yay!");
    return 0;
}