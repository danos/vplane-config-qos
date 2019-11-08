#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the rule.py module.
"""

import pytest

from vyatta_policy_qos_vci.rule import Rule

TEST_DATA = [
    (
        # test_input
        {
            "action": "pass",
            "destination": {
                "port": "http"
            },
            "dscp": "56",
            "id": "m1",
            "protocol": "tcp",
            "source": {
                "address": "10.10.0.0/24"
            }
        },
        # expected_result
        "action=accept proto-final=6 src-addr=10.10.0.0/24 dst-port=80 " \
        "dscp=56 handle=tag(1)",
    ),
    (
        # test_input
        {
            "action": "drop",
            "ethertype": "ipv4",
            "pcp": "3",
            "fragment": "yes",
            "action-group": "fred",
            "log": "yes"
        },
        # expected_result
        "action=drop ether-type=2048 pcp=3 fragment=y " \
        "rproc=action-group(fred);log handle=tag(1)"
    )
]

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_rule(test_input, expected_result):
    """ Unit-test the rule class """
    rule = Rule(1, test_input)
    assert rule is not None
    assert rule.commands() == expected_result
