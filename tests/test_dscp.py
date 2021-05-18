#!/usr/bin/env python3

# Copyright (c) 2019, 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
Unit-tests for the dscp.py module.
"""

import pytest

from vyatta_policy_qos_vci.dscp import dscp_range

TEST_DATA = [
    # good dscp ranges - tuples consist (<test_input>, <expected_results>)
    ("0", [0]),
    ("1-2", [1, 2]),
    ("0x3-0x5", [3, 4, 5]),
    ("6-0x8", [6, 7, 8]),
    ("0x9-11", [9, 10, 11]),
    ("12,13,14-16", [12, 13, 14, 15, 16]),
    ("17-19,21-23,25-27", [17, 18, 19, 21, 22, 23, 25, 26, 27]),
    ("default", [0]),
    ("cs0,cs1", [0, 8]),
    ("cs2-cs3", [16, 17, 18, 19, 20, 21, 22, 23, 24]),
    ("cs4-35", [32, 33, 34, 35]),
    ("38-cs5", [38, 39, 40]),
    ("cs6-0x32", [48, 49, 50]),
    ("0x36-cs7", [54, 55, 56]),
    ("af11,af12-af13,af21", [10, 12, 13, 14, 18]),
    ("0-3,0x5-0x7,af11-af12,cs6-cs7", [0, 1, 2, 3, 5, 6, 7, 10, 11, 12,
                                       48, 49, 50, 51, 52, 53, 54, 55, 56]),
    # bad dscp ranges
    ("z", None),
    ("2-1", None),
    ("64", None),
    ("-3,5", None),
    ("0xg", None),
    ("0x16-0x13", None),
    ("cs2-cs1", None),
    ("cs7-af11", None),
    ("0-3,0x6-0x16,af21-af23,p", None)
]


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_dscp_range(test_input, expected_result):
    """ Unit-test the dscp_range function """
    assert dscp_range(test_input) == expected_result
