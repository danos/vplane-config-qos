#!/bin/bash

INTERFACE=$1

del int data $INTERFACE firewall
del security firewall
commit

# Test 1 - make sure rproc is correctly formatted for firewall
# with no mark
set security firewall name fw rule 1 action accept
set security firewall name fw rule 1 police bandwidth 200kbit
set int data $INTERFACE firewall in fw
commit
ret=`run sh firewall | grep "policer(0,25000,100,drop,,0,20)" | wc -l`
if [ $ret -ne 1 ]; then
   echo "Firewall test 1 failed"
   exit 1;
fi

echo "Firewall test 1 passed"

# Test 2 - make sure rproc is correctly formatted for firewall
# with pcp mark
set security firewall name fw rule 1 police then mark pcp 5
commit
ret=`run sh firewall | grep "policer(0,25000,100,markpcp,5,0,20,none)" | wc -l`
if [ $ret -ne 1 ]; then
   echo "Firewall test 2 failed"
   exit 1;
fi

echo "Firewall test 2 passed"

# Test 3 - make sure rproc is correctly formatted for firewall
# with dscp mark
set security firewall name fw rule 1 police then mark dscp ef
commit
ret=`run sh firewall | grep "policer(0,25000,100,markdscp,46,0,20)" | wc -l`
if [ $ret -ne 1 ]; then
   echo "Firewall test 3 failed"
   exit 1;
fi

echo "Firewall test 3 passed"

echo "All Firewall tests passed"

del security firewall
del int data $INTERFACE firewall
commit
