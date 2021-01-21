#!/usr/bin/env python3

# Copyright (c) 2019-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the qos_config.py module.
"""

from vyatta_policy_qos_vci.qos_config_bond_members import QosConfigBondMembers

from unittest.mock import Mock

TEST_DATA = {
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

def test_qosconfig_bond_members():
    """ Simple Unit Test for the QoSConfigBondMembers class with bonding group
    in s9500 platform
    """
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

    config = QosConfigBondMembers(TEST_DATA, client=client)
    assert config is not None
    assert len(config.interfaces) == 2
    assert config.find_interface('dp0xe3') is not None
    assert config.find_interface('dp0xe4') is not None
    assert config.get_policy("policy-1") is not None
