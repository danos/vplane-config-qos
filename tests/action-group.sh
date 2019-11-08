#!/bin/bash

del policy
commit

INTERFACE=$1

# Test 1
# Make sure an action-group can't be configured in a policy if
# it doesn't exist
set policy qos name foo shaper class 1 match 1 action-group fred
set policy qos name foo shaper class 1 profile prof
set policy qos name foo shaper default prof
set policy qos name foo shaper profile prof bandwidth 1Gbit
if ( `commit` ); then
  echo "Test 1 failed, invalid config accepted"
  exit 1;
else
  echo "Test 1 passed"
fi

# Test 2
# Make sure a policer can't be configured in the same match as an
# as in an action-group
set policy action name fred police rate 100
set policy qos name foo shaper class 1 match 1 police rate 200
if ( `commit` ); then
  echo "Test 2 failed, allowed policer in match and action-group"
  exit 1;
else
  echo "Test 2 passed"
fi
del policy qos name foo shaper class 1 match 1 police rate 200

# Test 3
# Make sure mark can't be configured in a match and an action-group
set policy qos name foo shaper class 1 match 1 mark dscp ef
set policy action name fred mark dscp ef
if ( `commit` ); then
  echo "Test 3 failed, allowed mark in match and action-group"
  exit 1;
else
  echo "Test 3 passed"
fi

del policy 
commit

. ./ag-test4 $INTERFACE
. ./ag-test5 $INTERFACE
. ./ag-test6 $INTERFACE
. ./ag-test7 $INTERFACE
