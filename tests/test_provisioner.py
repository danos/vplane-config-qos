#!/usr/bin/env python3

# Copyright (c) 2019-2020, AT&T Intellectual Property.
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
                                    "vyatta-policy-qos-v1:qos": "policy-1",
                                    "vyatta-policy-qos-v1:ingress-map": "bill"
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
                "vyatta-policy-qos-v1:ingress-map": [
                    {
                        "id": "bill",
                        "pcp": [
                            {
                                "designation": 0,
                                "id": 0,
                                "drop-precedence": "green"
                            }, {
                                "designation": 1,
                                "id": 1,
                                "drop-precedence": "green"
                            }, {
                                "designation": 2,
                                "id": 2,
                                "drop-precedence": "green"
                            }, {
                                "designation": 3,
                                "id": 3,
                                "drop-precedence": "green"
                            }, {
                                "designation": 4,
                                "id": 4,
                                "drop-precedence": "green"
                            }, {
                                "designation": 5,
                                "id": 5,
                                "drop-precedence": "green"
                            }, {
                                "designation": 6,
                                "id": 6,
                                "drop-precedence": "green"
                            }, {
                                "designation": 7,
                                "id": 7,
                                "drop-precedence": "green"
                            }
                        ],
                        'system-default': [None]
                    }
                ],
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
                'qos global-object-cmd ingress-map bill pcp 0',
                'qos global-object-cmd ingress-map bill pcp 0 designation 0 drop-prec green',
                'ALL',
                'SET'
            ),
            (
                'qos global-object-cmd ingress-map bill pcp 1',
                'qos global-object-cmd ingress-map bill pcp 1 designation 1 drop-prec green',
                'ALL',
                'SET'
            ),
            (
                'qos global-object-cmd ingress-map bill pcp 2',
                'qos global-object-cmd ingress-map bill pcp 2 designation 2 drop-prec green',
                'ALL',
                'SET'
            ),
            (
                'qos global-object-cmd ingress-map bill pcp 3',
                'qos global-object-cmd ingress-map bill pcp 3 designation 3 drop-prec green',
                'ALL',
                'SET'
            ),
            (
                'qos global-object-cmd ingress-map bill pcp 4',
                'qos global-object-cmd ingress-map bill pcp 4 designation 4 drop-prec green',
                'ALL',
                'SET'
            ),
            (
                'qos global-object-cmd ingress-map bill pcp 5',
                'qos global-object-cmd ingress-map bill pcp 5 designation 5 drop-prec green',
                'ALL',
                'SET'
            ),
            (
                'qos global-object-cmd ingress-map bill pcp 6',
                'qos global-object-cmd ingress-map bill pcp 6 designation 6 drop-prec green',
                'ALL',
                'SET'
            ),
            (
                'qos global-object-cmd ingress-map bill pcp 7',
                'qos global-object-cmd ingress-map bill pcp 7 designation 7 drop-prec green',
                'ALL',
                'SET'
            ),
            (
                'qos global-object-cmd ingress-map bill complete',
                'qos global-object-cmd ingress-map bill complete',
                'ALL',
                'SET'
            ),
            (
                'qos-in-map lo ingress-map bill vlan 0',
                'qos lo ingress-map bill vlan 0',
                'lo',
                'SET'
            ),
            (
                'qos mark-map test123 dscp-group bert',
                'qos global-object-cmd mark-map test123 dscp-group bert pcp 3',
                'ALL',
                'SET'
            ),
            (
                'qos mark-map test123 dscp-group fred',
                'qos global-object-cmd mark-map test123 dscp-group fred pcp 4',
                'ALL',
                'SET'
            ),
            (
                'qos mark-map test123 dscp-group joe',
                'qos global-object-cmd mark-map test123 dscp-group joe pcp 2',
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
                'qos lo qos lo port subports 1 pipes 1 profiles 5 overhead 24 ql_packets',
                'qos lo port subports 1 pipes 1 profiles 5 overhead 24 ql_packets',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 0 rate 1250000000 size 16000 period 40',
                'qos lo subport 0 rate 1250000000 size 16000 period 40',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 0 queue 0 percent 100 msec 4',
                'qos lo subport 0 queue 0 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo param subport 0 0 limit packets 64',
                'qos lo param subport 0 0 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 0 queue 1 percent 100 msec 4',
                'qos lo subport 0 queue 1 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo param subport 0 1 limit packets 64',
                'qos lo param subport 0 1 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 0 queue 2 percent 100 msec 4',
                'qos lo subport 0 queue 2 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo param subport 0 2 limit packets 64',
                'qos lo param subport 0 2 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 0 queue 3 percent 100 msec 4',
                'qos lo subport 0 queue 3 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo param subport 0 3 limit packets 64',
                'qos lo param subport 0 3 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 0 mark-map test123',
                'qos lo subport 0 mark-map test123',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo vlan 0 0',
                'qos lo vlan 0 0',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 4 percent 100 size 16000 period 10',
                'qos lo profile 4 percent 100 size 16000 period 10',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 4 queue 0 percent 100 msec 4',
                'qos lo profile 4 queue 0 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 4 queue 1 percent 100 msec 4',
                'qos lo profile 4 queue 1 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 4 queue 2 percent 100 msec 4',
                'qos lo profile 4 queue 2 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 4 queue 3 percent 100 msec 4',
                'qos lo profile 4 queue 3 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 0 rate 12500000 size 16000 period 10',
                'qos lo profile 0 rate 12500000 size 16000 period 10',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 0 queue 0 percent 100 msec 4',
                'qos lo profile 0 queue 0 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 0 queue 1 percent 100 msec 4',
                'qos lo profile 0 queue 1 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 0 queue 2 percent 100 msec 4',
                'qos lo profile 0 queue 2 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 0 queue 3 percent 100 msec 4',
                'qos lo profile 0 queue 3 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 1 rate 25000000 msec 20 period 10',
                'qos lo profile 1 rate 25000000 msec 20 period 10',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 1 queue 0 percent 100 msec 4',
                'qos lo profile 1 queue 0 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 1 queue 1 percent 100 msec 4',
                'qos lo profile 1 queue 1 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 1 queue 2 percent 100 msec 4',
                'qos lo profile 1 queue 2 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 1 queue 3 percent 100 msec 4',
                'qos lo profile 1 queue 3 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 2 rate 37500000 msec 30 period 10',
                'qos lo profile 2 rate 37500000 msec 30 period 10',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 2 queue 0 percent 100 msec 4',
                'qos lo profile 2 queue 0 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 2 queue 1 percent 100 msec 4',
                'qos lo profile 2 queue 1 percent 100 msec 4',
                'lo',
                'SET'),
            (
                'qos lo qos lo profile 2 queue 2 percent 100 msec 4',
                'qos lo profile 2 queue 2 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 2 queue 3 percent 100 msec 4',
                'qos lo profile 2 queue 3 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 3 rate 50000000 size 16000 period 10',
                'qos lo profile 3 rate 50000000 size 16000 period 10',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 3 queue 0 percent 100 msec 4',
                'qos lo profile 3 queue 0 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 3 queue 1 percent 100 msec 4',
                'qos lo profile 3 queue 1 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 3 queue 2 percent 100 msec 4',
                'qos lo profile 3 queue 2 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 3 queue 3 percent 100 msec 4',
                'qos lo profile 3 queue 3 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo pipe 0 0 0',
                'qos lo pipe 0 0 0',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo enable',
                'qos lo enable',
                'lo',
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
