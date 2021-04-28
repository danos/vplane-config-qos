#!/usr/bin/env python3

# Copyright (c) 2019-2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the profile.py module.
"""

from unittest.mock import Mock

import pytest

from vyatta_policy_qos_vci.bandwidth import Bandwidth
from vyatta_policy_qos_vci.profile import Profile

TEST_DATA = [
    (
        # A default profile without any parameter modifications
        # test_input
        {
            "burst": "16000",
            "id": "profile-1"
        },
        # expected_result
        [
            "qos lo profile 0 percent 100 size 16000 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4"
        ]
    ),
    (
        # A simple profile with minor parameter modifications
        # test_input
        {
            "bandwidth": "1Gbit",
            "burst": "10000",
            "id": "profile-1",
            "period": 50
        },
        # expected_result
        [
            "qos lo profile 0 rate 125000000 size 10000 period 50000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4"
        ]
    ),
    (
        # A simple profile with millisecond burst size
        # test_input
        {
            "bandwidth": "1Gbit",
            "burst": "10msec",
            "id": "profile-1",
            "period": 50
        },
        # expected_result
        [
            "qos lo profile 0 rate 125000000 msec 10 period 50000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4"
        ]
    ),
    (
        # Throw in some traffic-class percentage bandwidth restrictions
        # test_input
        {
            "bandwidth": "1Gbit",
            "burst": "10000",
            "id": "profile-1",
            "period": 50,
            "traffic-class": [
                {"bandwidth": "10%", "id": 0},
                {"bandwidth": "20%", "id": 1},
                {"bandwidth": "30%", "id": 2},
                {"bandwidth": "40%", "id": 3}
            ]
        },
        # expected_result
        [
            "qos lo profile 0 rate 125000000 size 10000 period 50000",
            "qos lo profile 0 queue 0 percent 10 msec 4",
            "qos lo profile 0 queue 1 percent 20 msec 4",
            "qos lo profile 0 queue 2 percent 30 msec 4",
            "qos lo profile 0 queue 3 percent 40 msec 4"
        ]
    ),
    (
        # Change traffic-class absolute bandwidths
        # test_input
        {
            "bandwidth": "1Gbit",
            "burst": "10000",
            "id": "profile-1",
            "period": 50,
            "traffic-class": [
                {"bandwidth": "1Gbit", "id": 0},
                {"bandwidth": "2Gbit", "id": 1},
                {"bandwidth": "3Gbit", "id": 2},
                {"bandwidth": "4Gbit", "id": 3}
            ]
        },
        # expected_result
        [
            "qos lo profile 0 rate 125000000 size 10000 period 50000",
            "qos lo profile 0 queue 0 rate 125000000 msec 4",
            "qos lo profile 0 queue 1 rate 250000000 msec 4",
            "qos lo profile 0 queue 2 rate 375000000 msec 4",
            "qos lo profile 0 queue 3 rate 500000000 msec 4"
        ]
    ),
    (
        # Add a dscp-group map to queue 0, and queue 0 to traffic-class 1
        # test_input
        {
            "bandwidth": "1Gbit",
            "burst": "10000",
            "id": "profile-1",
            "map": {
                "dscp-group": [
                    {"group-name": "real-time-group", "to": 0}
                ]
            },
            "period": 50,
            "queue": [
                {"id": 0, "traffic-class": 1, "weight": 1}
            ],
            "traffic-class": [
                {"bandwidth": "1Gbit", "id": 0},
                {"bandwidth": "2Gbit", "id": 1},
                {"bandwidth": "3Gbit", "id": 2},
                {"bandwidth": "4Gbit", "id": 3}
            ]
        },
        # expected_result
        [
            "qos lo profile 0 rate 125000000 size 10000 period 50000",
            "qos lo profile 0 queue 0 rate 125000000 msec 4",
            "qos lo profile 0 queue 1 rate 250000000 msec 4",
            "qos lo profile 0 queue 2 rate 375000000 msec 4",
            "qos lo profile 0 queue 3 rate 500000000 msec 4",
            "qos lo profile 0 dscp-group real-time-group 0x1",
            "qos lo profile 0 queue 0x1 wrr-weight 1 0"
        ]
    ),
    (
        # Add more dscp-groups and some wrr-weights
        # test_input
        {
            "bandwidth": "1Gbit",
            "burst": "10000",
            "id": "profile-1",
            "map": {
                "dscp-group": [
                    {"group-name": "default-group-high-drop", "to": 5},
                    {"group-name": "default-group-low-drop", "to": 4},
                    {"group-name": "priority-group-high-drop", "to": 3},
                    {"group-name": "priority-group-low-drop", "to": 2},
                    {"group-name": "real-time-group", "to": 0},
                    {"group-name": "synch-group", "to": 1}
                ]
            },
            "period": 50,
            "queue": [
                {"id": 0, "traffic-class": 1, "weight": 1},
                {"id": 1, "traffic-class": 0, "weight": 1},
                {"id": 2, "traffic-class": 2, "weight": 80},
                {"id": 3, "traffic-class": 2, "weight": 20},
                {"id": 4, "traffic-class": 3, "weight": 70},
                {"id": 5, "traffic-class": 3, "weight": 30}
            ],
            "traffic-class": [
                {"bandwidth": "1Gbit", "id": 0},
                {"bandwidth": "2Gbit", "id": 1},
                {"bandwidth": "3Gbit", "id": 2},
                {"bandwidth": "4Gbit", "id": 3}
            ]
        },
        # expected_result
        [
            "qos lo profile 0 rate 125000000 size 10000 period 50000",
            "qos lo profile 0 queue 0 rate 125000000 msec 4",
            "qos lo profile 0 queue 1 rate 250000000 msec 4",
            "qos lo profile 0 queue 2 rate 375000000 msec 4",
            "qos lo profile 0 queue 3 rate 500000000 msec 4",
            "qos lo profile 0 dscp-group default-group-high-drop 0x7",
            "qos lo profile 0 dscp-group default-group-low-drop 0x3",
            "qos lo profile 0 dscp-group priority-group-high-drop 0x6",
            "qos lo profile 0 dscp-group priority-group-low-drop 0x2",
            "qos lo profile 0 dscp-group real-time-group 0x1",
            "qos lo profile 0 dscp-group synch-group 0x0",
            "qos lo profile 0 queue 0x1 wrr-weight 1 0",
            "qos lo profile 0 queue 0 wrr-weight 1 1",
            "qos lo profile 0 queue 0x2 wrr-weight 80 2",
            "qos lo profile 0 queue 0x6 wrr-weight 20 3",
            "qos lo profile 0 queue 0x3 wrr-weight 70 4",
            "qos lo profile 0 queue 0x7 wrr-weight 30 5"
        ]
    ),
    (
        # Repeat previous configuration using a dscp map
        # test_input
        {
            "bandwidth": "1Gbit",
            "id": "profile-1",
            "map": {
                "dscp": [
                    {"id": "0,1,2,3,4,5,6,7,9,11,12,13,14,15,17,19,20,21," \
                     "22,23,41,42,43,44,45,49, 50,51,52,53,54,55,57," \
                     "58,59,60,61,62,63", "to": 4},
                    {"id": "8,10,16,18", "to": 5},
                    {"id": "24,26,32,34", "to": 3},
                    {"id": "25,27,28,29,30,31,33,35,36,37,38,39", "to": 2},
                    {"id": "40,46,47,48", "to": 1},
                    {"id": "56", "to": 0}
                ]
            },
            "queue": [
                {"id": 0, "traffic-class": 0, "weight": 1},
                {"id": 1, "traffic-class": 1, "weight": 1},
                {"id": 2, "traffic-class": 2, "weight": 80},
                {"id": 3, "traffic-class": 2, "weight": 20},
                {"id": 4, "traffic-class": 3, "weight": 70},
                {"id": 5, "traffic-class": 3, "weight": 30}
            ]
        },
        # expected_result
        [
            "qos lo profile 0 rate 125000000 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo profile 0 dscp 0 0x3",
            "qos lo profile 0 dscp 1 0x3",
            "qos lo profile 0 dscp 2 0x3",
            "qos lo profile 0 dscp 3 0x3",
            "qos lo profile 0 dscp 4 0x3",
            "qos lo profile 0 dscp 5 0x3",
            "qos lo profile 0 dscp 6 0x3",
            "qos lo profile 0 dscp 7 0x3",
            "qos lo profile 0 dscp 8 0x7",
            "qos lo profile 0 dscp 9 0x3",
            "qos lo profile 0 dscp 10 0x7",
            "qos lo profile 0 dscp 11 0x3",
            "qos lo profile 0 dscp 12 0x3",
            "qos lo profile 0 dscp 13 0x3",
            "qos lo profile 0 dscp 14 0x3",
            "qos lo profile 0 dscp 15 0x3",
            "qos lo profile 0 dscp 16 0x7",
            "qos lo profile 0 dscp 17 0x3",
            "qos lo profile 0 dscp 18 0x7",
            "qos lo profile 0 dscp 19 0x3",
            "qos lo profile 0 dscp 20 0x3",
            "qos lo profile 0 dscp 21 0x3",
            "qos lo profile 0 dscp 22 0x3",
            "qos lo profile 0 dscp 23 0x3",
            "qos lo profile 0 dscp 24 0x6",
            "qos lo profile 0 dscp 25 0x2",
            "qos lo profile 0 dscp 26 0x6",
            "qos lo profile 0 dscp 27 0x2",
            "qos lo profile 0 dscp 28 0x2",
            "qos lo profile 0 dscp 29 0x2",
            "qos lo profile 0 dscp 30 0x2",
            "qos lo profile 0 dscp 31 0x2",
            "qos lo profile 0 dscp 32 0x6",
            "qos lo profile 0 dscp 33 0x2",
            "qos lo profile 0 dscp 34 0x6",
            "qos lo profile 0 dscp 35 0x2",
            "qos lo profile 0 dscp 36 0x2",
            "qos lo profile 0 dscp 37 0x2",
            "qos lo profile 0 dscp 38 0x2",
            "qos lo profile 0 dscp 39 0x2",
            "qos lo profile 0 dscp 40 0x1",
            "qos lo profile 0 dscp 41 0x3",
            "qos lo profile 0 dscp 42 0x3",
            "qos lo profile 0 dscp 43 0x3",
            "qos lo profile 0 dscp 44 0x3",
            "qos lo profile 0 dscp 45 0x3",
            "qos lo profile 0 dscp 46 0x1",
            "qos lo profile 0 dscp 47 0x1",
            "qos lo profile 0 dscp 48 0x1",
            "qos lo profile 0 dscp 49 0x3",
            "qos lo profile 0 dscp 50 0x3",
            "qos lo profile 0 dscp 51 0x3",
            "qos lo profile 0 dscp 52 0x3",
            "qos lo profile 0 dscp 53 0x3",
            "qos lo profile 0 dscp 54 0x3",
            "qos lo profile 0 dscp 55 0x3",
            "qos lo profile 0 dscp 56 0x0",
            "qos lo profile 0 dscp 57 0x3",
            "qos lo profile 0 dscp 58 0x3",
            "qos lo profile 0 dscp 59 0x3",
            "qos lo profile 0 dscp 60 0x3",
            "qos lo profile 0 dscp 61 0x3",
            "qos lo profile 0 dscp 62 0x3",
            "qos lo profile 0 dscp 63 0x3",
            "qos lo profile 0 queue 0 wrr-weight 1 0",
            "qos lo profile 0 queue 0x1 wrr-weight 1 1",
            "qos lo profile 0 queue 0x2 wrr-weight 80 2",
            "qos lo profile 0 queue 0x6 wrr-weight 20 3",
            "qos lo profile 0 queue 0x3 wrr-weight 70 4",
            "qos lo profile 0 queue 0x7 wrr-weight 30 5"
        ]
    ),
    (
        # A profile with a pcp map
        # test_input
        {
            "bandwidth": "1Gbit",
            "id": "profile-1",
            "map": {
                "pcp": [
                    {"id": 0, "to": 7},
                    {"id": 1, "to": 6},
                    {"id": 2, "to": 5},
                    {"id": 3, "to": 4},
                    {"id": 4, "to": 3},
                    {"id": 5, "to": 2},
                    {"id": 6, "to": 1},
                    {"id": 7, "to": 0}
                ]
            },
            "queue": [
                {"id": 0, "traffic-class": 0, "weight": 1},
                {"id": 1, "traffic-class": 0, "weight": 1},
                {"id": 2, "traffic-class": 1, "weight": 1},
                {"id": 3, "traffic-class": 1, "weight": 1},
                {"id": 4, "traffic-class": 2, "weight": 1},
                {"id": 5, "traffic-class": 2, "weight": 1},
                {"id": 6, "traffic-class": 3, "weight": 1},
                {"id": 7, "traffic-class": 3, "weight": 1}
            ],
            "traffic-class": [
                {"bandwidth": "1Gbit", "id": 0},
                {"bandwidth": "2Gbit", "id": 1},
                {"bandwidth": "3Gbit", "id": 2},
                {"bandwidth": "4Gbit", "id": 3}
            ]
        },
        # expected_result
        [
            "qos lo profile 0 rate 125000000 msec 4 period 10000",
            "qos lo profile 0 queue 0 rate 125000000 msec 4",
            "qos lo profile 0 queue 1 rate 250000000 msec 4",
            "qos lo profile 0 queue 2 rate 375000000 msec 4",
            "qos lo profile 0 queue 3 rate 500000000 msec 4",
            "qos lo profile 0 pcp 0 0x7",
            "qos lo profile 0 pcp 1 0x3",
            "qos lo profile 0 pcp 2 0x6",
            "qos lo profile 0 pcp 3 0x2",
            "qos lo profile 0 pcp 4 0x5",
            "qos lo profile 0 pcp 5 0x1",
            "qos lo profile 0 pcp 6 0x4",
            "qos lo profile 0 pcp 7 0x0",
            "qos lo profile 0 queue 0 wrr-weight 1 0",
            "qos lo profile 0 queue 0x4 wrr-weight 1 1",
            "qos lo profile 0 queue 0x1 wrr-weight 1 2",
            "qos lo profile 0 queue 0x5 wrr-weight 1 3",
            "qos lo profile 0 queue 0x2 wrr-weight 1 4",
            "qos lo profile 0 queue 0x6 wrr-weight 1 5",
            "qos lo profile 0 queue 0x3 wrr-weight 1 6",
            "qos lo profile 0 queue 0x7 wrr-weight 1 7"
        ]
    ),
    (
        # A profile with a dscp-group map and a pipe-queue that has two
        # wred-maps so we have some non-zero drop-precedences
        # test_input
        {
            "bandwidth": "1Gbit",
            "burst": "16000",
            "id": "profile-1",
            "map": {
                "dscp-group": [
                    {"group-name": "default-group-high", "to": 3},
                    {"group-name": "default-group-low", "to": 3},
                    {"group-name": "priority-group-high", "to": 2},
                    {"group-name": "priority-group-low", "to": 2},
                    {"group-name": "real-time-group", "to": 1},
                    {"group-name": "synch-group", "to": 0}
                ]
            },
            "queue": [
                {"id": 0, "traffic-class": 0, "weight": 1},
                {"id": 1, "traffic-class": 1, "weight": 1},
                {
                    "id": 2, "traffic-class": 2, "weight": 1,
                    "wred-map-bytes": {
                        "dscp-group": [
                            {
                                "group-name": "priority-group-high",
                                "mark-probability": 5,
                                "max-threshold": "30000",
                                "min-threshold": "20000"
                            },
                            {
                                "group-name": "priority-group-low",
                                "mark-probability": 10,
                                "max-threshold": "50000",
                                "min-threshold": "40000"
                            }
                        ],
                        "filter-weight": 10
                    }
                },
                {"id": 3, "traffic-class": 2, "weight": 1}
            ]
        },
        # expected_result
        [
            # packets limits generated during unit-test
            "qos lo profile 0 rate 125000000 size 16000 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo profile 0 dscp-group default-group-high 0x6",
            "qos lo profile 0 dscp-group default-group-low 0x26",
            "qos lo profile 0 dscp-group priority-group-high 0x2",
            "qos lo profile 0 dscp-group priority-group-low 0x22",
            "qos lo profile 0 dscp-group real-time-group 0x1",
            "qos lo profile 0 dscp-group synch-group 0x0",
            "qos lo profile 0 queue 0 wrr-weight 1 0",
            "qos lo profile 0 queue 0x1 wrr-weight 1 1",
            "qos lo profile 0 queue 0x2 wrr-weight 1 2",
            "qos lo profile 0 queue 0x2 dscp-group priority-group-high packets 30000 20000 5",
            "qos lo profile 0 queue 0x2 dscp-group priority-group-low packets 50000 40000 10",
            "qos lo profile 0 queue 0x2 wred-weight 10",
            "qos lo profile 0 queue 0x6 wrr-weight 1 3"
        ]
    ),
    (
        # A profile with a to-classifier map - drop-precedence always 0
        # test_input
        {
            "bandwidth": "1Gbit",
            "id": "profile-1",
            "map": {
                "designation": [
                    {"id": 0, "to": 7},
                    {"id": 1, "to": 6},
                    {"id": 2, "to": 5},
                    {"id": 3, "to": 4},
                    {"id": 4, "to": 3},
                    {"id": 5, "to": 2},
                    {"id": 6, "to": 1},
                    {"id": 7, "to": 0}
                ]
            },
            "queue": [
                {"id": 0, "traffic-class": 0, "weight": 1},
                {"id": 1, "traffic-class": 0, "weight": 1},
                {"id": 2, "traffic-class": 1, "weight": 1},
                {"id": 3, "traffic-class": 1, "weight": 1},
                {"id": 4, "traffic-class": 2, "weight": 1},
                {"id": 5, "traffic-class": 2, "weight": 1},
                {"id": 6, "traffic-class": 3, "weight": 1},
                {"id": 7, "traffic-class": 3, "weight": 1}
            ],
            "traffic-class": [
                {"bandwidth": "1Gbit", "id": 0},
                {"bandwidth": "2Gbit", "id": 1},
                {"bandwidth": "3Gbit", "id": 2},
                {"bandwidth": "4Gbit", "id": 3}
            ]
        },
        # expected_result
        [
            "qos lo profile 0 rate 125000000 msec 4 period 10000",
            "qos lo profile 0 queue 0 rate 125000000 msec 4",
            "qos lo profile 0 queue 1 rate 250000000 msec 4",
            "qos lo profile 0 queue 2 rate 375000000 msec 4",
            "qos lo profile 0 queue 3 rate 500000000 msec 4",
            "qos lo profile 0 designation 0 queue 0x7",
            "qos lo profile 0 designation 1 queue 0x3",
            "qos lo profile 0 designation 2 queue 0x6",
            "qos lo profile 0 designation 3 queue 0x2",
            "qos lo profile 0 designation 4 queue 0x5",
            "qos lo profile 0 designation 5 queue 0x1",
            "qos lo profile 0 designation 6 queue 0x4",
            "qos lo profile 0 designation 7 queue 0x0",
            "qos lo profile 0 queue 0 wrr-weight 1 0",
            "qos lo profile 0 queue 0x4 wrr-weight 1 1",
            "qos lo profile 0 queue 0x1 wrr-weight 1 2",
            "qos lo profile 0 queue 0x5 wrr-weight 1 3",
            "qos lo profile 0 queue 0x2 wrr-weight 1 4",
            "qos lo profile 0 queue 0x6 wrr-weight 1 5",
            "qos lo profile 0 queue 0x3 wrr-weight 1 6",
            "qos lo profile 0 queue 0x7 wrr-weight 1 7"
        ]
    ),
    (
        # A profile with a dscp-group map that does have any pipe-queue to
        # traffic-class assignment - the dscp-group map will be ignored
        # test_input
        {
            "bandwidth": "10Gbit",
            "default": "pro-1",
            "frame-overhead": "24",
            "profile": [
                {
                    "id": "pro-1",
                    "bandwidth": "1Gbps",
                    "map": {
                        "dscp-group": [
                            {
                                "group-name": "real-time",
                                "to": 1
                            }
                        ]
                    }
                }
            ]
        },
        # expected result
        [
            "qos lo profile 0 rate 1250000000 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4"
        ]
    ),
    (
        # A simple profile with the period set to a decimal number
        # test_input
        {
            "burst": "16000",
            "id": "profile-1",
            "period": "0.123"
        },
        # expected_result
        [
            "qos lo profile 0 percent 100 size 16000 period 123",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4"
        ]
    )
]

PARENT_BW_DICT = {"bandwidth": "10Gbit", "burst": "9000"}

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_profile(test_input, expected_result):
    """ Unit-test the profile class """
    attrs = {'profile_index_get.return_value':0}
    interface = Mock(ifname="lo", **attrs)
    parent_bw = Bandwidth(PARENT_BW_DICT, None)
    assert parent_bw is not None
    profile = Profile(0, test_input, parent_bw, None)
    assert profile is not None
    assert profile.commands("qos lo profile", interface, 0) == expected_result
