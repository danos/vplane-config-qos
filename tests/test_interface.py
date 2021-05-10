#!/usr/bin/env python3

# Copyright (c) 2019-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the interface.py module.
"""

import pytest
from unittest.mock import Mock

from vyatta_policy_qos_vci.ingress_map import IngressMap
from vyatta_policy_qos_vci.egress_map import EgressMap
from vyatta_policy_qos_vci.interface import (Interface, MissingBondGroupError)
from vyatta_policy_qos_vci.policy import Policy

# The following tests are based upon the following Vyatta VM and SIAD
# configurations
#
# set interfaces dataplane dp0s5 policy qos policy-1
# set interfaces dataplane dp0s5 vif 10 policy qos policy-2
#
# set interfaces dataplane dp0xe6 switch-group port-parameters policy
#    qos policy-3
# set interfaces dataplane dp0xe6 switch-group port-parameters
#    vlan-parameters qos-parameters vlan 10 policy qos policy-4
# set interfaces dataplane dp0xe6 switch-group port-parameters
#    vlan-parameters qos-parameters vlan 20 policy qos policy-5
#

# For unit-testing the "tagnode" of trunk interfaces needs to be "lo"
# not dp0s5 or dp0xe6
VM_IF_DICT = {
    "tagnode": "lo",
    "vyatta-interfaces-policy-v1:policy": {
        "vyatta-policy-qos-v1:qos": "policy-1"
    }
}

VM_VLAN_DICT = {
    "tagnode": "lo",
    "vif": [
        {
            "tagnode": 10,
            "vyatta-interfaces-policy-v1:policy": {
                "vyatta-policy-qos-v1:qos": "policy-2"
            }
        }
    ],
    "vyatta-interfaces-policy-v1:policy": {
        "vyatta-policy-qos-v1:qos": "policy-1"
    }
}

VM_POLICY_1_DICT = {
    "id": "policy-1",
    "shaper": {
        "bandwidth": "1Gbit",
        "default": "profile-1",
        "frame-overhead": "24",
        "profile": [
            {
                "id": "profile-1"
            }
        ]
    }
}

VM_POLICY_2_DICT = {
    "id": "policy-2",
    "shaper": {
        "bandwidth": "2Gbit",
        "default": "profile-2",
        "frame-overhead": "12",
        "profile": [
            {
                "id": "profile-2"
            }
        ]
    }
}

SIAD_IF_DICT = {
    "tagnode": "lo",
    "vyatta-interfaces-dataplane-switch-v1:switch-group": {
        "port-parameters": {
            "vyatta-interfaces-switch-policy-v1:policy": {
                "vyatta-policy-qos-v1:qos": "policy-3",
                "vyatta-policy-qos-v1:ingress-map": "in-map-1",
                "vyatta-policy-qos-v1:egress-map": "out-map-1"
            }
        }
    }
}

SIAD_VLAN_DICT = {
    "tagnode": "lo",
    "vyatta-interfaces-dataplane-switch-v1:switch-group": {
        "port-parameters": {
            "vlan-parameters": {
                "qos-parameters": {
                    "vlan": [
                        {
                            "vlan-id": 10,
                            "vyatta-interfaces-switch-policy-v1:policy": {
                                "vyatta-policy-qos-v1:qos": "policy-4"
                            }
                        },
                        {
                            "vlan-id": 20,
                            "vyatta-interfaces-switch-policy-v1:policy": {
                                "vyatta-policy-qos-v1:qos": "policy-5",
                                "vyatta-policy-qos-v1:ingress-map": "in-map-2",
                                "vyatta-policy-qos-v1:egress-map": "out-map-2"
                            }
                        },
                    ]
                }
            },
            "vyatta-interfaces-switch-policy-v1:policy": {
                "vyatta-policy-qos-v1:qos": "policy-3"
            }
        }
    }
}

VM_BONDED_IF_DICT = {
    'tagnode': 'lo',
    'vyatta-interfaces-policy-v1:policy': {
        'vyatta-interfaces-bonding-qos-v1:qos': 'policy-1'
    }
}

VM_BONDED_VLAN_DICT = {
    'tagnode': 'lo',
    'vyatta-interfaces-policy-v1:policy': {
        'vyatta-interfaces-bonding-qos-v1:qos': 'policy-1'
    },
    'vif': [
        {
            'tagnode': 10,
            'vyatta-interfaces-policy-v1:policy': {
                'vyatta-interfaces-bonding-qos-v1:qos': 'policy-2'
            }
        }
    ]
}

DCSG_BONDED_IF_DICT = {
    'tagnode': 'dp0bond1',
    'vyatta-interfaces-policy-v1:policy': {
        'vyatta-interfaces-bonding-qos-v1:qos': 'policy-3'
    }
}

SIAD_BONDED_IF_DICT = {
    'tagnode': 'dp0bond1',
    'vyatta-interfaces-bonding-switch-v1:switch-group': {
        'port-parameters': {
            'vyatta-interfaces-switch-policy-v1:policy': {
                'vyatta-policy-qos-v1:qos': 'policy-3',
                'vyatta-policy-qos-v1:ingress-map': 'in-map-1',
                'vyatta-policy-qos-v1:egress-map': 'out-map-1'
            }
        }
    }
}

SIAD_BONDED_IF_MEMBER_DICT = {
    'tagnode': 'dp0xe3',
    'bond-group': 'dp0bond1',
}

VNF_VHOST_IF_DICT = {
    'name': 'lo',
    'vyatta-interfaces-vhost-policy-v1:policy': {
        'vyatta-interfaces-vhost-qos-v1:qos': 'policy-1'
    }
}

VNF_VHOST_VLAN_DICT = {
    'name': 'lo',
    'vyatta-interfaces-vhost-policy-v1:policy': {
        'vyatta-interfaces-vhost-qos-v1:qos': 'policy-1'
    },
    'vyatta-interfaces-vhost-vif-v1:vif': [
        {
            'tagnode': 10,
            'vyatta-interfaces-vhost-policy-v1:policy': {
                'vyatta-interfaces-vhost-qos-v1:qos': 'policy-2'
            }
        }
    ]
}

SIAD_POLICY_3_DICT = {
    "id": "policy-3",
    "shaper": {
        "bandwidth": "3Gbit",
        "burst": "16000",
        "default": "profile-3",
        "frame-overhead": "6",
        "profile": [
            {
                "burst": "16000",
                "id": "profile-3"
            }
        ]
    }
}

SIAD_POLICY_4_DICT = {
    "id": "policy-4",
    "shaper": {
        "bandwidth": "6Gbit",
        "burst": "32000",
        "default": "profile-4",
        "frame-overhead": "3",
        "profile": [
            {
                "burst": "32000",
                "id": "profile-4"
            }
        ]
    }
}

SIAD_POLICY_5_DICT = {
    "id": "policy-5",
    "shaper": {
        "bandwidth": "12Gbit",
        "burst": "100msec",
        "default": "profile-5",
        "frame-overhead": "3",
        "profile": [
            {
                "burst": "200ms",
                "id": "profile-5"
            }
        ]
    }
}

QOS_POLICY_DICT = {
    "policy-1": Policy(VM_POLICY_1_DICT, {}, {}),
    "policy-2": Policy(VM_POLICY_2_DICT, {}, {}),
    "policy-3": Policy(SIAD_POLICY_3_DICT, {}, {}),
    "policy-4": Policy(SIAD_POLICY_4_DICT, {}, {}),
    "policy-5": Policy(SIAD_POLICY_5_DICT, {}, {})
}

for policy in QOS_POLICY_DICT.values():
    assert policy is not None

TEST_DATA = [
    (
        # test_input
        ('dataplane', VM_IF_DICT, None),
        # expected_data
        [
            # Vyatta VM trunk commands
            'qos lo port subports 1 pipes 1 profiles 1 overhead 24 ql_packets',
            'qos lo subport 0 rate 125000000 msec 4 period 40000',
            'qos lo subport 0 queue 0 percent 100 msec 4',
            'qos lo param subport 0 0 limit packets 64',
            'qos lo subport 0 queue 1 percent 100 msec 4',
            'qos lo param subport 0 1 limit packets 64',
            'qos lo subport 0 queue 2 percent 100 msec 4',
            'qos lo param subport 0 2 limit packets 64',
            'qos lo subport 0 queue 3 percent 100 msec 4',
            'qos lo param subport 0 3 limit packets 64',
            'qos lo vlan 0 0',
            'qos lo profile 0 percent 100 msec 4 period 10000',
            'qos lo profile 0 queue 0 percent 100 msec 4',
            'qos lo profile 0 queue 1 percent 100 msec 4',
            'qos lo profile 0 queue 2 percent 100 msec 4',
            'qos lo profile 0 queue 3 percent 100 msec 4',
            'qos lo pipe 0 0 0',
            'qos lo enable'
        ]
    ),
    (
        # test_input
        ('dataplane', VM_VLAN_DICT, None),
        # expected_data
        [
            # Vyatta VM trunk and vlan commands
            "qos lo port subports 2 pipes 1 profiles 2 overhead 24 ql_packets",
            "qos lo subport 0 rate 125000000 msec 4 period 40000",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 64",
            "qos lo subport 0 queue 1 percent 100 msec 4",
            "qos lo param subport 0 1 limit packets 64",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo vlan 0 0",
            "qos lo profile 0 percent 100 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0",
            "qos lo subport 1 rate 250000000 msec 4 period 40000",
            "qos lo subport 1 queue 0 percent 100 msec 4",
            "qos lo param subport 1 0 limit packets 64",
            "qos lo subport 1 queue 1 percent 100 msec 4",
            "qos lo param subport 1 1 limit packets 64",
            "qos lo subport 1 queue 2 percent 100 msec 4",
            "qos lo param subport 1 2 limit packets 64",
            "qos lo subport 1 queue 3 percent 100 msec 4",
            "qos lo param subport 1 3 limit packets 64",
            "qos lo vlan 10 1",
            "qos lo profile 1 percent 100 msec 4 period 10000",
            "qos lo profile 1 queue 0 percent 100 msec 4",
            "qos lo profile 1 queue 1 percent 100 msec 4",
            "qos lo profile 1 queue 2 percent 100 msec 4",
            "qos lo profile 1 queue 3 percent 100 msec 4",
            "qos lo pipe 1 0 1",
            "qos lo enable"
        ]
    ),
    (
        # test_input
        ('dataplane', SIAD_IF_DICT, None),
        # expected_data
        [
            # SIAD commands
            # During unit-test 'limit packets' commands are issued
            'qos lo port subports 1 pipes 1 profiles 1 overhead 6 ql_packets',
            'qos lo subport 0 rate 375000000 size 16000 period 40000',
            'qos lo subport 0 queue 0 percent 100 msec 4',
            'qos lo param subport 0 0 limit packets 64',
            'qos lo subport 0 queue 1 percent 100 msec 4',
            'qos lo param subport 0 1 limit packets 64',
            'qos lo subport 0 queue 2 percent 100 msec 4',
            'qos lo param subport 0 2 limit packets 64',
            'qos lo subport 0 queue 3 percent 100 msec 4',
            'qos lo param subport 0 3 limit packets 64',
            'qos lo vlan 0 0',
            'qos lo profile 0 percent 100 size 16000 period 10000',
            'qos lo profile 0 queue 0 percent 100 msec 4',
            'qos lo profile 0 queue 1 percent 100 msec 4',
            'qos lo profile 0 queue 2 percent 100 msec 4',
            'qos lo profile 0 queue 3 percent 100 msec 4',
            'qos lo pipe 0 0 0',
            'qos lo enable'
        ]
    ),
    (
        # test_input
        ('dataplane', SIAD_VLAN_DICT, None),
        # expected_data
        [
            # SIAD trunk and vlan commands
            # During unit-test 'limit packets' commands are issued
            "qos lo port subports 3 pipes 1 profiles 3 overhead 6 ql_packets",
            "qos lo subport 0 rate 375000000 size 16000 period 40000",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 64",
            "qos lo subport 0 queue 1 percent 100 msec 4",
            "qos lo param subport 0 1 limit packets 64",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo vlan 0 0",
            "qos lo profile 0 percent 100 size 16000 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0",
            "qos lo subport 1 rate 750000000 size 32000 period 40000",
            "qos lo subport 1 queue 0 percent 100 msec 4",
            "qos lo param subport 1 0 limit packets 64",
            "qos lo subport 1 queue 1 percent 100 msec 4",
            "qos lo param subport 1 1 limit packets 64",
            "qos lo subport 1 queue 2 percent 100 msec 4",
            "qos lo param subport 1 2 limit packets 64",
            "qos lo subport 1 queue 3 percent 100 msec 4",
            "qos lo param subport 1 3 limit packets 64",
            "qos lo vlan 10 1",
            "qos lo profile 1 percent 100 size 32000 period 10000",
            "qos lo profile 1 queue 0 percent 100 msec 4",
            "qos lo profile 1 queue 1 percent 100 msec 4",
            "qos lo profile 1 queue 2 percent 100 msec 4",
            "qos lo profile 1 queue 3 percent 100 msec 4",
            "qos lo pipe 1 0 1",
            "qos lo subport 2 rate 1500000000 msec 100 period 40000",
            "qos lo subport 2 queue 0 percent 100 msec 4",
            "qos lo param subport 2 0 limit packets 64",
            "qos lo subport 2 queue 1 percent 100 msec 4",
            "qos lo param subport 2 1 limit packets 64",
            "qos lo subport 2 queue 2 percent 100 msec 4",
            "qos lo param subport 2 2 limit packets 64",
            "qos lo subport 2 queue 3 percent 100 msec 4",
            "qos lo param subport 2 3 limit packets 64",
            "qos lo vlan 20 2",
            "qos lo profile 2 percent 100 msec 200 period 10000",
            "qos lo profile 2 queue 0 percent 100 msec 4",
            "qos lo profile 2 queue 1 percent 100 msec 4",
            "qos lo profile 2 queue 2 percent 100 msec 4",
            "qos lo profile 2 queue 3 percent 100 msec 4",
            "qos lo pipe 2 0 2",
            "qos lo enable"
        ]
    ),
    (
        # test_input
        ('bonding', VM_BONDED_IF_DICT, None),
        # expected_data
        [
            # Bonded interface trunk commands
            "qos lo port subports 1 pipes 1 profiles 1 overhead 24 ql_packets",
            "qos lo subport 0 rate 125000000 msec 4 period 40000",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 64",
            "qos lo subport 0 queue 1 percent 100 msec 4",
            "qos lo param subport 0 1 limit packets 64",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo vlan 0 0",
            "qos lo profile 0 percent 100 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0",
            "qos lo enable"
        ]
    ),
    (
        # test_input
        ('bonding', VM_BONDED_VLAN_DICT, None),
        # expected_data
        [
            # Bonded interface trunk and vlan commands
            "qos lo port subports 2 pipes 1 profiles 2 overhead 24 ql_packets",
            "qos lo subport 0 rate 125000000 msec 4 period 40000",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 64",
            "qos lo subport 0 queue 1 percent 100 msec 4",
            "qos lo param subport 0 1 limit packets 64",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo vlan 0 0",
            "qos lo profile 0 percent 100 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0",
            "qos lo subport 1 rate 250000000 msec 4 period 40000",
            "qos lo subport 1 queue 0 percent 100 msec 4",
            "qos lo param subport 1 0 limit packets 64",
            "qos lo subport 1 queue 1 percent 100 msec 4",
            "qos lo param subport 1 1 limit packets 64",
            "qos lo subport 1 queue 2 percent 100 msec 4",
            "qos lo param subport 1 2 limit packets 64",
            "qos lo subport 1 queue 3 percent 100 msec 4",
            "qos lo param subport 1 3 limit packets 64",
            "qos lo vlan 10 1",
            "qos lo profile 1 percent 100 msec 4 period 10000",
            "qos lo profile 1 queue 0 percent 100 msec 4",
            "qos lo profile 1 queue 1 percent 100 msec 4",
            "qos lo profile 1 queue 2 percent 100 msec 4",
            "qos lo profile 1 queue 3 percent 100 msec 4",
            "qos lo pipe 1 0 1",
            "qos lo enable"
        ]
    ),
    (
        # test_input
        ('vhost', VNF_VHOST_IF_DICT, None),
        # expected_data
        [
            # vhost interface trunk commands
            "qos lo port subports 1 pipes 1 profiles 1 overhead 24 ql_packets",
            "qos lo subport 0 rate 125000000 msec 4 period 40000",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 64",
            "qos lo subport 0 queue 1 percent 100 msec 4",
            "qos lo param subport 0 1 limit packets 64",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo vlan 0 0",
            "qos lo profile 0 percent 100 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0",
            "qos lo enable"
        ]
    ),
    (
        # test_input
        ('vhost', VNF_VHOST_VLAN_DICT, None),
        # expected_data
        [
            # vhost interface trunk and vlan commands
            "qos lo port subports 2 pipes 1 profiles 2 overhead 24 ql_packets",
            "qos lo subport 0 rate 125000000 msec 4 period 40000",
            "qos lo subport 0 queue 0 percent 100 msec 4",
            "qos lo param subport 0 0 limit packets 64",
            "qos lo subport 0 queue 1 percent 100 msec 4",
            "qos lo param subport 0 1 limit packets 64",
            "qos lo subport 0 queue 2 percent 100 msec 4",
            "qos lo param subport 0 2 limit packets 64",
            "qos lo subport 0 queue 3 percent 100 msec 4",
            "qos lo param subport 0 3 limit packets 64",
            "qos lo vlan 0 0",
            "qos lo profile 0 percent 100 msec 4 period 10000",
            "qos lo profile 0 queue 0 percent 100 msec 4",
            "qos lo profile 0 queue 1 percent 100 msec 4",
            "qos lo profile 0 queue 2 percent 100 msec 4",
            "qos lo profile 0 queue 3 percent 100 msec 4",
            "qos lo pipe 0 0 0",
            "qos lo subport 1 rate 250000000 msec 4 period 40000",
            "qos lo subport 1 queue 0 percent 100 msec 4",
            "qos lo param subport 1 0 limit packets 64",
            "qos lo subport 1 queue 1 percent 100 msec 4",
            "qos lo param subport 1 1 limit packets 64",
            "qos lo subport 1 queue 2 percent 100 msec 4",
            "qos lo param subport 1 2 limit packets 64",
            "qos lo subport 1 queue 3 percent 100 msec 4",
            "qos lo param subport 1 3 limit packets 64",
            "qos lo vlan 10 1",
            "qos lo profile 1 percent 100 msec 4 period 10000",
            "qos lo profile 1 queue 0 percent 100 msec 4",
            "qos lo profile 1 queue 1 percent 100 msec 4",
            "qos lo profile 1 queue 2 percent 100 msec 4",
            "qos lo profile 1 queue 3 percent 100 msec 4",
            "qos lo pipe 1 0 1",
            "qos lo enable"
        ]
    ),
    (
        # test_input
        ('bond_member', SIAD_BONDED_IF_MEMBER_DICT, SIAD_BONDED_IF_DICT),
        # expected_data
        [
            # SIAD commands
            'qos dp0xe3 port subports 1 pipes 1 profiles 1 overhead 6 ql_packets',
            'qos dp0xe3 subport 0 rate 375000000 size 16000 period 40000',
            'qos dp0xe3 subport 0 queue 0 percent 100 msec 4',
            'qos dp0xe3 param subport 0 0 limit packets 64',
            'qos dp0xe3 subport 0 queue 1 percent 100 msec 4',
            'qos dp0xe3 param subport 0 1 limit packets 64',
            'qos dp0xe3 subport 0 queue 2 percent 100 msec 4',
            'qos dp0xe3 param subport 0 2 limit packets 64',
            'qos dp0xe3 subport 0 queue 3 percent 100 msec 4',
            'qos dp0xe3 param subport 0 3 limit packets 64',
            'qos dp0xe3 vlan 0 0',
            'qos dp0xe3 profile 0 percent 100 size 16000 period 10000',
            'qos dp0xe3 profile 0 queue 0 percent 100 msec 4',
            'qos dp0xe3 profile 0 queue 1 percent 100 msec 4',
            'qos dp0xe3 profile 0 queue 2 percent 100 msec 4',
            'qos dp0xe3 profile 0 queue 3 percent 100 msec 4',
            'qos dp0xe3 pipe 0 0 0',
            'qos dp0xe3 enable'
        ]
    ),
    (
        # test_input
        ('bond_member', SIAD_BONDED_IF_MEMBER_DICT, DCSG_BONDED_IF_DICT),
        # expected_data
        [
            # SIAD commands
            'qos dp0xe3 port subports 1 pipes 1 profiles 1 overhead 6 ql_packets',
            'qos dp0xe3 subport 0 rate 375000000 size 16000 period 40000',
            'qos dp0xe3 subport 0 queue 0 percent 100 msec 4',
            'qos dp0xe3 param subport 0 0 limit packets 64',
            'qos dp0xe3 subport 0 queue 1 percent 100 msec 4',
            'qos dp0xe3 param subport 0 1 limit packets 64',
            'qos dp0xe3 subport 0 queue 2 percent 100 msec 4',
            'qos dp0xe3 param subport 0 2 limit packets 64',
            'qos dp0xe3 subport 0 queue 3 percent 100 msec 4',
            'qos dp0xe3 param subport 0 3 limit packets 64',
            'qos dp0xe3 vlan 0 0',
            'qos dp0xe3 profile 0 percent 100 size 16000 period 10000',
            'qos dp0xe3 profile 0 queue 0 percent 100 msec 4',
            'qos dp0xe3 profile 0 queue 1 percent 100 msec 4',
            'qos dp0xe3 profile 0 queue 2 percent 100 msec 4',
            'qos dp0xe3 profile 0 queue 3 percent 100 msec 4',
            'qos dp0xe3 pipe 0 0 0',
            'qos dp0xe3 enable'
        ]
    )
]

IN_MAP_1_DICT = {
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
}

IN_MAP_2_DICT = {
    'id': 'in-map-2',
    'dscp-group': [
        {'id': 'group-1', 'designation': 0},
        {'id': 'group-2', 'designation': 1},
        {'id': 'group-3', 'designation': 2}
    ],
    'system-default': 1
}

OUT_MAP_1_DICT = {
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
}

OUT_MAP_2_DICT = {
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


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_interface(test_input, expected_result):
    """ Unit-test the interface class with simple configs """
    ingress_map_dict = {}
    ingress_map_dict['in-map-1'] = IngressMap(IN_MAP_1_DICT)
    ingress_map_dict['in-map-2'] = IngressMap(IN_MAP_2_DICT)
    egress_map_dict = {}
    egress_map_dict['out-map-1'] = EgressMap(OUT_MAP_1_DICT)
    egress_map_dict['out-map-2'] = EgressMap(OUT_MAP_2_DICT)
    if_type, if_dict, bond_dict = test_input
    interface = Interface(if_type, if_dict, QOS_POLICY_DICT, ingress_map_dict,
                          egress_map_dict, bond_dict=bond_dict)

    assert interface is not None
    assert interface.commands() == expected_result


def test_missing_bond_group():
    """
    Interface construction must raise exception if bond_member interface is
    provided without bond_group
    """
    ingress_map_dict = {}
    ingress_map_dict['in-map-1'] = IngressMap(IN_MAP_1_DICT)
    ingress_map_dict['in-map-2'] = IngressMap(IN_MAP_2_DICT)
    egress_map_dict = {}
    egress_map_dict['out-map-1'] = EgressMap(OUT_MAP_1_DICT)
    egress_map_dict['out-map-2'] = EgressMap(OUT_MAP_2_DICT)
    if_type = 'bond_member'
    if_dict = SIAD_BONDED_IF_MEMBER_DICT
    with pytest.raises(MissingBondGroupError):
        Interface(if_type, if_dict, QOS_POLICY_DICT, ingress_map_dict,
                  egress_map_dict)


def test_compare_bond_member_interface():
    """
    Test the comparison between two Interface objects of 'bond_member' type.
    Two 'bond_member' Interface objects with distinct policies in the
    bonding group are not equal.
    """

    bond_pol_1 = {
        'tagnode': 'dp0bond1',
        'vyatta-interfaces-bonding-switch-v1:switch-group': {
            'port-parameters': {
                'vyatta-interfaces-switch-policy-v1:policy': {
                    'vyatta-policy-qos-v1:qos': 'policy-1'
                }
            }
        }
    }

    bond_pol_2 = {
        'tagnode': 'dp0bond1',
        'vyatta-interfaces-bonding-switch-v1:switch-group': {
            'port-parameters': {
                'vyatta-interfaces-switch-policy-v1:policy': {
                    'vyatta-policy-qos-v1:qos': 'policy-2'
                }
            }
        }
    }

    if1 = Interface('bond_member', SIAD_BONDED_IF_MEMBER_DICT, QOS_POLICY_DICT,
                    {}, {}, bond_dict=bond_pol_1)
    if2 = Interface('bond_member', SIAD_BONDED_IF_MEMBER_DICT, QOS_POLICY_DICT,
                    {}, {}, bond_dict=bond_pol_2)
    assert if1 != if2
