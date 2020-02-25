#!/usr/bin/env python3

# Copyright (c) 2019-2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the interface.py module.
"""

import pytest

from vyatta_policy_qos_vci.ingress_map import IngressMap
from vyatta_policy_qos_vci.interface import Interface
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
                "vyatta-policy-qos-v1:ingress-map": "in-map-1"
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
                                "vyatta-policy-qos-v1:ingress-map": "in-map-2"
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
        ('dataplane', VM_IF_DICT),
        # expected_data
        [
            # Vyatta VM trunk commands
            'qos 1 port subports 1 pipes 1 profiles 1 overhead 24 ql_packets',
            'qos 1 subport 0 rate 125000000 msec 4 period 40',
            'qos 1 subport 0 queue 0 percent 100 msec 4',
            'qos 1 param subport 0 0 limit packets 64',
            'qos 1 subport 0 queue 1 percent 100 msec 4',
            'qos 1 param subport 0 1 limit packets 64',
            'qos 1 subport 0 queue 2 percent 100 msec 4',
            'qos 1 param subport 0 2 limit packets 64',
            'qos 1 subport 0 queue 3 percent 100 msec 4',
            'qos 1 param subport 0 3 limit packets 64',
            'qos 1 vlan 0 0',
            'qos 1 profile 0 percent 100 msec 4 period 10',
            'qos 1 profile 0 queue 0 percent 100 msec 4',
            'qos 1 profile 0 queue 1 percent 100 msec 4',
            'qos 1 profile 0 queue 2 percent 100 msec 4',
            'qos 1 profile 0 queue 3 percent 100 msec 4',
            'qos 1 pipe 0 0 0',
            'qos 1 enable'
        ]
    ),
    (
        # test_input
        ('dataplane', VM_VLAN_DICT),
        # expected_data
        [
            # Vyatta VM trunk and vlan commands
            "qos 1 port subports 2 pipes 1 profiles 2 overhead 24 ql_packets",
            "qos 1 subport 0 rate 125000000 msec 4 period 40",
            "qos 1 subport 0 queue 0 percent 100 msec 4",
            "qos 1 param subport 0 0 limit packets 64",
            "qos 1 subport 0 queue 1 percent 100 msec 4",
            "qos 1 param subport 0 1 limit packets 64",
            "qos 1 subport 0 queue 2 percent 100 msec 4",
            "qos 1 param subport 0 2 limit packets 64",
            "qos 1 subport 0 queue 3 percent 100 msec 4",
            "qos 1 param subport 0 3 limit packets 64",
            "qos 1 vlan 0 0",
            "qos 1 profile 0 percent 100 msec 4 period 10",
            "qos 1 profile 0 queue 0 percent 100 msec 4",
            "qos 1 profile 0 queue 1 percent 100 msec 4",
            "qos 1 profile 0 queue 2 percent 100 msec 4",
            "qos 1 profile 0 queue 3 percent 100 msec 4",
            "qos 1 pipe 0 0 0",
            "qos 1 subport 1 rate 250000000 msec 4 period 40",
            "qos 1 subport 1 queue 0 percent 100 msec 4",
            "qos 1 param subport 1 0 limit packets 64",
            "qos 1 subport 1 queue 1 percent 100 msec 4",
            "qos 1 param subport 1 1 limit packets 64",
            "qos 1 subport 1 queue 2 percent 100 msec 4",
            "qos 1 param subport 1 2 limit packets 64",
            "qos 1 subport 1 queue 3 percent 100 msec 4",
            "qos 1 param subport 1 3 limit packets 64",
            "qos 1 vlan 10 1",
            "qos 1 profile 1 percent 100 msec 4 period 10",
            "qos 1 profile 1 queue 0 percent 100 msec 4",
            "qos 1 profile 1 queue 1 percent 100 msec 4",
            "qos 1 profile 1 queue 2 percent 100 msec 4",
            "qos 1 profile 1 queue 3 percent 100 msec 4",
            "qos 1 pipe 1 0 1",
            "qos 1 enable"
        ]
    ),
    (
        # test_input
        ('dataplane', SIAD_IF_DICT),
        # expected_data
        [
            # SIAD commands
            # During unit-test 'limit packets' commands are issued
            'qos 1 port subports 1 pipes 1 profiles 1 overhead 6 ql_packets',
            'qos 1 subport 0 rate 375000000 size 16000 period 40',
            'qos 1 subport 0 queue 0 percent 100 msec 4',
            'qos 1 param subport 0 0 limit packets 64',
            'qos 1 subport 0 queue 1 percent 100 msec 4',
            'qos 1 param subport 0 1 limit packets 64',
            'qos 1 subport 0 queue 2 percent 100 msec 4',
            'qos 1 param subport 0 2 limit packets 64',
            'qos 1 subport 0 queue 3 percent 100 msec 4',
            'qos 1 param subport 0 3 limit packets 64',
            'qos 1 vlan 0 0',
            'qos 1 profile 0 percent 100 size 16000 period 10',
            'qos 1 profile 0 queue 0 percent 100 msec 4',
            'qos 1 profile 0 queue 1 percent 100 msec 4',
            'qos 1 profile 0 queue 2 percent 100 msec 4',
            'qos 1 profile 0 queue 3 percent 100 msec 4',
            'qos 1 pipe 0 0 0',
            'qos 1 enable'
        ]
    ),
    (
        # test_input
        ('dataplane', SIAD_VLAN_DICT),
        # expected_data
        [
            # SIAD trunk and vlan commands
            # During unit-test 'limit packets' commands are issued
            "qos 1 port subports 3 pipes 1 profiles 3 overhead 6 ql_packets",
            "qos 1 subport 0 rate 375000000 size 16000 period 40",
            "qos 1 subport 0 queue 0 percent 100 msec 4",
            "qos 1 param subport 0 0 limit packets 64",
            "qos 1 subport 0 queue 1 percent 100 msec 4",
            "qos 1 param subport 0 1 limit packets 64",
            "qos 1 subport 0 queue 2 percent 100 msec 4",
            "qos 1 param subport 0 2 limit packets 64",
            "qos 1 subport 0 queue 3 percent 100 msec 4",
            "qos 1 param subport 0 3 limit packets 64",
            "qos 1 vlan 0 0",
            "qos 1 profile 0 percent 100 size 16000 period 10",
            "qos 1 profile 0 queue 0 percent 100 msec 4",
            "qos 1 profile 0 queue 1 percent 100 msec 4",
            "qos 1 profile 0 queue 2 percent 100 msec 4",
            "qos 1 profile 0 queue 3 percent 100 msec 4",
            "qos 1 pipe 0 0 0",
            "qos 1 subport 1 rate 750000000 size 32000 period 40",
            "qos 1 subport 1 queue 0 percent 100 msec 4",
            "qos 1 param subport 1 0 limit packets 64",
            "qos 1 subport 1 queue 1 percent 100 msec 4",
            "qos 1 param subport 1 1 limit packets 64",
            "qos 1 subport 1 queue 2 percent 100 msec 4",
            "qos 1 param subport 1 2 limit packets 64",
            "qos 1 subport 1 queue 3 percent 100 msec 4",
            "qos 1 param subport 1 3 limit packets 64",
            "qos 1 vlan 10 1",
            "qos 1 profile 1 percent 100 size 32000 period 10",
            "qos 1 profile 1 queue 0 percent 100 msec 4",
            "qos 1 profile 1 queue 1 percent 100 msec 4",
            "qos 1 profile 1 queue 2 percent 100 msec 4",
            "qos 1 profile 1 queue 3 percent 100 msec 4",
            "qos 1 pipe 1 0 1",
            "qos 1 subport 2 rate 1500000000 msec 100 period 40",
            "qos 1 subport 2 queue 0 percent 100 msec 4",
            "qos 1 param subport 2 0 limit packets 64",
            "qos 1 subport 2 queue 1 percent 100 msec 4",
            "qos 1 param subport 2 1 limit packets 64",
            "qos 1 subport 2 queue 2 percent 100 msec 4",
            "qos 1 param subport 2 2 limit packets 64",
            "qos 1 subport 2 queue 3 percent 100 msec 4",
            "qos 1 param subport 2 3 limit packets 64",
            "qos 1 vlan 20 2",
            "qos 1 profile 2 percent 100 msec 200 period 10",
            "qos 1 profile 2 queue 0 percent 100 msec 4",
            "qos 1 profile 2 queue 1 percent 100 msec 4",
            "qos 1 profile 2 queue 2 percent 100 msec 4",
            "qos 1 profile 2 queue 3 percent 100 msec 4",
            "qos 1 pipe 2 0 2",
            "qos 1 enable"
        ]
    ),
    (
        # test_input
        ('bonding', VM_BONDED_IF_DICT),
        # expected_data
        [
            # Bonded interface trunk commands
            "qos 1 port subports 1 pipes 1 profiles 1 overhead 24 ql_packets",
            "qos 1 subport 0 rate 125000000 msec 4 period 40",
            "qos 1 subport 0 queue 0 percent 100 msec 4",
            "qos 1 param subport 0 0 limit packets 64",
            "qos 1 subport 0 queue 1 percent 100 msec 4",
            "qos 1 param subport 0 1 limit packets 64",
            "qos 1 subport 0 queue 2 percent 100 msec 4",
            "qos 1 param subport 0 2 limit packets 64",
            "qos 1 subport 0 queue 3 percent 100 msec 4",
            "qos 1 param subport 0 3 limit packets 64",
            "qos 1 vlan 0 0",
            "qos 1 profile 0 percent 100 msec 4 period 10",
            "qos 1 profile 0 queue 0 percent 100 msec 4",
            "qos 1 profile 0 queue 1 percent 100 msec 4",
            "qos 1 profile 0 queue 2 percent 100 msec 4",
            "qos 1 profile 0 queue 3 percent 100 msec 4",
            "qos 1 pipe 0 0 0",
            "qos 1 enable"
        ]
    ),
    (
        # test_input
        ('bonding', VM_BONDED_VLAN_DICT),
        # expected_data
        [
            # Bonded interface trunk and vlan commands
            "qos 1 port subports 2 pipes 1 profiles 2 overhead 24 ql_packets",
            "qos 1 subport 0 rate 125000000 msec 4 period 40",
            "qos 1 subport 0 queue 0 percent 100 msec 4",
            "qos 1 param subport 0 0 limit packets 64",
            "qos 1 subport 0 queue 1 percent 100 msec 4",
            "qos 1 param subport 0 1 limit packets 64",
            "qos 1 subport 0 queue 2 percent 100 msec 4",
            "qos 1 param subport 0 2 limit packets 64",
            "qos 1 subport 0 queue 3 percent 100 msec 4",
            "qos 1 param subport 0 3 limit packets 64",
            "qos 1 vlan 0 0",
            "qos 1 profile 0 percent 100 msec 4 period 10",
            "qos 1 profile 0 queue 0 percent 100 msec 4",
            "qos 1 profile 0 queue 1 percent 100 msec 4",
            "qos 1 profile 0 queue 2 percent 100 msec 4",
            "qos 1 profile 0 queue 3 percent 100 msec 4",
            "qos 1 pipe 0 0 0",
            "qos 1 subport 1 rate 250000000 msec 4 period 40",
            "qos 1 subport 1 queue 0 percent 100 msec 4",
            "qos 1 param subport 1 0 limit packets 64",
            "qos 1 subport 1 queue 1 percent 100 msec 4",
            "qos 1 param subport 1 1 limit packets 64",
            "qos 1 subport 1 queue 2 percent 100 msec 4",
            "qos 1 param subport 1 2 limit packets 64",
            "qos 1 subport 1 queue 3 percent 100 msec 4",
            "qos 1 param subport 1 3 limit packets 64",
            "qos 1 vlan 10 1",
            "qos 1 profile 1 percent 100 msec 4 period 10",
            "qos 1 profile 1 queue 0 percent 100 msec 4",
            "qos 1 profile 1 queue 1 percent 100 msec 4",
            "qos 1 profile 1 queue 2 percent 100 msec 4",
            "qos 1 profile 1 queue 3 percent 100 msec 4",
            "qos 1 pipe 1 0 1",
            "qos 1 enable"
        ]
    ),
    (
        # test_input
        ('vhost', VNF_VHOST_IF_DICT),
        # expected_data
        [
            # vhost interface trunk commands
            "qos 1 port subports 1 pipes 1 profiles 1 overhead 24 ql_packets",
            "qos 1 subport 0 rate 125000000 msec 4 period 40",
            "qos 1 subport 0 queue 0 percent 100 msec 4",
            "qos 1 param subport 0 0 limit packets 64",
            "qos 1 subport 0 queue 1 percent 100 msec 4",
            "qos 1 param subport 0 1 limit packets 64",
            "qos 1 subport 0 queue 2 percent 100 msec 4",
            "qos 1 param subport 0 2 limit packets 64",
            "qos 1 subport 0 queue 3 percent 100 msec 4",
            "qos 1 param subport 0 3 limit packets 64",
            "qos 1 vlan 0 0",
            "qos 1 profile 0 percent 100 msec 4 period 10",
            "qos 1 profile 0 queue 0 percent 100 msec 4",
            "qos 1 profile 0 queue 1 percent 100 msec 4",
            "qos 1 profile 0 queue 2 percent 100 msec 4",
            "qos 1 profile 0 queue 3 percent 100 msec 4",
            "qos 1 pipe 0 0 0",
            "qos 1 enable"
        ]
    ),
    (
        # test_input
        ('vhost', VNF_VHOST_VLAN_DICT),
        # expected_data
        [
            # vhost interface trunk and vlan commands
            "qos 1 port subports 2 pipes 1 profiles 2 overhead 24 ql_packets",
            "qos 1 subport 0 rate 125000000 msec 4 period 40",
            "qos 1 subport 0 queue 0 percent 100 msec 4",
            "qos 1 param subport 0 0 limit packets 64",
            "qos 1 subport 0 queue 1 percent 100 msec 4",
            "qos 1 param subport 0 1 limit packets 64",
            "qos 1 subport 0 queue 2 percent 100 msec 4",
            "qos 1 param subport 0 2 limit packets 64",
            "qos 1 subport 0 queue 3 percent 100 msec 4",
            "qos 1 param subport 0 3 limit packets 64",
            "qos 1 vlan 0 0",
            "qos 1 profile 0 percent 100 msec 4 period 10",
            "qos 1 profile 0 queue 0 percent 100 msec 4",
            "qos 1 profile 0 queue 1 percent 100 msec 4",
            "qos 1 profile 0 queue 2 percent 100 msec 4",
            "qos 1 profile 0 queue 3 percent 100 msec 4",
            "qos 1 pipe 0 0 0",
            "qos 1 subport 1 rate 250000000 msec 4 period 40",
            "qos 1 subport 1 queue 0 percent 100 msec 4",
            "qos 1 param subport 1 0 limit packets 64",
            "qos 1 subport 1 queue 1 percent 100 msec 4",
            "qos 1 param subport 1 1 limit packets 64",
            "qos 1 subport 1 queue 2 percent 100 msec 4",
            "qos 1 param subport 1 2 limit packets 64",
            "qos 1 subport 1 queue 3 percent 100 msec 4",
            "qos 1 param subport 1 3 limit packets 64",
            "qos 1 vlan 10 1",
            "qos 1 profile 1 percent 100 msec 4 period 10",
            "qos 1 profile 1 queue 0 percent 100 msec 4",
            "qos 1 profile 1 queue 1 percent 100 msec 4",
            "qos 1 profile 1 queue 2 percent 100 msec 4",
            "qos 1 profile 1 queue 3 percent 100 msec 4",
            "qos 1 pipe 1 0 1",
            "qos 1 enable"
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

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_interface(test_input, expected_result):
    """ Unit-test the interface class with simple configs """
    ingress_map_dict = {}
    ingress_map_dict['in-map-1'] = IngressMap(IN_MAP_1_DICT)
    ingress_map_dict['in-map-2'] = IngressMap(IN_MAP_2_DICT)
    if_type, if_dict = test_input
    interface = Interface(if_type, if_dict, QOS_POLICY_DICT, ingress_map_dict)

    assert interface is not None
    assert interface.commands() == expected_result
