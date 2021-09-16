#!/bin/bash

del policy
commit

INTERFACE=$1

. ./policer-tc-test1 $INTERFACE
. ./policer-tc-test2 $INTERFACE
. ./policer-tc-test3 $INTERFACE
echo "All policer tc tests passed."
