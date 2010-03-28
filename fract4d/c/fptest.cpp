#include <stdio.h>

#include "fenv.h"

int 
main(int argc, char **argv)
{

    //int x = _FPU_DEFAULT & ~(_FPU_MASK_ZM | _FPU_MASK_IM);
    //_FPU_SETCW(x);

    int result = fedisableexcept(FE_ALL_EXCEPT);
    printf("%d\n", result);

    int i = -1 / 0;
}
