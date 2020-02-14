#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the bandwidth.py module.
"""

from vyatta_policy_qos_vci.bandwidth import Bandwidth

PARENT_DATA = [
    {"bandwidth": "10Gbit", "burst": "9000"},
    {"bandwidth": "1Gbit", "burst": "9000"},
    {"bandwidth": "1Gbit", "burst": "1ms"},
    {"bandwidth": "10Gbit", "burst": "600msec"},
    {"bandwidth": "0.1Gbit", "burst": "1500"},
    {"bandwidth": "100%", "burst": "1500"}
]
PARENT_BANDWIDTHS = [
    1250000000,
    125000000,
    125000000,
    1250000000,
    12500000,
    0
]
PARENT_COMMANDS = [
    " rate 1250000000 size 9000 period 10",
    " rate 125000000 size 9000 period 10",
    " rate 125000000 msec 1 period 10",
    " rate 1250000000 msec 600 period 10",
    " rate 12500000 size 1500 period 10",
    " percent 100 size 1500 period 10",
    " rate 2500000 size 9000 period 20",
]
CHILD_DATA = [
    {"bandwidth": "50%", "burst": "6000"},
    {"bandwidth": "10%", "burst": "1000"},
    {"bandwidth": "50%", "burst": "60msec"},
    {"bandwidth": "10%", "burst": "10ms"},
    {"bandwidth": "50%", "burst": "2345"},
    {"bandwidth": "10%", "burst": "1500"},
    {"bandwidth": "20%", "burst": "9000"},
]
CHILD_BANDWIDTHS = [
    (1250000000 / 2),
    (125000000 / 10),
    (125000000 / 2),
    (1250000000 / 10),
    (12500000 / 2),
    0,
    (2500000 / 5),
]
CHILD_COMMANDS = [
    " percent 50 size 6000",
    " percent 10 size 1000",
    " percent 50 msec 60",
    " percent 10 msec 10",
    " percent 50 size 2345",
    " percent 10 size 1500",
    " percent 20 size 9000"
]

def test_bandwidth():
    """ Unit-test the bandwidth class """

    for index, parent_input in enumerate(PARENT_DATA):
        parent_bandwidth = PARENT_BANDWIDTHS[index]
        parent_command = PARENT_COMMANDS[index]
        parent_bw = Bandwidth(parent_input, None)
        assert parent_bw is not None
        assert parent_bw.bps == parent_bandwidth
        assert parent_bw.commands("", 10) == parent_command

        child_input = CHILD_DATA[index]
        child_bandwidth = CHILD_BANDWIDTHS[index]
        child_command = CHILD_COMMANDS[index]
        child_bw = Bandwidth(child_input, parent_bw)
        assert child_bw is not None
        assert child_bw.bps == child_bandwidth
        assert child_bw.commands("", None) == child_command
