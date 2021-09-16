#!/bin/bash

INTERFACE=$1

. ./po-firewall-tests.sh $INTERFACE
. ./po-ag-tests.sh $INTERFACE
. ./po-policy-tests.sh $INTERFACE
. ./action-group.sh $INTERFACE
. ./policer-tc.sh $INTERFACE
