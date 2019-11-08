#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the interface.py module.
"""

import pytest

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
                "vyatta-policy-qos-v1:qos": "policy-3"
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
                                "vyatta-policy-qos-v1:qos": "policy-5"
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
        VM_IF_DICT,
        # expected_data
        [
            # Vyatta VM trunk commands
            'qos 1 port subports 1 pipes 1 profiles 1 overhead 24',
            'qos 1 subport 0 rate 125000000 size 0 period 40',
            'qos 1 subport 0 queue 0 percent 100 size 0',
            'qos 1 param subport 0 0 limit packets 64',
            'qos 1 subport 0 queue 1 percent 100 size 0',
            'qos 1 param subport 0 1 limit packets 64',
            'qos 1 subport 0 queue 2 percent 100 size 0',
            'qos 1 param subport 0 2 limit packets 64',
            'qos 1 subport 0 queue 3 percent 100 size 0',
            'qos 1 param subport 0 3 limit packets 64',
            'qos 1 vlan 0 0',
            'qos 1 profile 0 percent 100 size 0 period 10',
            'qos 1 profile 0 queue 0 percent 100 size 0',
            'qos 1 profile 0 queue 1 percent 100 size 0',
            'qos 1 profile 0 queue 2 percent 100 size 0',
            'qos 1 profile 0 queue 3 percent 100 size 0',
            'qos 1 pipe 0 0 0',
            'qos 1 enable'
        ]
    ),
    (
        # test_input
        VM_VLAN_DICT,
        # expected_data
        [
            # Vyatta VM trunk and vlan commands
            "qos 1 port subports 2 pipes 1 profiles 2 overhead 24",
            "qos 1 subport 0 rate 125000000 size 0 period 40",
            "qos 1 subport 0 queue 0 percent 100 size 0",
            "qos 1 param subport 0 0 limit packets 64",
            "qos 1 subport 0 queue 1 percent 100 size 0",
            "qos 1 param subport 0 1 limit packets 64",
            "qos 1 subport 0 queue 2 percent 100 size 0",
            "qos 1 param subport 0 2 limit packets 64",
            "qos 1 subport 0 queue 3 percent 100 size 0",
            "qos 1 param subport 0 3 limit packets 64",
            "qos 1 vlan 0 0",
            "qos 1 profile 0 percent 100 size 0 period 10",
            "qos 1 profile 0 queue 0 percent 100 size 0",
            "qos 1 profile 0 queue 1 percent 100 size 0",
            "qos 1 profile 0 queue 2 percent 100 size 0",
            "qos 1 profile 0 queue 3 percent 100 size 0",
            "qos 1 pipe 0 0 0",
            "qos 1 subport 1 rate 250000000 size 0 period 40",
            "qos 1 subport 1 queue 0 percent 100 size 0",
            "qos 1 param subport 1 0 limit packets 64",
            "qos 1 subport 1 queue 1 percent 100 size 0",
            "qos 1 param subport 1 1 limit packets 64",
            "qos 1 subport 1 queue 2 percent 100 size 0",
            "qos 1 param subport 1 2 limit packets 64",
            "qos 1 subport 1 queue 3 percent 100 size 0",
            "qos 1 param subport 1 3 limit packets 64",
            "qos 1 vlan 10 1",
            "qos 1 profile 1 percent 100 size 0 period 10",
            "qos 1 profile 1 queue 0 percent 100 size 0",
            "qos 1 profile 1 queue 1 percent 100 size 0",
            "qos 1 profile 1 queue 2 percent 100 size 0",
            "qos 1 profile 1 queue 3 percent 100 size 0",
            "qos 1 pipe 1 0 1",
            "qos 1 enable"
        ]
    ),
    (
        # test_input
        SIAD_IF_DICT,
        # expected_data
        [
            # SIAD commands
            # During unit-test 'limit packets' commands are issued
            'qos 1 port subports 1 pipes 1 profiles 1 overhead 6',
            'qos 1 subport 0 rate 375000000 size 16000 period 40',
            'qos 1 subport 0 queue 0 percent 100 size 0',
            'qos 1 param subport 0 0 limit packets 64',
            'qos 1 subport 0 queue 1 percent 100 size 0',
            'qos 1 param subport 0 1 limit packets 64',
            'qos 1 subport 0 queue 2 percent 100 size 0',
            'qos 1 param subport 0 2 limit packets 64',
            'qos 1 subport 0 queue 3 percent 100 size 0',
            'qos 1 param subport 0 3 limit packets 64',
            'qos 1 vlan 0 0',
            'qos 1 profile 0 percent 100 size 16000 period 10',
            'qos 1 profile 0 queue 0 percent 100 size 0',
            'qos 1 profile 0 queue 1 percent 100 size 0',
            'qos 1 profile 0 queue 2 percent 100 size 0',
            'qos 1 profile 0 queue 3 percent 100 size 0',
            'qos 1 pipe 0 0 0',
            'qos 1 enable'
        ]
    ),
    (
        # test_input
        SIAD_VLAN_DICT,
        # expected_data
        [
            # SIAD trunk and vlan commands
            # During unit-test 'limit packets' commands are issued
            "qos 1 port subports 3 pipes 1 profiles 3 overhead 6",
            "qos 1 subport 0 rate 375000000 size 16000 period 40",
            "qos 1 subport 0 queue 0 percent 100 size 0",
            "qos 1 param subport 0 0 limit packets 64",
            "qos 1 subport 0 queue 1 percent 100 size 0",
            "qos 1 param subport 0 1 limit packets 64",
            "qos 1 subport 0 queue 2 percent 100 size 0",
            "qos 1 param subport 0 2 limit packets 64",
            "qos 1 subport 0 queue 3 percent 100 size 0",
            "qos 1 param subport 0 3 limit packets 64",
            "qos 1 vlan 0 0",
            "qos 1 profile 0 percent 100 size 16000 period 10",
            "qos 1 profile 0 queue 0 percent 100 size 0",
            "qos 1 profile 0 queue 1 percent 100 size 0",
            "qos 1 profile 0 queue 2 percent 100 size 0",
            "qos 1 profile 0 queue 3 percent 100 size 0",
            "qos 1 pipe 0 0 0",
            "qos 1 subport 1 rate 750000000 size 32000 period 40",
            "qos 1 subport 1 queue 0 percent 100 size 0",
            "qos 1 param subport 1 0 limit packets 64",
            "qos 1 subport 1 queue 1 percent 100 size 0",
            "qos 1 param subport 1 1 limit packets 64",
            "qos 1 subport 1 queue 2 percent 100 size 0",
            "qos 1 param subport 1 2 limit packets 64",
            "qos 1 subport 1 queue 3 percent 100 size 0",
            "qos 1 param subport 1 3 limit packets 64",
            "qos 1 vlan 10 1",
            "qos 1 profile 1 percent 100 size 32000 period 10",
            "qos 1 profile 1 queue 0 percent 100 size 0",
            "qos 1 profile 1 queue 1 percent 100 size 0",
            "qos 1 profile 1 queue 2 percent 100 size 0",
            "qos 1 profile 1 queue 3 percent 100 size 0",
            "qos 1 pipe 1 0 1",
            "qos 1 subport 2 rate 1500000000 msec 100 period 40",
            "qos 1 subport 2 queue 0 percent 100 size 0",
            "qos 1 param subport 2 0 limit packets 64",
            "qos 1 subport 2 queue 1 percent 100 size 0",
            "qos 1 param subport 2 1 limit packets 64",
            "qos 1 subport 2 queue 2 percent 100 size 0",
            "qos 1 param subport 2 2 limit packets 64",
            "qos 1 subport 2 queue 3 percent 100 size 0",
            "qos 1 param subport 2 3 limit packets 64",
            "qos 1 vlan 20 2",
            "qos 1 profile 2 percent 100 msec 200 period 10",
            "qos 1 profile 2 queue 0 percent 100 size 0",
            "qos 1 profile 2 queue 1 percent 100 size 0",
            "qos 1 profile 2 queue 2 percent 100 size 0",
            "qos 1 profile 2 queue 3 percent 100 size 0",
            "qos 1 pipe 2 0 2",
            "qos 1 enable"
        ]
    )
]

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_interface(test_input, expected_result):
    """ Unit-test the interface class with simple configs """
    interface = Interface(test_input, QOS_POLICY_DICT)
    assert interface is not None
    assert interface.commands() == expected_result
