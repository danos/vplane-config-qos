#!/usr/bin/env python3

# Copyright (c) 2019, 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the wred_map.py module.
"""

import pytest

from vyatta_policy_qos_vci.wred_map import WredMap, byte_limits

TEST_DATA = [
    (
        # test_input
        {
            "group-name": "priority-group-high",
            "mark-probability": 5,
            "max-threshold": "30000",
            "min-threshold": "20000"
        },
        # expected_result
        " dscp-group priority-group-high packets 30000 20000 5"
    ),
    (
        # test_input
        {
            "group-name": "priority-group-low",
            "mark-probability": 10,
            "max-threshold": "50000",
            "min-threshold": "40000"
        },
        # expected_results
        " dscp-group priority-group-low packets 50000 40000 10"
    )
]


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_wred_map(test_input, expected_result):
    """ Unit-test the WredMap class """
    group = WredMap(test_input, 1, 0, None)
    assert group is not None
    # As all the JSON configs so the check method will not return any errors
    assert group.check("") == (True, None, None)
    assert group.commands("") == expected_result


def test_byte_limits():
    """ Unit-test the byte_limits function - only returns False for UT """
    assert byte_limits() is False
