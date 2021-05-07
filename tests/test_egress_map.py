#!/usr/bin/env python3

# Copyright (c) 2020, AT&T Intellectual Property.
# All rights reserved.

"""
Unit-tests for the egress_map.py module.
"""

import logging
import pytest
from vyatta_policy_qos_vci.egress_map import EgressMap


LOG = logging.getLogger('Policy QoS VCI')


TEST_DATA = [
    (
        # test_input
        [
            {
                'id': 'out-map-1',
                'dscp-group': [
                    {'id': 'group-1', 'dscp': 0},
                    {'id': 'group-2', 'dscp': 1},
                    {'id': 'group-3', 'dscp': 2},
                    {'id': 'group-4', 'dscp': 3},
                ]
            }
        ],
        # expected_result
        [
            ("qos global-object-cmd egress-map out-map-1 dscp-group group-1",
             "qos global-object-cmd egress-map out-map-1 dscp-group group-1 dscp 0",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 dscp-group group-2",
             "qos global-object-cmd egress-map out-map-1 dscp-group group-2 dscp 1",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 dscp-group group-3",
             "qos global-object-cmd egress-map out-map-1 dscp-group group-3 dscp 2",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 dscp-group group-4",
             "qos global-object-cmd egress-map out-map-1 dscp-group group-4 dscp 3",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 complete",
             "qos global-object-cmd egress-map out-map-1 complete",
             "ALL"),
        ]
    )
]


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_egress_map(test_input, expected_result):
    """
    Unit-test the egress-map class.
    """
    eg_maps = []
    for egress_map_dict in test_input:
        egress_map = EgressMap(egress_map_dict)
        assert egress_map is not None
        eg_maps.append(egress_map)

    cmd_list = []
    for egress_map in eg_maps:
        cmd_list.extend(egress_map.commands())

    assert cmd_list == expected_result
