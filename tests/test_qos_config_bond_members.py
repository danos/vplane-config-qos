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
from vyatta_policy_qos_vci.bond_membership import BondMembership

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
    # Create a BondMembership object with the desired membership state
    membership = {
        'vyatta-interfaces-bonding-v1:bond-groups': [
            {
                'bond-group': 'dp0bond1',
                'bond-members': ['dp0xe3', 'dp0xe4']
            }
        ]
    }
    bond_membership = BondMembership(notification=membership)

    config = QosConfigBondMembers(TEST_DATA, bond_membership=bond_membership)
    assert config is not None
    assert len(config.interfaces) == 2
    assert config.find_interface('dp0xe3') is not None
    assert config.find_interface('dp0xe4') is not None
    assert config.get_policy("policy-1") is not None
