#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the qclass.py module.
"""

from unittest.mock import Mock

import pytest

from vyatta_policy_qos_vci.qclass import Class

TEST_DATA = [
    (
        # single match rule with dscp matching
        # test_input
        {
            # single match rule with dscp matching
            "id": 1,
            "match": [
                {
                    "action": "pass",
                    "dscp": "48",
                    "id": "m1",
                }
            ],
            "profile": "profile-1"
        },
        # expected_result
        [
            "qos 1 pipe 0 1 999",
            "qos 1 match 0 1 action=accept dscp=48 handle=tag(1)"
        ]
    ),
    (
        # Add a source address to the single match rule
        # test_input
        {
            "id": 1,
            "match": [
                {
                    "action": "pass",
                    "dscp": "48",
                    "id": "m1",
                    "source": {
                        "address": "10.10.0.0/24"
                    }
                }
            ],
            "profile": "profile-1"
        },
        # expected_result
        [
            "qos 1 pipe 0 1 999",
            "qos 1 match 0 1 action=accept src-addr=10.10.0.0/24 " \
            "dscp=48 handle=tag(1)"
        ]
    ),
    (
        # Add a second match rule with a TCP protocol match
        # test_input
        {
            "id": 1,
            "match": [
                {
                    "action": "pass",
                    "dscp": "48",
                    "id": "m1",
                    "source": {
                        "address": "10.10.0.0/24"
                    }
                },
                {
                    "action": "pass",
                    "id": "m2",
                    "protocol": "tcp"
                }
            ],
            "profile": "profile-1"
        },
        # expected_result
        [
            "qos 1 pipe 0 1 999",
            "qos 1 match 0 1 action=accept src-addr=10.10.0.0/24 " \
            "dscp=48 handle=tag(1)",
            "qos 1 match 0 1 action=accept proto-final=6 handle=tag(1)"
        ]
    )
]

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_class(test_input, expected_result):
    """ Unit-test the Class class """
    attrs = {'profile_index_get.return_value': 999}
    interface = Mock(ifindex=1, **attrs)
    class_obj = Class(test_input)
    assert class_obj is not None
    assert class_obj.commands(interface, "qos 1", 0, 0) == expected_result
