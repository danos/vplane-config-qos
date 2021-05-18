#!/usr/bin/env python3

# Copyright (c) 2020- 2021, AT&T Intellectual Property.
# All rights reserved.

"""
Unit-tests for the ingress_map.py module.
"""

import pytest

from vyatta_policy_qos_vci.ingress_map import IngressMap

TEST_DATA = [
    (
        # test_input
        [
            {
                'id': 'in-map-1',
                'pcp': [
                    {'id': 0, 'designation': 0, 'drop-precedence': "green"},
                    {'id': 1, 'designation': 1, 'drop-precedence': "yellow"},
                    {'id': 2, 'designation': 2, 'drop-precedence': "red"},
                    {'id': 3, 'designation': 3, 'drop-precedence': "red"},
                    {'id': 4, 'designation': 4, 'drop-precedence': "yellow"},
                    {'id': 5, 'designation': 5, 'drop-precedence': "green"},
                    {'id': 6, 'designation': 6, 'drop-precedence': "green"},
                    {'id': 7, 'designation': 7, 'drop-precedence': "yellow"}
                ]
            }, {
                'id': 'in-map-2',
                'dscp-group': [
                    {'id': 'group-1', 'designation': 0, 'drop-precedence': "green"},
                    {'id': 'group-2', 'designation': 1, 'drop-precedence': "green"},
                    {'id': 'group-3', 'designation': 2, 'drop-precedence': "green"},
                    {'id': 'group-4', 'designation': 2, 'drop-precedence': "yellow"}
                ],
                'system-default': [None]
            }
        ],
        # expected_result
        [
            ("qos global-object-cmd ingress-map in-map-1 pcp 0",
             "qos global-object-cmd ingress-map in-map-1 pcp 0 designation 0 drop-prec green",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-1 pcp 1",
             "qos global-object-cmd ingress-map in-map-1 pcp 1 designation 1 drop-prec yellow",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-1 pcp 2",
             "qos global-object-cmd ingress-map in-map-1 pcp 2 designation 2 drop-prec red",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-1 pcp 3",
             "qos global-object-cmd ingress-map in-map-1 pcp 3 designation 3 drop-prec red",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-1 pcp 4",
             "qos global-object-cmd ingress-map in-map-1 pcp 4 designation 4 drop-prec yellow",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-1 pcp 5",
             "qos global-object-cmd ingress-map in-map-1 pcp 5 designation 5 drop-prec green",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-1 pcp 6",
             "qos global-object-cmd ingress-map in-map-1 pcp 6 designation 6 drop-prec green",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-1 pcp 7",
             "qos global-object-cmd ingress-map in-map-1 pcp 7 designation 7 drop-prec yellow",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-1 complete",
             "qos global-object-cmd ingress-map in-map-1 complete",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-2 dscp-group group-1",
             "qos global-object-cmd ingress-map in-map-2 dscp-group group-1 designation 0 drop-prec green",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-2 dscp-group group-2",
             "qos global-object-cmd ingress-map in-map-2 dscp-group group-2 designation 1 drop-prec green",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-2 dscp-group group-3",
             "qos global-object-cmd ingress-map in-map-2 dscp-group group-3 designation 2 drop-prec green",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-2 dscp-group group-4",
             "qos global-object-cmd ingress-map in-map-2 dscp-group group-4 designation 2 drop-prec yellow",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-2 system-default",
             "qos global-object-cmd ingress-map in-map-2 system-default",
             "ALL"),
            ("qos global-object-cmd ingress-map in-map-2 complete",
             "qos global-object-cmd ingress-map in-map-2 complete",
             "ALL")
        ]
    )
]


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_ingress_map(test_input, expected_result):
    """
    Unit-test the ingress-map class.
    """
    in_maps = []
    for ingress_map_dict in test_input:
        ingress_map = IngressMap(ingress_map_dict)
        assert ingress_map is not None
        in_maps.append(ingress_map)

    cmd_list = []
    for ingress_map in in_maps:
        cmd_list.extend(ingress_map.commands())

    assert cmd_list == expected_result
