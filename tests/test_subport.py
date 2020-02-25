#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the subport.py module.
"""

from unittest.mock import Mock

import pytest

from vyatta_policy_qos_vci.policy import Policy
from vyatta_policy_qos_vci.subport import Subport

POLICY_1_DICT = {
    "id": "policy-1",
    "shaper": {
        "bandwidth": "10Gbit",
        "default": "profile-1",
        "frame-overhead": "24",
        "profile": [
            {"bandwidth": "1Gbit", "id": "profile-1"}
        ]
    }
}

POLICY_2_DICT = {
    "id": "policy-2",
    "shaper": {
        "bandwidth": "5Gbit",
        "default": "profile-2",
        "frame-overhead": "20",
        "profile": [
            {"bandwidth": "500Mbit", "id": "profile-2"}
        ]
    }
}

POLICY_1 = Policy(POLICY_1_DICT, {}, {})
POLICY_2 = Policy(POLICY_2_DICT, {}, {})
assert POLICY_1 is not None
assert POLICY_2 is not None

TEST_DATA = [
    #subport-id, vlan-id, policy-obj
    (
        # test_input
        (0, 0, POLICY_1),
        # expected_result
        [
            "qos 1 subport 0 rate 1250000000 msec 4 period 40",
            "qos 1 subport 0 queue 0 percent 100 msec 4",
            "qos 1 param subport 0 0 limit packets 64",
            "qos 1 subport 0 queue 1 percent 100 msec 4",
            "qos 1 param subport 0 1 limit packets 64",
            "qos 1 subport 0 queue 2 percent 100 msec 4",
            "qos 1 param subport 0 2 limit packets 64",
            "qos 1 subport 0 queue 3 percent 100 msec 4",
            "qos 1 param subport 0 3 limit packets 64",
            "qos 1 vlan 0 0",
            "qos 1 profile 0 rate 125000000 msec 4 period 10",
            "qos 1 profile 0 queue 0 percent 100 msec 4",
            "qos 1 profile 0 queue 1 percent 100 msec 4",
            "qos 1 profile 0 queue 2 percent 100 msec 4",
            "qos 1 profile 0 queue 3 percent 100 msec 4",
            "qos 1 pipe 0 0 0"
        ]
    ),
    (
        # test_input
        (1, 10, POLICY_2),
        # expected_result
        [
            "qos 1 subport 1 rate 625000000 msec 4 period 40",
            "qos 1 subport 1 queue 0 percent 100 msec 4",
            "qos 1 param subport 1 0 limit packets 64",
            "qos 1 subport 1 queue 1 percent 100 msec 4",
            "qos 1 param subport 1 1 limit packets 64",
            "qos 1 subport 1 queue 2 percent 100 msec 4",
            "qos 1 param subport 1 2 limit packets 64",
            "qos 1 subport 1 queue 3 percent 100 msec 4",
            "qos 1 param subport 1 3 limit packets 64",
            "qos 1 vlan 10 1",
            "qos 1 profile 0 rate 62500000 msec 4 period 10",
            "qos 1 profile 0 queue 0 percent 100 msec 4",
            "qos 1 profile 0 queue 1 percent 100 msec 4",
            "qos 1 profile 0 queue 2 percent 100 msec 4",
            "qos 1 profile 0 queue 3 percent 100 msec 4",
            "qos 1 pipe 1 0 0"
        ]
    )
]

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_subport(test_input, expected_result):
    """ Unit-test a subport object """
    attrs = {'profile_index_get.return_value':0}
    interface = Mock(ifindex=1, **attrs)
    subport = Subport(interface, *test_input)
    assert subport is not None
    subport.build_profile_index(interface)
    assert subport.commands(interface) == expected_result
