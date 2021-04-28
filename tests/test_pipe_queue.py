#!/usr/bin/env python3

# Copyright (c) 2019,2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the pipe_queue.py module.
"""

import pytest

from vyatta_policy_qos_vci.bandwidth import Bandwidth
from vyatta_policy_qos_vci.pipe_queue import PipeQueues
from vyatta_policy_qos_vci.traffic_class_block import TrafficClassBlock

# valid JSON data can have "none" in it, we need to define it for python
null = None

TEST_DATA = [
    (
        # 4 pipe-queues, one per traffic-class with identical weights
        # test_input
        [
            {"id": 0, "traffic-class": 0, "weight": 1},
            {"id": 1, "traffic-class": 1, "weight": 1},
            {"id": 2, "traffic-class": 2, "weight": 1},
            {"id": 3, "traffic-class": 3, "weight": 1},
        ],
        # expected_result
        # The numerical columns are: qmap wrr-weight pipe-queue-id
        # where qmap is wrr-queue-id << 2 | traffic-class
        [
            " queue 0 wrr-weight 1 0",
            " queue 0x1 wrr-weight 1 1",
            " queue 0x2 wrr-weight 1 2",
            " queue 0x3 wrr-weight 1 3",
        ]
    ),
    (
        # 8 pipe-queues all for the same traffic-class
        # test_input
        [
            {"id": 0, "traffic-class": 0, "weight": 1},
            {"id": 1, "traffic-class": 0, "weight": 1},
            {"id": 2, "traffic-class": 0, "weight": 1},
            {"id": 3, "traffic-class": 0, "weight": 1},
            {"id": 4, "traffic-class": 0, "weight": 1},
            {"id": 5, "traffic-class": 0, "weight": 1},
            {"id": 6, "traffic-class": 0, "weight": 1},
            {"id": 7, "traffic-class": 0, "weight": 1},
        ],
        # expected_result
        [
            " queue 0 wrr-weight 1 0",
            " queue 0x4 wrr-weight 1 1",
            " queue 0x8 wrr-weight 1 2",
            " queue 0xc wrr-weight 1 3",
            " queue 0x10 wrr-weight 1 4",
            " queue 0x14 wrr-weight 1 5",
            " queue 0x18 wrr-weight 1 6",
            " queue 0x1c wrr-weight 1 7",
        ],
    ),
    (
        # 8 pipe-queues, two to each traffic-class with different weights
        # test_input
        [
            {"id": 0, "traffic-class": 0, "weight": 11},
            {"id": 1, "traffic-class": 0, "weight": 12},
            {"id": 2, "traffic-class": 1, "weight": 23},
            {"id": 3, "traffic-class": 1, "weight": 24},
            {"id": 4, "traffic-class": 2, "weight": 35},
            {"id": 5, "traffic-class": 2, "weight": 36},
            {"id": 6, "traffic-class": 3, "weight": 47},
            {"id": 7, "traffic-class": 3, "weight": 48}
        ],
        # expected_result
        [
            " queue 0 wrr-weight 11 0",
            " queue 0x4 wrr-weight 12 1",
            " queue 0x1 wrr-weight 23 2",
            " queue 0x5 wrr-weight 24 3",
            " queue 0x2 wrr-weight 35 4",
            " queue 0x6 wrr-weight 36 5",
            " queue 0x3 wrr-weight 47 6",
            " queue 0x7 wrr-weight 48 7"
        ],
    ),
    (
        # 2 pipe-queues, different TCs, one for local-priority traffic
        # test_input
        [
            {"id": 9, "traffic-class": 0, "weight": 1},
            {"id": 10, "traffic-class": 1, "weight": 1, "priority-local": [null]}
        ],
        # expected_result
        [
            # the local-priority queue never uses wrr-id 0 hence a qmap of 0x5
            " queue 0 wrr-weight 1 9",
            " queue 0x5 wrr-weight 1 10 prio-loc"
        ],
    ),
    (
        # one pipe-queue with two dscp-group wred-maps
        # test_input
        [
            {
                "id": 2,
                "traffic-class": 2,
                "weight": 1,
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
            }
        ],
        # expected_result
        [
            # one pipe-queue with two dscp-group wred-maps
            # NOTE: during unit-test we always use packet limits
            " queue 0x2 wrr-weight 1 2",
            " queue 0x2 dscp-group priority-group-high packets 30000 20000 5",
            " queue 0x2 dscp-group priority-group-low packets 50000 40000 10",
            " queue 0x2 wred-weight 10"
        ]
    )
]

# We need a parent Bandwidth object to create the TrafficClassBlock object
PARENT_BW_DICT = {"bandwidth": "10Gbit", "burst": "9000"}

# We need a TrafficClassBlock object in order to create a PipeQueues object
# The TrafficClassBlock object doesn't affect the PipeQueue's commands
TCB_DICT_LIST = [
    {"id": 0, "bandwidth": "40%", "queue-limit": 64},
    {"id": 1, "bandwidth": "30%", "queue-limit": 128},
    {"id": 2, "bandwidth": "20%", "queue-limit": 256},
    {"id": 3, "bandwidth": "10%", "queue-limit": 512}
]

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_pipe_queue(test_input, expected_result):
    """ Unit-test the pipe-queue class """
    parent_bw = Bandwidth(PARENT_BW_DICT, None)
    assert parent_bw is not None
    tcb = TrafficClassBlock(TCB_DICT_LIST, parent_bw)
    assert tcb is not None
    pipe_queues = PipeQueues(test_input, tcb, None)
    assert pipe_queues is not None
    assert pipe_queues.commands("") == expected_result
