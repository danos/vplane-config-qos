#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the mark_map.py module.
"""

import pytest

from vyatta_policy_qos_vci.mark_map import MarkMap


TEST_DATA = [
    (
        # test_input
        {
            "dscp-group": [
                {
                    "group-name": "default-group-high-drop",
                    "pcp-mark": 2
                },
                {
                    "group-name": "default-group-low-drop",
                    "pcp-mark": 3
                },
                {
                    "group-name": "priority-group-high-drop",
                    "pcp-mark": 4
                },
                {
                    "group-name": "priority-group-low-drop",
                    "pcp-mark": 5
                },
                {
                    "group-name": "real-time-group",
                    "pcp-mark": 6
                },
                {
                    "group-name": "synch-group",
                    "pcp-mark": 7
                }
            ],
            "id": "test123"
        },
        # expected_result
        [
            ("qos mark-map test123 dscp-group default-group-high-drop",
             "qos 0 mark-map test123 dscp-group default-group-high-drop pcp 2",
             "ALL"),
            ("qos mark-map test123 dscp-group default-group-low-drop",
             "qos 0 mark-map test123 dscp-group default-group-low-drop pcp 3",
             "ALL"),
            ("qos mark-map test123 dscp-group priority-group-high-drop",
             "qos 0 mark-map test123 dscp-group priority-group-high-drop pcp 4",
             "ALL"),
            ("qos mark-map test123 dscp-group priority-group-low-drop",
             "qos 0 mark-map test123 dscp-group priority-group-low-drop pcp 5",
             "ALL"),
            ("qos mark-map test123 dscp-group real-time-group",
             "qos 0 mark-map test123 dscp-group real-time-group pcp 6",
             "ALL"),
            ("qos mark-map test123 dscp-group synch-group",
             "qos 0 mark-map test123 dscp-group synch-group pcp 7",
             "ALL")
        ]
    )
]

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_mark_map(test_input, expected_result):
    """ Unit-test the MarkMap class """
    mark_map = MarkMap(test_input)
    assert mark_map is not None
    assert mark_map.commands() == expected_result
    assert mark_map.delete_cmd() == [("qos mark-map test123",
                                      "qos 0 mark-map test123 delete",
                                      "ALL")]
