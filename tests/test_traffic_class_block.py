#!/usr/bin/env python3

# Copyright (c) 2019, 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the traffic_class_block.py module.
"""

import pytest

from vyatta_policy_qos_vci.bandwidth import Bandwidth
from vyatta_policy_qos_vci.traffic_class_block import TrafficClassBlock

TEST_DATA = [
    (
        # SW-version - fully populated
        # test_input
        [
            {"id": 0, "bandwidth": "40%", "queue-limit": 64},
            {"id": 1, "bandwidth": "30%", "queue-limit": 128},
            {"id": 2, "bandwidth": "20%", "queue-limit": 256},
            {"id": 3, "bandwidth": "10%", "queue-limit": 512}
        ],
        # expected_result
        [
            "qos lo subport 2 queue 0 percent 40 msec 4",
            "qos lo param subport 2 0 limit packets 64",
            "qos lo subport 2 queue 1 percent 30 msec 4",
            "qos lo param subport 2 1 limit packets 128",
            "qos lo subport 2 queue 2 percent 20 msec 4",
            "qos lo param subport 2 2 limit packets 256",
            "qos lo subport 2 queue 3 percent 10 msec 4",
            "qos lo param subport 2 3 limit packets 512",
        ]
    ),
    (
        # SW-version - partial population, missing TCs auto-generated
        # test_input
        [
            {"id": 0, "bandwidth": "15%", "queue-limit": 1024},
            {"id": 2, "bandwidth": "25%", "queue-limit": 2048},
        ],
        # expected_result
        [
            "qos lo subport 2 queue 0 percent 15 msec 4",
            "qos lo param subport 2 0 limit packets 1024",
            "qos lo subport 2 queue 1 percent 100 msec 4",
            "qos lo param subport 2 1 limit packets 64",
            "qos lo subport 2 queue 2 percent 25 msec 4",
            "qos lo param subport 2 2 limit packets 2048",
            "qos lo subport 2 queue 3 percent 100 msec 4",
            "qos lo param subport 2 3 limit packets 64",
        ]
    ),
    (
        # HW-version - fully populated
        [
            {"id": 0, "bandwidth": "10%", "queue-limit-bytes": 10000},
            {"id": 1, "bandwidth": "20%", "queue-limit-bytes": 20000},
            {"id": 2, "bandwidth": "30%", "queue-limit-bytes": 30000},
            {"id": 3, "bandwidth": "40%", "queue-limit-bytes": 40000}
        ],
        [
            "qos lo subport 2 queue 0 percent 10 msec 4",
            "qos lo param subport 2 0 limit bytes 10000",
            "qos lo subport 2 queue 1 percent 20 msec 4",
            "qos lo param subport 2 1 limit bytes 20000",
            "qos lo subport 2 queue 2 percent 30 msec 4",
            "qos lo param subport 2 2 limit bytes 30000",
            "qos lo subport 2 queue 3 percent 40 msec 4",
            "qos lo param subport 2 3 limit bytes 40000",
        ]
    ),
    (
        # HW-version - partial population, missing TCs auto-generated
        [
            {"id": 1, "bandwidth": "95%", "queue-limit-bytes": 5000},
            {"id": 3, "bandwidth": "5%", "queue-limit-bytes": 95000},
        ],
        [
            # NOTE: since the byte-limit if-feature file doesn't exist
            # during unit-testing the auto-generated entries TC-0 and TC-2
            # get the software packet-based default queue-limits
            "qos lo subport 2 queue 0 percent 100 msec 4",
            "qos lo param subport 2 0 limit packets 64",
            "qos lo subport 2 queue 1 percent 95 msec 4",
            "qos lo param subport 2 1 limit bytes 5000",
            "qos lo subport 2 queue 2 percent 100 msec 4",
            "qos lo param subport 2 2 limit packets 64",
            "qos lo subport 2 queue 3 percent 5 msec 4",
            "qos lo param subport 2 3 limit bytes 95000",
        ]
    )
]

# We need a parent bandwidth object to create the TrafficClassBlock object
PARENT_BW_DICT = {"bandwidth": "10Gbit", "burst": "9000"}


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_traffic_class_block(test_input, expected_result):
    """ Unit test the traffic-class-block class """
    parent_bw = Bandwidth(PARENT_BW_DICT, None)
    assert parent_bw is not None
    tcb = TrafficClassBlock(test_input, parent_bw)
    assert tcb is not None
    assert tcb.commands("qos lo subport 2") == expected_result
