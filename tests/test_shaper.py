#!/usr/bin/env python3

# Copyright (c) 2019-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the shaper.py module.
"""

from unittest.mock import Mock

import pytest

from vyatta_policy_qos_vci.shaper import Shaper

TEST_DATA = [
    (
        # A simple shaper with just a default profile
        # test_input
        {
            "bandwidth": "10Gbit",
            "default": "profile-1",
            "frame-overhead": "24",
            "profile": [
                {"bandwidth": "1Gbit", "id": "profile-1"}
            ]
        },
        # expected_result
        [
            "qos lo subport 0 rate 1250000000 msec 4 period 40000",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 64",
            "qos lo subport 0 queue 1 percent 100 msec 4",
            "qos lo param subport 0 1 limit packets 64",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo vlan 0 0",
            "qos lo profile 0 rate 125000000 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0"
        ]
    ),
    (
        # A shaper with some modified parameters
        {
            "bandwidth": "2Gbit",
            "burst": "321ms",
            "default": "profile-1",
            "frame-overhead": "16",
            "mark-map": "test123",
            "period": 33,
            "profile": [
                {"bandwidth": "1Gbit", "id": "profile-1"}
            ]
        },
        # expected_result
        [
            "qos lo subport 0 rate 250000000 msec 321 period 33000",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 64",
            "qos lo subport 0 queue 1 percent 100 msec 4",
            "qos lo param subport 0 1 limit packets 64",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo subport 0 mark-map test123",
            "qos lo vlan 0 0",
            "qos lo profile 0 rate 125000000 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0"
        ]
    ),
    (
        # Add a couple of traffic-classes to the shaper
        # test_input
        {
            "bandwidth": "2Gbit",
            "burst": "12345",
            "default": "profile-1",
            "frame-overhead": "16",
            "period": 33,
            "profile": [
                {"bandwidth": "1Gbit", "id": "profile-1"}
            ],
            "traffic-class": [
                {"bandwidth": "100%", "id": 0, "queue-limit": 128},
                {"bandwidth": "100Mbit", "id": 1, "queue-limit": 256}
            ]
        },
        # expected_result
        [
            "qos lo subport 0 rate 250000000 size 12345 period 33000",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 128",
            "qos lo subport 0 queue 1 rate 12500000 msec 4",
            "qos lo param subport 0 1 limit packets 256",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo vlan 0 0",
            "qos lo profile 0 rate 125000000 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0"
        ]
    ),
    (
        # Add a third traffic-class with a wred config
        # test_input
        {
            "bandwidth": "2Gbit",
            "burst": "12345",
            "default": "profile-1",
            "frame-overhead": "16",
            "mark-map": "pcp-egress-map",
            "period": 33,
            "profile": [
                {"bandwidth": "1Gbit", "id": "profile-1"}
            ],
            "traffic-class": [
                {"bandwidth": "100%", "id": 0, "queue-limit": 128},
                {"bandwidth": "100Mbit", "id": 1, "queue-limit": 256},
                {"bandwidth": "100%", "id": 2, "queue-limit": 64,
                 "random-detect": {
                     "filter-weight": 10,
                     "mark-probability": 22,
                     "max-threshold": 63,
                     "min-threshold": 3
                 }
                 }
            ]
        },
        # expected_result
        [
            "qos lo subport 0 rate 250000000 size 12345 period 33000",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 128",
            "qos lo subport 0 queue 1 rate 12500000 msec 4",
            "qos lo param subport 0 1 limit packets 256",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64 red 0 3 63 22 10",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo subport 0 mark-map pcp-egress-map",
            "qos lo vlan 0 0",
            "qos lo profile 0 rate 125000000 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0"
        ]
    ),
    (
        # A simple shaper with the period set to a decimal number
        # test_input
        {
            "bandwidth": "10Gbit",
            "default": "profile-1",
            "frame-overhead": "24",
            "period": "0.1",
            "profile": [
                {"bandwidth": "1Gbit", "id": "profile-1"}
            ]
        },
        # expected_result
        [
            "qos lo subport 0 rate 1250000000 msec 4 period 100",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 64",
            "qos lo subport 0 queue 1 percent 100 msec 4",
            "qos lo param subport 0 1 limit packets 64",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo vlan 0 0",
            "qos lo profile 0 rate 125000000 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0"
        ]
    )
]


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_shaper(test_input, expected_result):
    """ Unit-test the shaper class """
    attrs = {'profile_index_get.return_value': 0}
    interface = Mock(ifname="lo", **attrs)
    shaper = Shaper(test_input, {}, {})
    assert shaper is not None
    assert shaper.commands(interface, 0, 0) == expected_result
