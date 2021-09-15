#!/bin/bash

INTERFACE=$1

del policy qos
del int data $INTERFACE policy
commit

# Test 1 - Make sure a standard police config is accepted
set policy qos name foo shaper class 1 match 1 police rate 100
set policy qos name foo shaper class 1 profile prof
set policy qos name foo shaper def prof
set policy qos name foo shaper profile prof bandwidth 1Gbit
set int data $INTERFACE policy qos foo
commit
ret=`run sh queuing $INTERFACE class | grep "policer(100,0,0,drop,,0,1000)" | wc -l`
if [ $ret -ne 1 ]; then
   echo "Policy test 1 failed";
   exit 1;
fi

echo "Policy test 1 passed";

# Test 2 - Make sure a standard police config is accepted
del policy qos name foo shaper class 1 match 1 police rate
set policy qos name foo shaper class 1 match 1 police bandwidth 200kbit
commit
ret=`run sh queuing $INTERFACE class | grep "policer(0,25000,100,drop,,0,20)" | wc -l`
if [ $ret -ne 1 ]; then
   echo "Policy test 2 failed";
   exit 1;
fi

echo "Policy test 2 passed";

# Test 3 - Check that overhead can be inherited correctly
set policy qos name foo shaper class 1 match 1 police frame-overhead inherit
commit
ret=`run sh queuing $INTERFACE class | grep "policer(0,25000,100,drop,,inherit,20)" | wc -l`
if [ $ret -ne 1 ]; then
   echo "Policy test 3 failed";
   exit 1;
fi

echo "Policy test 3 passed";

# Test 4 - Check that overhead can be inherited correctly
set policy qos name foo shaper class 1 match 1 police frame-overhead 200
commit
ret=`run sh queuing $INTERFACE class | grep "policer(0,25000,100,drop,,200,20)" | wc -l`
if [ $ret -ne 1 ]; then
   echo "Policy test 4 failed";
   exit 1;
fi

echo "Policy test 4 passed";

# Test 5 - Check that overhead can be inherited correctly with marking pcp
set policy qos name foo shaper class 1 match 1 police then mark pcp 5
commit
ret=`run sh queuing $INTERFACE class | grep "policer(0,25000,100,markpcp,5,200,20,none)" | wc -l`
if [ $ret -ne 1 ]; then
   echo "Policy test 5 failed";
   exit 1;
fi

echo "Policy test 5 passed";

# Test 6 - Check that overhead can be inherited correctly with marking dscp
del policy qos name foo shaper class 1 match 1 police then mark pcp
set policy qos name foo shaper class 1 match 1 police then mark dscp ef
commit
ret=`run sh queuing $INTERFACE class | grep "policer(0,25000,100,markdscp,46,200,20)" | wc -l`
if [ $ret -ne 1 ]; then
   echo "Policy test 6 failed";
   exit 1;
fi

echo "Policy test 6 passed";

echo "All Policy police overhead tests passed";

del policy qos
del int data $INTERFACE policy
commit
