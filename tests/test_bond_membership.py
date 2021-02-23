#!/usr/bin/env python3

# Copyright (c) 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the BondMembership class.
"""

from unittest.mock import MagicMock, patch

from vyatta_policy_qos_vci.bond_membership import BondMembership


@patch('vyatta_policy_qos_vci.bond_membership.subprocess.check_output')
def test_fetch_bond_groups(mock_check_output):
    """
    Tests that _fetch_bond_groups() method can properly retrieve a list of
    bonding groups from the kernel.
    """
    membership = BondMembership()
    assert membership is not None

    # Two bonding groups:

    # Configure the output of the mocked kernel. This is the mocked output for
    # 'ls -1 /sys/class/net'.
    mock_check_output.return_value = b'bp0p0\nbp0p1\ndp0bond1\ndp0bond2\n\
        dp0ce0\ndp0ce1\ndp0p7s0\ndp0xe0\ndp0xe1\ndp0xe10\ndp0xe11\ndp0xe12\n\
        dp0xe13\ndp0xe14\ndp0xe15\ndp0xe16\ndp0xe17\ndp0xe18\ndp0xe19\ndp0xe2\n\
        dp0xe20\ndp0xe21\ndp0xe22\ndp0xe23\ndp0xe24\ndp0xe25\ndp0xe26\n\
        dp0xe27\ndp0xe3\ndp0xe4\ndp0xe5\ndp0xe6\ndp0xe7\ndp0xe8\ndp0xe9\n\
        enp0s20u4u2c2\nlo\nsw0\nsw0.10\nsw0.30\n'

    assert membership._fetch_bond_groups() == ['dp0bond1', 'dp0bond2']

    # No bonding groups:

    mock_check_output.return_value = b'bp0p0\nbp0p1\n\
        dp0ce0\ndp0ce1\ndp0p7s0\ndp0xe0\ndp0xe1\ndp0xe10\ndp0xe11\ndp0xe12\n\
        dp0xe13\ndp0xe14\ndp0xe15\ndp0xe16\ndp0xe17\ndp0xe18\ndp0xe19\ndp0xe2\n\
        dp0xe20\ndp0xe21\ndp0xe22\ndp0xe23\ndp0xe24\ndp0xe25\ndp0xe26\n\
        dp0xe27\ndp0xe3\ndp0xe4\ndp0xe5\ndp0xe6\ndp0xe7\ndp0xe8\ndp0xe9\n\
        enp0s20u4u2c2\nlo\nsw0\nsw0.10\nsw0.30\n'

    assert membership._fetch_bond_groups() == []

@patch('vyatta_policy_qos_vci.bond_membership.subprocess.check_output')
def test_fetch_membership(mock_check_output):
    """
    Tests that _fetch_membership method() can properly retrieve the complete
    LAG membership state from the kernel.
    """
    membership = BondMembership()
    assert membership is not None

    # Bonding group with three members:

    # Configure the return value of the mocked _fetch_bond_groups() method.
    bond_groups = ['dp0bond1']
    membership._fetch_bond_groups = MagicMock(name='_fetch_bond_groups',
        return_value=bond_groups)
    # Configure the output of the mocked kernel. This is the mocked output for
    # 'teamdctl <bond_group> config dump actual'.
    mock_check_output.return_value = b'{\n    "device": "dp0bond1",\n    \
        "link_watch": {\n        "name": "ethtool"\n    },\n    \
        "ports": {\n        "dp0xe25": {},\n        "dp0xe4": {},\n        \
        "dp0xe6": {}\n    },\n    \
        "runner": {\n        "name": "loadbalance",\n        \
        "tx_hash": [\n            "eth",\n            "ipv4",\n            \
        "ipv6"\n        ]\n    }\n}\n'
    expected = {
        'dp0bond1': ['dp0xe25', 'dp0xe4', 'dp0xe6']
    }

    assert membership._fetch_membership() == expected

    # Empty bonding group (no "ports"):

    bond_groups = ['dp0bond1']
    membership._fetch_bond_groups = MagicMock(name='_fetch_bond_groups',
        return_value=bond_groups)
    mock_check_output.return_value = b'{\n    "device": "dp0bond1",\n    \
        "link_watch": {\n        "name": "ethtool"\n    },\n    \
        "runner": {\n        "name": "loadbalance",\n        \
        "tx_hash": [\n            "eth",\n            "ipv4",\n            \
        "ipv6"\n        ]\n    }\n}\n'
    expected = {
        'dp0bond1': []
    }

    assert membership._fetch_membership() == expected

    # Empty bonding group ("ports" is empty):

    bond_groups = ['dp0bond1']
    membership._fetch_bond_groups = MagicMock(name='_fetch_bond_groups',
        return_value=bond_groups)
    mock_check_output.return_value = b'{\n    "device": "dp0bond1",\n    \
        "link_watch": {\n        "name": "ethtool"\n    },\n    \
        "ports": {},\n\
        "runner": {\n        "name": "loadbalance",\n        \
        "tx_hash": [\n            "eth",\n            "ipv4",\n            \
        "ipv6"\n        ]\n    }\n}\n'
    expected = {
        'dp0bond1': []
    }

    assert membership._fetch_membership() == expected

def test_init_state_from_kernel():
    """
    Test BondMembership construction in the case where it has to fetch the
    LAG membership state from the kernel.
    """
    membership = BondMembership()
    assert membership is not None

    # Configure the return value of the mocked _fetch_membership() method.
    return_value = {
        'dp0bond1': ['dp0xe1', 'dp0xe2'],
        'dp0bond2': ['dp0xe3', 'dp0xe4', 'dp0xe5']
    }
    membership._fetch_membership = MagicMock(
        name='_get_membership_from_kernel',
        return_value=return_value)

    membership.refresh()

    expected = {
        'dp0bond1': [
            {
                'tagnode': 'dp0xe1',
                'bond-group': 'dp0bond1'
            },
            {
                'tagnode': 'dp0xe2',
                'bond-group': 'dp0bond1'
            }
        ],
        'dp0bond2': [
            {
                'tagnode': 'dp0xe3',
                'bond-group': 'dp0bond2'
            },
            {
                'tagnode': 'dp0xe4',
                'bond-group': 'dp0bond2'
            },
            {
                'tagnode': 'dp0xe5',
                'bond-group': 'dp0bond2'
            }
        ]
    }

    assert membership.get_membership() == expected
    assert len(membership.get_bond_groups()) == len(expected)
    for expected_bond_group, expected_members in expected.items():
        for expected_member in expected_members:
            found = False
            members = membership.get_members(expected_bond_group)
            for member in members:
                if expected_member['tagnode'] == member['tagnode']:
                    found = True
            assert found is True

def test_init_state_from_notification():
    """
    Test BondMembership construction in the case where the LAG membership
    state was received in a VCI notification from the LAG component.
    """
    notification = {
        'vyatta-interfaces-bonding-v1:bond-groups': [
            {
                'bond-group': 'dp0bond1',
                'bond-members': ['dp0xe1', 'dp0xe2']
            },
            {
                'bond-group': 'dp0bond2',
                'bond-members': ['dp0xe3', 'dp0xe4', 'dp0xe5']
            }
        ]
    }
    membership = BondMembership(notification=notification)

    expected = {
        'dp0bond1': [
            {
                'tagnode': 'dp0xe1',
                'bond-group': 'dp0bond1'
            },
            {
                'tagnode': 'dp0xe2',
                'bond-group': 'dp0bond1'
            }
        ],
        'dp0bond2': [
            {
                'tagnode': 'dp0xe3',
                'bond-group': 'dp0bond2'
            },
            {
                'tagnode': 'dp0xe4',
                'bond-group': 'dp0bond2'
            },
            {
                'tagnode': 'dp0xe5',
                'bond-group': 'dp0bond2'
            }
        ]
    }

    assert membership is not None
    assert membership.get_membership() == expected
