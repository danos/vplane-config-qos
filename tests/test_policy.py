#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the policy.py module.
"""

from unittest.mock import Mock

import pytest

from vyatta_policy_qos_vci.policy import Policy

TEST_DATA = [
    (
        # test_input
        {
            "id": "policy-1",
            "shaper": {
                "bandwidth": "10Gbit",
                "default": "profile-1",
                "frame-overhead": "24",
                "profile": [
                    {"bandwidth": "1Gbit", "id": "profile-1"}
                ]
            }
        },
        # expected_results
        [
            "qos lo subport 0 rate 1250000000 msec 4 period 40",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 64",
            "qos lo subport 0 queue 1 percent 100 msec 4",
            "qos lo param subport 0 1 limit packets 64",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo vlan 0 0",
            "qos lo profile 0 rate 125000000 msec 4 period 10",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0"
        ]
    )
]

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_policy(test_input, expected_result):
    """ Unit-test the policy class """
    attrs = {'profile_index_get.return_value':0}
    interface = Mock(ifname="lo",**attrs)
    policy = Policy(test_input, {}, {})
    assert policy is not None
    assert policy.commands(interface, 0, 0) == expected_result
