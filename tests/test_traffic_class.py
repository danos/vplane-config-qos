#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the traffic_class.py module.
"""

import pytest

from vyatta_policy_qos_vci.bandwidth import Bandwidth
from vyatta_policy_qos_vci.traffic_class import TrafficClass

# Note that "id" and test index are identical
TEST_DATA = [
    (
        # test_input
        {"id": 0, "bandwidth": "1Gbit", "queue-limit": 64},
        # expected_result
        # id qlim  bandwidth-command      queue-limit command
        (0, 64, " rate 125000000 msec 4", " limit packets 64"),
    ),
    (
        # test_input
        {"id": 1, "bandwidth": "100%", "queue-limit": 128},
        # expected_result
        (1, 128, " percent 100 msec 4", " limit packets 128"),
    ),
    (
        # test_input
        {"id": 2, "bandwidth": "50%", "queue-limit": 256, "wred": {
            "filter-weight": 5, "mark-probability": 10, "min-threshold": "32",
            "max-threshold": "96"
            }
         },
        # expected_result
        (2, 256, " percent 50 msec 4", " limit packets 256"),
    ),
    (
        # test_input
        {"id": 3, "bandwidth": "100Mbit", "queue-limit-bytes": 65536},
        # expected_result
        (3, 65536, " rate 12500000 msec 4", " limit bytes 65536")
    )
]

# We need a parent bandwidth object to create the TrafficClass object
PARENT_BW_DICT = {"bandwidth": "10Gbit", "burst": "9000"}


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_traffic_class(test_input, expected_result):
    """ Unit-test the traffic-class class """
    parent_bw = Bandwidth(PARENT_BW_DICT, None)
    assert parent_bw is not None
    test_tc = TrafficClass(test_input['id'], test_input, parent_bw)
    assert test_tc is not None
    actual_result = (test_tc.id, test_tc.queue_limit,
                     test_tc.bandwidth_commands(""),
                     test_tc.queuelimit_commands())
    assert actual_result == expected_result
