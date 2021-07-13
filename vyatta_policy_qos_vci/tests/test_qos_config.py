#!/usr/bin/env python3

# Copyright (c) 2019-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the qos_config.py module.
"""

from vyatta_policy_qos_vci.qos_config import QosConfig
from vyatta_policy_qos_vci.qos_config_bond_members import QosConfigBondMembers

TEST_DATA = {
    "vyatta-interfaces-v1:interfaces": {
        "vyatta-interfaces-dataplane-v1:dataplane": [
            {
                "tagnode": "lo",
                "vif": [
                    {
                        "tagnode": 10,
                        "vyatta-interfaces-policy-v1:policy": {
                            "vyatta-policy-qos-v1:qos": "policy-1"
                        }
                    }
                ],
                "vyatta-interfaces-policy-v1:policy": {
                    "vyatta-policy-qos-v1:qos": "policy-1"
                }
            }
        ],
        "vyatta-interfaces-vhost-v1:vhost": [
            {
                "name": "dp0vhost0",
                "vyatta-interfaces-vhost-policy-v1:policy": {
                    "vyatta-interfaces-vhost-qos-v1:qos": "policy-1"
                }
            }
        ]
    },
    "vyatta-policy-v1:policy": {
        "vyatta-policy-action-v1:action": {
            "name": [
                {
                    "id": "action-group-2",
                    "mark": {
                        "pcp": 3
                    }
                },
                {
                    "id": "action-group-1",
                    "mark": {
                        "dscp": "cs6"
                    }
                }
            ]
        },
        "vyatta-policy-qos-v1:qos": {
            "mark-map": [
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
                }
            ],
            "name": [
                {
                    "id": "policy-1",
                    "shaper": {
                        "bandwidth": "10Gbit",
                        "default": "profile-1",
                        "frame-overhead": "24",
                        "profile": [
                            {
                                "id": "profile-1"
                            }
                        ]
                    }
                }
            ],
            "profile": [
                {
                    "bandwidth": "600Mbit",
                    "id": "global-profile-1"
                }
            ]
        },
        'vyatta-policy-qos-v1:ingress-map': [
            {
                'id': 'in-map-1',
                'pcp': [
                    {'id': 0, 'designation': 0},
                    {'id': 1, 'designation': 1},
                    {'id': 2, 'designation': 2},
                    {'id': 3, 'designation': 3},
                    {'id': 4, 'designation': 4},
                    {'id': 5, 'designation': 5},
                    {'id': 6, 'designation': 6},
                    {'id': 7, 'designation': 7}
                ]
            }, {
                'id': 'in-map-2',
                'dscp-group': [
                    {'id': 'group-1', 'designation': 0},
                    {'id': 'group-2', 'designation': 1},
                    {'id': 'group-3', 'designation': 2}
                ]
            }
        ],
        'vyatta-policy-qos-v1:egress-map': [
            {
                'id': 'out-map-1',
                'designation': [
                    {'id': 0, 'dscp': 0},
                    {'id': 1, 'dscp': 1},
                    {'id': 2, 'dscp': 2},
                    {'id': 3, 'dscp': 3},
                    {'id': 4, 'dscp': 4},
                    {'id': 5, 'dscp': 5},
                    {'id': 6, 'dscp': 6},
                    {'id': 7, 'dscp': 7}
                ]
            },
            {
                'id': 'out-map-2',
                'designation': [
                    {'id': 0, 'pcp': 7},
                    {'id': 1, 'pcp': 6},
                    {'id': 2, 'pcp': 5},
                    {'id': 3, 'pcp': 4},
                    {'id': 4, 'pcp': 3},
                    {'id': 5, 'pcp': 2},
                    {'id': 6, 'pcp': 1},
                    {'id': 7, 'pcp': 0}
                ]
            }
        ]
    }
}


def simple_qos_config_test(qos_config):
    assert qos_config is not None
    assert len(qos_config.interfaces) == 2
    assert qos_config.find_interface("lo") is not None
    assert len(qos_config.global_profiles) == 1
    assert qos_config.find_global_profile("global-profile-1") is not None
    assert qos_config.get_policy("policy-1") is not None
    assert qos_config.get_mark_map("test123") is not None
    assert qos_config.get_action_group("action-group-1") is not None
    assert qos_config.get_action_group("action-group-2") is not None
    assert qos_config.get_ingress_map("in-map-1") is not None
    assert qos_config.get_ingress_map("in-map-2") is not None


def test_qosconfig():
    """ Simple Unit Test for the QoSConfig class """
    config = QosConfig(TEST_DATA)
    simple_qos_config_test(config)


def test_qosconfig_bond_members_no_bonding():
    """ Simple Unit Test for the QoSConfigBondMembers class. This test
    ensures that QosConfigBondMembers class has the same behavior of QosConfig
    when there are not bonding groups in the configuration.
    """
    config = QosConfigBondMembers(TEST_DATA)
    simple_qos_config_test(config)
