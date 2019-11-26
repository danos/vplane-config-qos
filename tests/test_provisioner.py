#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the dscp.py module.
"""

from unittest.mock import Mock, MagicMock

import pytest

from vyatta_policy_qos_vci.provisioner import Provisioner

# python doesn't define null, but it is valid JSON
null = None

TEST_DATA = [
    (
        # test_input
        {
            "vyatta-interfaces-v1:interfaces": {
                "vyatta-interfaces-dataplane-v1:dataplane": [
                    {
                        "tagnode": "lo",
                        "vyatta-interfaces-dataplane-switch-v1:switch-group": {
                            "port-parameters": {
                                "vyatta-interfaces-switch-policy-v1:policy": {
                                    "vyatta-policy-qos-v1:qos": "policy-1"
                                }
                            }
                        }
                    }
                ]
            },
            "vyatta-policy-v1:policy": {
                "vyatta-policy-action-v1:action": {
                    "name": [
                        {
                            "id": "bert",
                            "mark": {
                                "dscp": "cs4",
                                "pcp": 7,
                                "pcp-inner": [
                                    null
                                ]
                            },
                            "police": {
                                "bandwidth": "100Mbit"
                            }
                        }
                    ]
                },
                "vyatta-policy-qos-v1:qos": {
                    "name": [
                        {
                            "id": "policy-1",
                            "shaper": {
                                "bandwidth": "10Gbit",
                                "burst": "16000",
                                "default": "glob-prof-1",
                                "frame-overhead": "24",
                                "profile": [
                                    {
                                        "burst": "16000",
                                        "id": "profile-1"
                                    }
                                ],
                                "mark-map": "test123"
                            }
                        }
                    ],
                    "profile": [
                        {
                            "bandwidth": "100Mbit",
                            "burst": "16000",
                            "id": "glob-prof-1"
                        },
                        {
                            "bandwidth": "200Mbit",
                            "burst": "20msec",
                            "id": "glob-prof-2"
                        },
                        {
                            "bandwidth": "300Mbit",
                            "burst": "30msec",
                            "id": "glob-prof-3"
                        },
                        {
                            "bandwidth": "400Mbit",
                            "burst": "16000",
                            "id": "glob-prof-4"
                        }
                    ],
                    "mark-map": [
                        {
                            "id": "test123",
                            "dscp-group": [
                                {"group-name": "fred", "pcp-mark": "4"},
                                {"group-name": "bert", "pcp-mark": "3"},
                                {"group-name": "joe", "pcp-mark": "2"}
                            ]
                        }
                    ]
                }
            },
            'vyatta-resources-v1:resources': {
	        'vyatta-resources-group-misc-v1:group': {
		    'vyatta-resources-dscp-group-v1:dscp-group': [
			{
			    'group-name': 'group-a',
			    'dscp': [
                                '0', '1', '2', '3', '4', '5', '6', '7', '8',
                                '9', '10', '11', '12', '13', '14', '15'
                            ]
			}, {
			    'group-name': 'group-b',
			    'dscp': [
                                '16', '17', '18', '19', '20', '21', '22', '23',
                                '24', '25', '26', '27', '28', '29', '30', '31'
                            ]
			}, {
			    'group-name': 'group-c',
			    'dscp': [
                                '32', '33', '34', '35', '36', '37', '38', '39',
                                '40', '41', '42', '43', '44', '45', '46', '47'
                            ]
			}, {
			    'group-name': 'group-d',
			    'dscp': [
                                '48', '49', '50', '51', '52', '53', '54', '55',
                                '56', '57', '58', '59', '60', '61', '62', '63'
                            ]
			}
		    ]
	        }
            }
        },
        # expected_result
        [
            # Each tuple represents the arguments passed into ctrl.store
            # 1st element: the cstore path that the command is store at
            # 2nd element: the stored command
            # 3rd element: the interface that the command applies to
            #              for unit-testing it is either "lo" or "ALL"
            # 4th element: the store command, can be "SET" or "DELETE"
            (
                'qos mark-map test123 dscp-group bert',
                'qos 0 mark-map test123 dscp-group bert pcp 3',
                'ALL',
                'SET'
            ),
            (
                'qos mark-map test123 dscp-group fred',
                'qos 0 mark-map test123 dscp-group fred pcp 4',
                'ALL',
                'SET'
            ),
            (
                'qos mark-map test123 dscp-group joe',
                'qos 0 mark-map test123 dscp-group joe pcp 2',
                'ALL',
                'SET'
            ),
            (
                'policy action name bert',
                'npf-cfg add action-group:bert 0 rproc=markpcp(7,inner);'
                'policer(0,12500000,50000,drop,,0,20)',
                'ALL',
                'SET'
            ),
            (
                'qos 1 qos 1 port subports 1 pipes 1 profiles 5 overhead 24',
                'qos 1 port subports 1 pipes 1 profiles 5 overhead 24',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 subport 0 rate 1250000000 size 16000 period 40',
                'qos 1 subport 0 rate 1250000000 size 16000 period 40',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 subport 0 queue 0 percent 100 size 0',
                'qos 1 subport 0 queue 0 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 param subport 0 0 limit packets 64',
                'qos 1 param subport 0 0 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 subport 0 queue 1 percent 100 size 0',
                'qos 1 subport 0 queue 1 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 param subport 0 1 limit packets 64',
                'qos 1 param subport 0 1 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 subport 0 queue 2 percent 100 size 0',
                'qos 1 subport 0 queue 2 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 param subport 0 2 limit packets 64',
                'qos 1 param subport 0 2 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 subport 0 queue 3 percent 100 size 0',
                'qos 1 subport 0 queue 3 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 param subport 0 3 limit packets 64',
                'qos 1 param subport 0 3 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 subport 0 mark-map test123',
                'qos 1 subport 0 mark-map test123',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 vlan 0 0',
                'qos 1 vlan 0 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 4 percent 100 size 16000 period 10',
                'qos 1 profile 4 percent 100 size 16000 period 10',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 4 queue 0 percent 100 size 0',
                'qos 1 profile 4 queue 0 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 4 queue 1 percent 100 size 0',
                'qos 1 profile 4 queue 1 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 4 queue 2 percent 100 size 0',
                'qos 1 profile 4 queue 2 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 4 queue 3 percent 100 size 0',
                'qos 1 profile 4 queue 3 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 0 rate 12500000 size 16000 period 10',
                'qos 1 profile 0 rate 12500000 size 16000 period 10',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 0 queue 0 percent 100 size 0',
                'qos 1 profile 0 queue 0 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 0 queue 1 percent 100 size 0',
                'qos 1 profile 0 queue 1 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 0 queue 2 percent 100 size 0',
                'qos 1 profile 0 queue 2 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 0 queue 3 percent 100 size 0',
                'qos 1 profile 0 queue 3 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 1 rate 25000000 msec 20 period 10',
                'qos 1 profile 1 rate 25000000 msec 20 period 10',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 1 queue 0 percent 100 size 0',
                'qos 1 profile 1 queue 0 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 1 queue 1 percent 100 size 0',
                'qos 1 profile 1 queue 1 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 1 queue 2 percent 100 size 0',
                'qos 1 profile 1 queue 2 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 1 queue 3 percent 100 size 0',
                'qos 1 profile 1 queue 3 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 2 rate 37500000 msec 30 period 10',
                'qos 1 profile 2 rate 37500000 msec 30 period 10',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 2 queue 0 percent 100 size 0',
                'qos 1 profile 2 queue 0 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 2 queue 1 percent 100 size 0',
                'qos 1 profile 2 queue 1 percent 100 size 0',
                'lo',
                'SET'),
            (
                'qos 1 qos 1 profile 2 queue 2 percent 100 size 0',
                'qos 1 profile 2 queue 2 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 2 queue 3 percent 100 size 0',
                'qos 1 profile 2 queue 3 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 3 rate 50000000 size 16000 period 10',
                'qos 1 profile 3 rate 50000000 size 16000 period 10',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 3 queue 0 percent 100 size 0',
                'qos 1 profile 3 queue 0 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 3 queue 1 percent 100 size 0',
                'qos 1 profile 3 queue 1 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 3 queue 2 percent 100 size 0',
                'qos 1 profile 3 queue 2 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 profile 3 queue 3 percent 100 size 0',
                'qos 1 profile 3 queue 3 percent 100 size 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 pipe 0 0 0',
                'qos 1 pipe 0 0 0',
                'lo',
                'SET'
            ),
            (
                'qos 1 qos 1 enable',
                'qos 1 enable',
                'lo',
                'SET'
            ),
            (
                'qos commit',
                'qos commit',
                'ALL',
                'SET'
            ),
            (
                'resources group dscp-group group-a dscp',
                'npf-cfg add dscp-group:group-a 0 0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15',
                'ALL',
                'SET'
            ),
            (
                'resources group dscp-group group-b dscp',
                'npf-cfg add dscp-group:group-b 0 16;17;18;19;20;21;22;23;24;25;26;27;28;29;30;31',
                'ALL',
                'SET'
            ),
            (
                'resources group dscp-group group-c dscp',
                'npf-cfg add dscp-group:group-c 0 32;33;34;35;36;37;38;39;40;41;42;43;44;45;46;47',
                'ALL',
                'SET'
            ),
            (
                'resources group dscp-group group-d dscp',
                'npf-cfg add dscp-group:group-d 0 48;49;50;51;52;53;54;55;56;57;58;59;60;61;62;63',
                'ALL',
                'SET'
            )
        ]
    )
]

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_provisioner(test_input, expected_result):
    """ Simple unit-test for the provisioner class """
    # Mock up a dataplane context manager
    mock_dataplane = MagicMock()
    mock_dataplane.__enter__.return_value = mock_dataplane

    # Mock up a controller class
    attrs = {
        'get_dataplanes.return_value':[mock_dataplane],
        'store.return_value':0
    }
    ctrl = Mock(**attrs)

    prov = Provisioner({}, test_input)
    assert prov is not None
    # prov.commands writes the QoS config commands to the mocked controller
    prov.commands(ctrl)
    for call_args in expected_result:
        ctrl.store.assert_any_call(*call_args)
