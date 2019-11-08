#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the action.py module.
"""

from vyatta_policy_qos_vci.action import Action

def test_action():
    """ Some simple unit-tests for the action class """
    # Python doesn't define null but it is valid JSON
    null = None

    test_data = [
        {
            "id": "joey",
            "mark": {"pcp": 1}
        },
        {
            "id": "fred",
            "mark": {"dscp": "2"}
        },
        {
            "id": "paul",
            "mark": {"dscp": "cs4"}
        },
        {
            "id": "bill",
            "police": {
                "bandwidth": "100Mbit"
            }
        },
        {
            "id": "gary",
            "mark": {"pcp-inner": [null]},
            "police": {
                "bandwidth": "200Mbit"
            }
        },
        {
            "id": "bert",
            "mark": {"dscp": "18", "pcp": 4},
            "police": {
                "bandwidth": "1Gbit",
                "burst": 10000
            }
        },
        {
            "id": "jack",
            "mark": {"dscp": "18", "pcp": 7, "pcp-inner": [null]},
            "police": {
                "bandwidth": "2Gbit",
                "burst": 20000
            }
        }
    ]

    expected_results = [
        [("policy action name joey",
          "npf-cfg add action-group:joey 0 rproc=markpcp(1,none)")],
        [("policy action name fred",
          "npf-cfg add action-group:fred 0 rproc=markdscp(2)")],
        [("policy action name paul",
          "npf-cfg add action-group:paul 0 rproc=markdscp(32)")],
        [("policy action name bill",
          "npf-cfg add action-group:bill 0 rproc=policer(0,12500000,50000,drop,,0,20)")],
        [("policy action name gary",
          "npf-cfg add action-group:gary 0 rproc=policer(0,25000000,100000,drop,,0,20)")],
        [("policy action name bert",
          "npf-cfg add action-group:bert 0 rproc=markpcp(4,none);" \
          "policer(0,125000000,10000,drop,,0,20)")],
        [("policy action name jack",
          "npf-cfg add action-group:jack 0 rproc=markpcp(7,inner);" \
          "policer(0,250000000,20000,drop,,0,20)")]
    ]

    for test_input, expected_result in zip(test_data, expected_results):
        action = Action(test_input)
        assert action is not None
        assert action.commands() == expected_result
