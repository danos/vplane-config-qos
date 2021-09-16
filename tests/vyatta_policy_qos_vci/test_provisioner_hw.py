#!/usr/bin/env python3

# Copyright (c) 2019-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the provisioner.py module.
"""

from unittest.mock import Mock, MagicMock

import pytest

from vyatta_policy_qos_vci.provisioner import Provisioner

# Sanity Hardware Qos Configuration
#
# The following JSON configuration and expected results represents an specific
# example of a complex QoS configuration targetted for a particular hardware
# platform.  As such this configuration or its expected results should not be
# changed without the express permission of the vplane-config-qos package
# maintainer
#
# It is separated from other tests as the wred_map.byte_limits method is mocked
# to emulate the test running on a hardware platform.

HW_SANITY_TEST_DATA = [
    (
        # fakes
        # pylint: disable=no-member
        pytest.lazy_fixture("byte_limits_faker"),
        # old config
        {},
        # new config
        {
            'vyatta-interfaces-v1:interfaces': {
                'vyatta-interfaces-dataplane-v1:dataplane': [
                    {
                        'tagnode': 'dp0xe6',
                        'vyatta-interfaces-dataplane-switch-v1:switch-group': {
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
                    'mark-map': [
                        {
                            'id': 'vlan-pcp-marking',
                            'dscp-group': [
                                {
                                    'group-name': 'default-high',
                                    'pcp-mark': 2
                                }, {
                                    'group-name': 'default-low',
                                    'pcp-mark': 1
                                }, {
                                    'group-name': 'priority-high',
                                    'pcp-mark': 4
                                }, {
                                    'group-name': 'priority-low',
                                    'pcp-mark': 3
                                }, {
                                    'group-name': 'real-time',
                                    'pcp-mark': 5
                                }, {
                                    'group-name': 'synch',
                                    'pcp-mark': 7
                                }
                            ]
                        }
                    ],
                    'name': [
                        {
                            'id': 'policy-1',
                            'shaper': {
                                'bandwidth': 'auto',
                                'burst': 16000,
                                'default': 'profile-1',
                                'frame-overhead': '0',
                                'mark-map': 'vlan-pcp-marking',
                                'profile': [
                                    {
                                        'id': 'profile-1',
                                        'bandwidth': '1Gbit',
                                        'burst': 16000,
                                        'map': {
                                            'dscp-group': [
                                                {
                                                    'group-name': 'default-high',
                                                    'to': 9
                                                }, {
                                                    'group-name': 'default-low',
                                                    'to': 9
                                                }, {
                                                    'group-name': 'priority-high',
                                                    'to': 8
                                                }, {
                                                    'group-name': 'priority-low',
                                                    'to': 8
                                                }, {
                                                    'group-name': 'real-time',
                                                    'to': 4
                                                }, {
                                                    'group-name': 'synch',
                                                    'to': 0
                                                }
                                            ]
                                        },
                                        'queue': [
                                            {
                                                'id': 0,
                                                'traffic-class': 0,
                                                'weight': 1
                                            }, {
                                                'id': 2,
                                                'priority-local': [None],
                                                'traffic-class': 1,
                                                'weight': 1
                                            }, {
                                                'id': 4,
                                                'traffic-class': 2,
                                                'weight': 1
                                            }, {
                                                'id': 8,
                                                'traffic-class': 3,
                                                'weight': 60,
                                                'wred-map-bytes': {
                                                    'dscp-group': [
                                                        {
                                                            'group-name': 'priority-high',
                                                            'mark-probability': 10,
                                                            'max-threshold': '4375000',
                                                            'min-threshold': '3125000'
                                                        }, {
                                                            'group-name': 'priority-low',
                                                            'mark-probability': 10,
                                                            'max-threshold': '6250000',
                                                            'min-threshold': '5625000'
                                                        }
                                                    ],
                                                    'filter-weight': 6
                                                }
                                            }, {
                                                'id': 9,
                                                'traffic-class': 3,
                                                'weight': 40,
                                                'wred-map-bytes': {
                                                    'dscp-group': [
                                                        {
                                                            'group-name': 'default-high',
                                                            'mark-probability': 10,
                                                            'max-threshold': '4375000',
                                                            'min-threshold': '3125000'
                                                        }, {
                                                            'group-name': 'default-low',
                                                            'mark-probability': 10,
                                                            'max-threshold': '6250000',
                                                            'min-threshold': '5625000'
                                                        }
                                                    ],
                                                    'filter-weight': 8
                                                }
                                            }
                                        ],
                                        'traffic-class': [
                                            {
                                                'id': 0,
                                                'bandwidth': '40%'
                                            }, {
                                                'id': 2,
                                                'bandwidth': '40%'
                                            }
                                        ]
                                    }
                                ],
                                'traffic-class': [
                                    {
                                        'id': 0,
                                        'bandwidth': '100%',
                                        'queue-limit-bytes': '125000'
                                    }, {
                                        'id': 1,
                                        'bandwidth': '100%',
                                        'queue-limit-bytes': '125000'
                                    }, {
                                        'id': 2,
                                        'bandwidth': '100%',
                                        'queue-limit-bytes': '625000'
                                    }, {
                                        'id': 3,
                                        'bandwidth': '100%',
                                        'queue-limit-bytes': '6250001'
                                    }
                                ]
                            }
                        }
                    ]
                }
            },
            'vyatta-resources-v1:resources': {
                'vyatta-resources-group-misc-v1:group': {
                    'vyatta-resources-dscp-group-v1:dscp-group': [
                        {
                            'group-name': 'default-high',
                            'dscp': [
                                '8', '10', '16', '18'
                            ]
                        }, {
                            'group-name': 'default-low',
                            'dscp': [
                                '0', '1', '2', '3', '4', '5', '6', '7', '9', '11',
                                '12', '13', '14', '15', '17', '19', '20', '21', '22',
                                '23', '41', '42', '43', '44', '45', '49', '50', '51',
                                '52', '53', '54', '55', '57', '58', '59', '60', '61',
                                '62', '63'
                            ]
                        }, {
                            'group-name': 'priority-high',
                            'dscp': [
                                '24', '26', '34'
                            ]
                        }, {
                            'group-name': 'priority-low',
                            'dscp': [
                                '25', '27', '28', '29', '30', '31', '33', '35', '36',
                                '37', '38', '39'
                            ]
                        }, {
                            'group-name': 'real-time',
                            'dscp': [
                                '32', '40', '46', '48'
                            ]
                        }, {
                            'group-name': 'synch',
                            'dscp': [
                                '47', '56'
                            ]
                        }
                    ]
                }
            }
        },
        # expected result
        [
            (
                'qos mark-map vlan-pcp-marking dscp-group default-high',
                'qos global-object-cmd mark-map vlan-pcp-marking dscp-group default-high pcp 2',
                'ALL',
                'SET'
            ),
            (
                'qos mark-map vlan-pcp-marking dscp-group default-low',
                'qos global-object-cmd mark-map vlan-pcp-marking dscp-group default-low pcp 1',
                'ALL',
                'SET'
            ),
            (
                'qos mark-map vlan-pcp-marking dscp-group priority-high',
                'qos global-object-cmd mark-map vlan-pcp-marking dscp-group priority-high pcp 4',
                'ALL',
                'SET'
            ),
            (
                'qos mark-map vlan-pcp-marking dscp-group priority-low',
                'qos global-object-cmd mark-map vlan-pcp-marking dscp-group priority-low pcp 3',
                'ALL',
                'SET'
            ),
            (
                'qos mark-map vlan-pcp-marking dscp-group real-time',
                'qos global-object-cmd mark-map vlan-pcp-marking dscp-group real-time pcp 5',
                'ALL',
                'SET'
            ),
            (
                'qos mark-map vlan-pcp-marking dscp-group synch',
                'qos global-object-cmd mark-map vlan-pcp-marking dscp-group synch pcp 7',
                'ALL',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 port subports 1 pipes 1 profiles 1 overhead 0 ql_bytes',
                'qos dp0xe6 port subports 1 pipes 1 profiles 1 overhead 0 ql_bytes',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 subport 0 auto size 16000 period 40000',
                'qos dp0xe6 subport 0 auto size 16000 period 40000',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 subport 0 queue 0 percent 100 msec 4',
                'qos dp0xe6 subport 0 queue 0 percent 100 msec 4',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 param subport 0 0 limit bytes 125000',
                'qos dp0xe6 param subport 0 0 limit bytes 125000',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 subport 0 queue 1 percent 100 msec 4',
                'qos dp0xe6 subport 0 queue 1 percent 100 msec 4',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 param subport 0 1 limit bytes 125000',
                'qos dp0xe6 param subport 0 1 limit bytes 125000',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 subport 0 queue 3 percent 100 msec 4',
                'qos dp0xe6 subport 0 queue 3 percent 100 msec 4',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 param subport 0 2 limit bytes 625000',
                'qos dp0xe6 param subport 0 2 limit bytes 625000',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 param subport 0 3 limit bytes 6250001',
                'qos dp0xe6 param subport 0 3 limit bytes 6250001',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 subport 0 mark-map vlan-pcp-marking',
                'qos dp0xe6 subport 0 mark-map vlan-pcp-marking',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 subport 0 queue 2 percent 100 msec 4',
                'qos dp0xe6 subport 0 queue 2 percent 100 msec 4',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 vlan 0 0',
                'qos dp0xe6 vlan 0 0',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 rate 125000000 size 16000 period 10000',
                'qos dp0xe6 profile 0 rate 125000000 size 16000 period 10000',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0 percent 40 msec 4',
                'qos dp0xe6 profile 0 queue 0 percent 40 msec 4',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 1 percent 100 msec 4',
                'qos dp0xe6 profile 0 queue 1 percent 100 msec 4',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 2 percent 40 msec 4',
                'qos dp0xe6 profile 0 queue 2 percent 40 msec 4',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 3 percent 100 msec 4',
                'qos dp0xe6 profile 0 queue 3 percent 100 msec 4',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 dscp-group default-high 0x7',
                'qos dp0xe6 profile 0 dscp-group default-high 0x7',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 dscp-group default-low 0x27',
                'qos dp0xe6 profile 0 dscp-group default-low 0x27',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 dscp-group priority-high 0x3',
                'qos dp0xe6 profile 0 dscp-group priority-high 0x3',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 dscp-group priority-low 0x23',
                'qos dp0xe6 profile 0 dscp-group priority-low 0x23',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 dscp-group real-time 0x2',
                'qos dp0xe6 profile 0 dscp-group real-time 0x2',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 dscp-group synch 0x0',
                'qos dp0xe6 profile 0 dscp-group synch 0x0',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0 wrr-weight 1 0',
                'qos dp0xe6 profile 0 queue 0 wrr-weight 1 0',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0x5 wrr-weight 1 2 prio-loc',
                'qos dp0xe6 profile 0 queue 0x5 wrr-weight 1 2 prio-loc',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0x2 wrr-weight 1 4',
                'qos dp0xe6 profile 0 queue 0x2 wrr-weight 1 4',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0x3 wrr-weight 60 8',
                'qos dp0xe6 profile 0 queue 0x3 wrr-weight 60 8',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0x3 dscp-group '
                'priority-high bytes 4375000 3125000 10',
                'qos dp0xe6 profile 0 queue 0x3 dscp-group priority-high bytes 4375000 3125000 10',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0x3 dscp-group '
                'priority-low bytes 6250000 5625000 10',
                'qos dp0xe6 profile 0 queue 0x3 dscp-group priority-low bytes 6250000 5625000 10',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0x3 wred-weight 6',
                'qos dp0xe6 profile 0 queue 0x3 wred-weight 6',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0x7 wrr-weight 40 9',
                'qos dp0xe6 profile 0 queue 0x7 wrr-weight 40 9',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0x7 dscp-group '
                'default-high bytes 4375000 3125000 10',
                'qos dp0xe6 profile 0 queue 0x7 dscp-group default-high bytes 4375000 3125000 10',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0x7 dscp-group '
                'default-low bytes 6250000 5625000 10',
                'qos dp0xe6 profile 0 queue 0x7 dscp-group default-low bytes 6250000 5625000 10',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 profile 0 queue 0x7 wred-weight 8',
                'qos dp0xe6 profile 0 queue 0x7 wred-weight 8',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 pipe 0 0 0',
                'qos dp0xe6 pipe 0 0 0',
                'dp0xe6',
                'SET'
            ),
            (
                'qos dp0xe6 qos dp0xe6 enable',
                'qos dp0xe6 enable',
                'dp0xe6',
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


@pytest.fixture
def byte_limits_faker(monkeypatch):
    """
    Overwrite the function pointer to byte_limits to pretend that this
    unit-test is running on a hardware platform.
    """
    # pylint: disable=import-outside-toplevel
    import vyatta_policy_qos_vci.interface
    import vyatta_policy_qos_vci.traffic_class_block
    import vyatta_policy_qos_vci.wred_map

    def fake_byte_limits():
        return True

    # byte_limits is called from three different modules, overwrite all of them
    monkeypatch.setattr(vyatta_policy_qos_vci.interface, "byte_limits",
                        fake_byte_limits)
    monkeypatch.setattr(vyatta_policy_qos_vci.traffic_class_block,
                        "byte_limits", fake_byte_limits)
    monkeypatch.setattr(vyatta_policy_qos_vci.wred_map, "byte_limits",
                        fake_byte_limits)


@pytest.mark.parametrize("fakes, old_config, new_config, expected_result",
                         HW_SANITY_TEST_DATA)
# pylint: disable=unused-argument
def test_provisioner_hw(fakes, old_config, new_config, expected_result):
    """ Simple unit-test for the provisioner class on hardware """
    # Mock up a dataplane context manager
    mock_dataplane = MagicMock()
    mock_dataplane.__enter__.return_value = mock_dataplane

    # Mock up a controller class
    attrs = {
        'get_dataplanes.return_value': [mock_dataplane],
        'store.return_value': 0
    }
    ctrl = Mock(**attrs)

    prov = Provisioner(old_config, new_config, cur_bond_membership=None)
    assert prov is not None
    # prov.commands writes the QoS config commands to the mocked controller
    prov.commands(ctrl)

    for call_args in expected_result:
        ctrl.store.assert_any_call(*call_args)
