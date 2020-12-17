#!/usr/bin/env python3

# Copyright (c) 2019-2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the qos_config.py module.
"""

from vyatta_policy_qos_vci.qos_config import QosConfig

from unittest.mock import Mock

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

TEST_DATA_SIAD_BONDED = {
    'vyatta-interfaces-v1:interfaces': {
        'vyatta-interfaces-bonding-v1:bonding': [
            {
                'tagnode': 'dp0bond1',
                'vyatta-interfaces-bonding-switch-v1:switch-group': {
                    'port-parameters': {
                        'vyatta-interfaces-switch-policy-v1:policy': {
                            'vyatta-policy-qos-v1:qos': 'policy-1'
                        }
                    }
                }
            }
        ]
    },
    'vyatta-policy-v1:policy': {
        'vyatta-policy-qos-v1:qos': {
            'name': [
                {
                    'id': 'policy-1',
                    'shaper': {
                        'bandwidth': 'auto',
                        'burst': 16000,
                        'default': 'profile-1',
                        'frame-overhead': '24'
                    }
                }
            ],
            'profile': [
                {
                    'bandwidth': '200Mbit',
                    'burst': 16000,
                    'id': 'profile-1'
                }
            ]
        }
    }
}

def test_qosconfig():
    """ Simple Unit Test for the QoSConfig class """
    config = QosConfig(TEST_DATA)
    assert config is not None
    assert len(config.interfaces) == 2
    assert config.find_interface("lo") is not None
    assert len(config.global_profiles) == 1
    assert config.find_global_profile("global-profile-1") is not None
    assert config.get_policy("policy-1") is not None
    assert config.get_mark_map("test123") is not None
    assert config.get_action_group("action-group-1") is not None
    assert config.get_action_group("action-group-2") is not None
    assert config.get_ingress_map("in-map-1") is not None
    assert config.get_ingress_map("in-map-2") is not None

def test_qosconfig_siad_bonded():
    """ Simple Unit Test for the QoSConfig class with bonding group in SIAD """
    # Mock up a configuration object from configd
    attrs = {
        'tree_get_dict.return_value': {
            'dataplane': [
                {
                    'tagnode': 'dp0xe1',
                    'admin-status': 'up',
                    'duplex': 'auto',
                    'ip': {
                        'gratuitous-arp-count': 1,
                        'rpf-check': 'disable'
                    },
                    'ipv6': {
                        'dup-addr-detect-transmits': 1
                    },
                    'mtu': 1500,
                    'oper-status': 'dormant',
                    'speed': 'auto',
                    'vlan-protocol': '0x8100',
                    'vrrp': {
                        'start-delay': 0
                    }
                },
                {
                    'tagnode': 'dp0xe2',
                    'admin-status': 'up',
                    'duplex': 'auto',
                    'ip': {
                        'gratuitous-arp-count': 1,
                        'rpf-check': 'disable'
                    },
                    'ipv6': {
                        'dup-addr-detect-transmits': 1
                    },
                    'mtu': 1500,
                    'oper-status': 'dormant',
                    'speed': 'auto',
                    'vlan-protocol': '0x8100',
                    'vrrp': {
                        'start-delay': 0
                    }
                },
                {
                    'tagnode': 'dp0xe3',
                    'admin-status': 'up',
                    'bond-group': 'dp0bond1',
                    'duplex': 'auto',
                    'ip': {
                        'gratuitous-arp-count': 1,
                        'rpf-check': 'disable'
                    },
                    'ipv6': {
                        'dup-addr-detect-transmits': 1
                    },
                    'mtu': 1500,
                    'oper-status': 'dormant',
                    'speed': 'auto',
                    'vlan-protocol': '0x8100',
                    'vrrp': {
                        'start-delay': 0
                    }
                },
                {
                    'tagnode': 'dp0xe4',
                    'admin-status': 'up',
                    'bond-group': 'dp0bond1',
                    'duplex': 'auto',
                    'ip': {
                        'gratuitous-arp-count': 1,
                        'rpf-check': 'disable'
                    },
                    'ipv6': {
                        'dup-addr-detect-transmits': 1
                    },
                    'mtu': 1500,
                    'oper-status': 'dormant',
                    'speed': 'auto',
                    'vlan-protocol': '0x8100',
                    'vrrp': {
                        'start-delay': 0
                    }
                },
            ]
        }
    }
    # Mock up configd
    mock_config = Mock(**attrs)
    attrs = {
        'Client.return_value': mock_config
    }
    configd = Mock(**attrs)
    client = configd.Client()

    config = QosConfig(TEST_DATA_SIAD_BONDED, client=client)
    assert config is not None
    assert len(config.interfaces) == 2
    assert config.find_interface('dp0xe3') is not None
    assert config.find_interface('dp0xe4') is not None
    assert config.get_policy("policy-1") is not None
