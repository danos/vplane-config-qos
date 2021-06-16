#!/usr/bin/env python3

# Copyright (c) 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the traffic_class.py module.
"""
from vyatta_policy_qos_vci.traffic_class import TrafficClass
import pytest


def test_should_only_allow_8_or_less_queues():
    # GIVEN a traffic class
    TRAFFIC_CLASS_DICT = {"queue-limit": 1}  # Dictionary containing queue-limit needed in TrafficClass constructor
    tc_id = 1
    test_tc = TrafficClass(tc_id, TRAFFIC_CLASS_DICT, None)

    # GIVEN the traffic class has 8 queues
    for i in range(8):
        test_tc.add_pipe_queue(i, None)
    result, error, path = test_tc.check("dummy/path")
    assert result is True

    # WHEN a 9th queue is added
    test_tc.add_pipe_queue(8, None)

    # THEN it will fail the check
    result, error, path = test_tc.check("dummy/path")
    assert result is False
    assert error == f"Too many queues assigned to traffic-class {tc_id}"


TRAFFIC_CLASS_DICT_LIST = [
        {"queue-limit": 1, "queue-limit-bytes": 1},
        {"queue-limit": 1, "queue-limit-time": 1},
        {"queue-limit-bytes": 1, "queue-limit-time": 1}
]
@pytest.mark.parametrize("traffic_class_dict", TRAFFIC_CLASS_DICT_LIST)
def test_should_only_allow_one_queue_limit_type(traffic_class_dict):

    # GIVEN a traffic class with multiple queue limit types
    test_tc = TrafficClass(None, traffic_class_dict, None)

    # THEN it will fail the check
    result, error, path = test_tc.check("dummy/path")
    assert result is False
    assert error == "Can have only queue-limit-packets, queue-limit-bytes or queue-limit-time set"
