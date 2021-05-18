#!/usr/bin/env python3

# Copyright (c) 2019, 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the queue.py module.
"""

import pytest

from vyatta_policy_qos_vci.queue import Queue

# valid JSON data can have "none" in it, we need to define it for python
null = None

TEST_DATA = [
    # During unit-test we always use packet limits
    (
        # test_input
        {"id": 0, "traffic-class": 0, "weight": 1},
        # expected_result
        [" queue 0 wrr-weight 1 0"],
    ),
    (
        # test_input
        {"id": 1, "traffic-class": 1, "weight": 2},
        # expected_result
        [" queue 0x5 wrr-weight 2 1"],
    ),
    (
        # test_input
        {"id": 2, "traffic-class": 2, "weight": 3, "priority-local": [null]},
        # expected_result
        [" queue 0xa wrr-weight 3 2 prio-loc"],
    ),
    (
        # test_input
        {
            "id": 3,
            "traffic-class": 3,
            "weight": 4,
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
        # expected_result
        [" queue 0xf wrr-weight 4 3",
         " queue 0xf dscp-group priority-group-high packets 30000 20000 5",
         " queue 0xf dscp-group priority-group-low packets 50000 40000 10",
         " queue 0xf wred-weight 10"]
    ),
    (
        # test_input
        {
            "id": 4,
            "traffic-class": 3,
            "weight": 4,
            "wred-map-time": {
                "dscp-group": [
                    {
                        "group-name": "priority-group-high",
                        "mark-probability": 5,
                        "max-threshold": "30",
                        "min-threshold": "20"
                    },
                    {
                        "group-name": "priority-group-low",
                        "mark-probability": 10,
                        "max-threshold": "50",
                        "min-threshold": "40"
                    }
                ],
                "filter-weight": 10
            }
        },
        # expected_result
        [" queue 0x13 wrr-weight 4 4",
         " queue 0x13 dscp-group priority-group-high usec 30000 20000 5",
         " queue 0x13 dscp-group priority-group-low usec 50000 40000 10",
         " queue 0x13 wred-weight 10"]
    )
]


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_queue(test_input, expected_result):
    """ Unit-test a queue object """
    tc_id = test_input.get('traffic-class')
    wrr_id = test_input.get('id')
    wrr_weight = test_input.get('weight')
    priority_local = test_input.get('priority-local')
    is_time = 0
    wred_map_dict = test_input.get('wred-map-bytes')
    if wred_map_dict is None:
        wred_map_dict = test_input.get('wred-map-time')
        is_time = 1
    queue = Queue(tc_id, wrr_id, wrr_weight, priority_local, wred_map_dict, is_time, None)
    assert queue is not None
    assert queue.commands("", queue.wrr_id) == expected_result
