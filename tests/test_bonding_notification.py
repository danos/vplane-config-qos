#!/usr/bin/env python3

# Copyright (c) 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the LAG membership change notification.
"""

from unittest.mock import Mock, MagicMock, call

import pytest

from vyatta_policy_qos_vci.provisioner import Provisioner
from vyatta_policy_qos_vci.bond_membership import BondMembership

# python doesn't define null, but it is valid JSON
null = None

TEST_DATA = [
    # Test: Add new LAG member
    (
        # test_input - configuration JSON file contents
        {
            "vyatta-interfaces-v1:interfaces": {
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
        },
        # test input - current LAG membership state
        {
            'vyatta-interfaces-bonding-v1:bond-groups': [
                {
                    'bond-group': 'dp0bond1',
                    'bond-members': ['dp0xe4']
                }
            ]
        },
        # test input - new LAG membership state from notification
        {
            'vyatta-interfaces-bonding-v1:bond-groups': [
                {
                    'bond-group': 'dp0bond1',
                    'bond-members': ['dp0xe3', 'dp0xe4']
                }
            ]
        },
        # expected_result
        [
            (
                'qos dp0xe3 qos dp0xe3 port subports 1 pipes 1 profiles 1 overhead 24 ql_packets',
                'qos dp0xe3 port subports 1 pipes 1 profiles 1 overhead 24 ql_packets',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 subport 0 auto size 16000 period 40000',
                'qos dp0xe3 subport 0 auto size 16000 period 40000',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 subport 0 queue 0 percent 100 msec 4',
                'qos dp0xe3 subport 0 queue 0 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 param subport 0 0 limit packets 64',
                'qos dp0xe3 param subport 0 0 limit packets 64',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 subport 0 queue 1 percent 100 msec 4',
                'qos dp0xe3 subport 0 queue 1 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 param subport 0 1 limit packets 64',
                'qos dp0xe3 param subport 0 1 limit packets 64',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 subport 0 queue 2 percent 100 msec 4',
                'qos dp0xe3 subport 0 queue 2 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 param subport 0 2 limit packets 64',
                'qos dp0xe3 param subport 0 2 limit packets 64',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 subport 0 queue 3 percent 100 msec 4',
                'qos dp0xe3 subport 0 queue 3 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 param subport 0 3 limit packets 64',
                'qos dp0xe3 param subport 0 3 limit packets 64',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 vlan 0 0',
                'qos dp0xe3 vlan 0 0',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 0 rate 25000000 size 16000 period 10000',
                'qos dp0xe3 profile 0 rate 25000000 size 16000 period 10000',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 0 queue 0 percent 100 msec 4',
                'qos dp0xe3 profile 0 queue 0 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 0 queue 1 percent 100 msec 4',
                'qos dp0xe3 profile 0 queue 1 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 0 queue 2 percent 100 msec 4',
                'qos dp0xe3 profile 0 queue 2 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 0 queue 3 percent 100 msec 4',
                'qos dp0xe3 profile 0 queue 3 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 pipe 0 0 0',
                'qos dp0xe3 pipe 0 0 0',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 enable',
                'qos dp0xe3 enable',
                'dp0xe3',
                'SET'
            ),
            (
                'qos commit',
                'qos commit',
                'ALL',
                'SET'
            )
        ]
    ),

    # Test: Delete LAG member
    (
        # test_input - configuration JSON file contents
        {
            "vyatta-interfaces-v1:interfaces": {
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
        },
        # test input - current LAG membership state
        {
            'vyatta-interfaces-bonding-v1:bond-groups': [
                {
                    'bond-group': 'dp0bond1',
                    'bond-members': ['dp0xe3', 'dp0xe4']
                }
            ]
        },
        # test input - new LAG membership state from notification
        {
            'vyatta-interfaces-bonding-v1:bond-groups': [
                {
                    'bond-group': 'dp0bond1',
                    'bond-members': ['dp0xe4']
                }
            ]
        },
        # expected_result
        [
            (
                'qos dp0xe3',
                'qos dp0xe3 disable',
                'dp0xe3',
                'DELETE'
            ),
            (
                'qos commit',
                'qos commit',
                'ALL',
                'SET'
            )
        ]
    ),

    # Test: Attach QoS to LAG + Delete LAG member + Attach QoS to front-panel port
    (
        # test_input -  configuration JSON file contents
        {
            'vyatta-interfaces-v1:interfaces': {
                'vyatta-interfaces-dataplane-v1:dataplane': [
                    {
                        'tagnode': 'dp0xe3',
                        'vyatta-interfaces-dataplane-switch-v1:switch-group': {
                            'port-parameters': {
                                'vyatta-interfaces-switch-policy-v1:policy': {
                                    'vyatta-policy-qos-v1:qos': 'policy-2'
                                }
                            }
                        }
                    }
                ],
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
                        },
                        {
                            'id': 'policy-2',
                            'shaper': {
                                'bandwidth': 'auto',
                                'burst': 16000,
                                'default': 'profile-2',
                                'frame-overhead': '24'
                            }
                        }
                    ],
                    'profile': [
                        {
                            'bandwidth': '200Mbit',
                            'burst': 16000,
                            'id': 'profile-1'
                        },
                        {
                            'bandwidth': '300Mbit',
                            'burst': 16000,
                            'id': 'profile-2'
                        }
                    ]
                }
            }
        },
        # test input - current LAG membership state
        {
            'vyatta-interfaces-bonding-v1:bond-groups': [
                {
                    'bond-group': 'dp0bond1',
                    'bond-members': ['dp0xe3', 'dp0xe4']
                }
            ]
        },
        # test input - new LAG membership state from notification
        {
            'vyatta-interfaces-bonding-v1:bond-groups': [
                {
                    'bond-group': 'dp0bond1',
                    'bond-members': ['dp0xe4']
                }
            ]
        },
        # expected_result
        [
            # Detach LAG QoS from port:
            (
                'qos dp0xe3',
                'qos dp0xe3 disable',
                'dp0xe3',
                'DELETE'
            ),
            # Attach port QoS to port:
            (
                'qos dp0xe3 qos dp0xe3 port subports 1 pipes 1 profiles 2 overhead 24 ql_packets',
                'qos dp0xe3 port subports 1 pipes 1 profiles 2 overhead 24 ql_packets',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 subport 0 auto size 16000 period 40000',
                'qos dp0xe3 subport 0 auto size 16000 period 40000',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 subport 0 queue 0 percent 100 msec 4',
                'qos dp0xe3 subport 0 queue 0 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 param subport 0 0 limit packets 64',
                'qos dp0xe3 param subport 0 0 limit packets 64',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 subport 0 queue 1 percent 100 msec 4',
                'qos dp0xe3 subport 0 queue 1 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 param subport 0 1 limit packets 64',
                'qos dp0xe3 param subport 0 1 limit packets 64',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 subport 0 queue 2 percent 100 msec 4',
                'qos dp0xe3 subport 0 queue 2 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 param subport 0 2 limit packets 64',
                'qos dp0xe3 param subport 0 2 limit packets 64',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 subport 0 queue 3 percent 100 msec 4',
                'qos dp0xe3 subport 0 queue 3 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 param subport 0 3 limit packets 64',
                'qos dp0xe3 param subport 0 3 limit packets 64',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 vlan 0 0',
                'qos dp0xe3 vlan 0 0',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 0 rate 25000000 size 16000 period 10000',
                'qos dp0xe3 profile 0 rate 25000000 size 16000 period 10000',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 0 queue 0 percent 100 msec 4',
                'qos dp0xe3 profile 0 queue 0 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 0 queue 1 percent 100 msec 4',
                'qos dp0xe3 profile 0 queue 1 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 0 queue 2 percent 100 msec 4',
                'qos dp0xe3 profile 0 queue 2 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 0 queue 3 percent 100 msec 4',
                'qos dp0xe3 profile 0 queue 3 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 1 rate 37500000 size 16000 period 10000',
                'qos dp0xe3 profile 1 rate 37500000 size 16000 period 10000',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 1 queue 0 percent 100 msec 4',
                'qos dp0xe3 profile 1 queue 0 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 1 queue 1 percent 100 msec 4',
                'qos dp0xe3 profile 1 queue 1 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 1 queue 2 percent 100 msec 4',
                'qos dp0xe3 profile 1 queue 2 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 profile 1 queue 3 percent 100 msec 4',
                'qos dp0xe3 profile 1 queue 3 percent 100 msec 4',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 pipe 0 0 1',
                'qos dp0xe3 pipe 0 0 1',
                'dp0xe3',
                'SET'
            ),
            (
                'qos dp0xe3 qos dp0xe3 enable',
                'qos dp0xe3 enable',
                'dp0xe3',
                'SET'
            ),
            (
                'qos commit',
                'qos commit',
                'ALL',
                'SET'
            )
        ]
    )
]

@pytest.mark.parametrize("config, cur_membership, notification,\
    expected_result", TEST_DATA)
def test_lag_membership_ntfy(config, cur_membership, notification,
                             expected_result):
    # Mock up a dataplane context manager
    mock_dataplane = MagicMock()
    mock_dataplane.__enter__.return_value = mock_dataplane

    # Mock up a controller class
    attrs = {
        'get_dataplanes.return_value': [mock_dataplane],
        'store.return_value': 0
    }
    ctrl = Mock(**attrs)

    # Create BondMembership objects with the current membership state and the
    # new state received from a VCI notification
    cur_membership_obj = BondMembership(notification=cur_membership)
    ntfy_membership_obj = BondMembership(notification=notification)

    # prov.commands writes the QoS config commands to the mocked controller
    prov = Provisioner(config, config, cur_bond_membership=cur_membership_obj,
                       bonding_ntfy=ntfy_membership_obj)
    prov.commands(ctrl)

    # The tests for QoS on LAG contain a few corner cases where the number
    # of cstore commands and their order is important.
    # Ensure that the mock has been called exactly the same number of times
    # it is expected (no calls beyond the ones expected) and in the correct
    # order
    assert ctrl.store.call_count == len(expected_result)
    calls = []
    for call_args in expected_result:
        (path, cmd, intf, oper) = call_args
        calls.append(call(path, cmd, intf, oper))
    ctrl.store.assert_has_calls(calls, any_order=False)
