#!/bin/bash

INTERFACE=$1

. ./perQwred-test1 $INTERFACE
if [ $? -ne 0 ]; then
    return 1;
fi

. ./perQwred-test2 $INTERFACE
if [ $? -ne 0 ]; then
    return 1;
fi

. ./perQwred-test3 $INTERFACE
if [ $? -ne 0 ]; then
    return 1;
fi

. ./perQwred-test4 $INTERFACE
if [ $? -ne 0 ]; then
    return 1;
fi

. ./perQwred-test5 $INTERFACE
if [ $? -ne 0 ]; then
    return 1;
fi

. ./perQwred-test6 $INTERFACE
if [ $? -ne 0 ]; then
    return 1;
fi

return 0;
