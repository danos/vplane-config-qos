#!/usr/bin/env python3

# Copyright (c) 2020, AT&T Intellectual Property.
# All rights reserved.

"""
Unit-tests for the egress_map.py module.
"""

from traceback import format_tb
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
                'designation': [
                    {'id': 0, 'dscp' : 0},
                    {'id': 1, 'dscp' : 1},
                    {'id': 2, 'dscp' : 2},
                    {'id': 3, 'dscp' : 3},
                    {'id': 4, 'dscp' : 4},
                    {'id': 5, 'dscp' : 5},
                    {'id': 6, 'dscp' : 6},
                    {'id': 7, 'dscp' : 7}
                ]
            }, {
                'id': 'out-map-2',
                'designation': [
                    {'id': 0, 'pcp' : 7},
                    {'id': 1, 'pcp' : 6},
                    {'id': 2, 'pcp' : 5},
                    {'id': 3, 'pcp' : 4},
                    {'id': 4, 'pcp' : 3},
                    {'id': 5, 'pcp' : 2},
                    {'id': 6, 'pcp' : 1},
                    {'id': 7, 'pcp' : 0}
                ]
            }
        ],
        # expected_result
        [
            ("qos global-object-cmd egress-map out-map-1 designation 0",
             "qos global-object-cmd egress-map out-map-1 designation 0 dscp 0",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 designation 1",
             "qos global-object-cmd egress-map out-map-1 designation 1 dscp 1",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 designation 2",
             "qos global-object-cmd egress-map out-map-1 designation 2 dscp 2",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 designation 3",
             "qos global-object-cmd egress-map out-map-1 designation 3 dscp 3",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 designation 4",
             "qos global-object-cmd egress-map out-map-1 designation 4 dscp 4",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 designation 5",
             "qos global-object-cmd egress-map out-map-1 designation 5 dscp 5",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 designation 6",
             "qos global-object-cmd egress-map out-map-1 designation 6 dscp 6",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 designation 7",
             "qos global-object-cmd egress-map out-map-1 designation 7 dscp 7",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-1 complete",
             "qos global-object-cmd egress-map out-map-1 complete",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-2 designation 0",
             "qos global-object-cmd egress-map out-map-2 designation 0 pcp 7",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-2 designation 1",
             "qos global-object-cmd egress-map out-map-2 designation 1 pcp 6",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-2 designation 2",
             "qos global-object-cmd egress-map out-map-2 designation 2 pcp 5",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-2 designation 3",
             "qos global-object-cmd egress-map out-map-2 designation 3 pcp 4",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-2 designation 4",
             "qos global-object-cmd egress-map out-map-2 designation 4 pcp 3",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-2 designation 5",
             "qos global-object-cmd egress-map out-map-2 designation 5 pcp 2",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-2 designation 6",
             "qos global-object-cmd egress-map out-map-2 designation 6 pcp 1",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-2 designation 7",
             "qos global-object-cmd egress-map out-map-2 designation 7 pcp 0",
             "ALL"),
            ("qos global-object-cmd egress-map out-map-2 complete",
             "qos global-object-cmd egress-map out-map-2 complete",
             "ALL")
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
