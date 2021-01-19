#!/usr/bin/env python3

# Copyright (c) 2019-2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the dscp.py module.
"""

from unittest.mock import Mock, MagicMock, call

import pytest

from vyatta_policy_qos_vci.provisioner import Provisioner

# python doesn't define null, but it is valid JSON
null = None

TEST_DATA = [
    (
        # old_config
        {},
        # new_config
        {
            "vyatta-interfaces-v1:interfaces": {
                "vyatta-interfaces-dataplane-v1:dataplane": [
                    {
                        "tagnode": "lo",
                        "vyatta-interfaces-dataplane-switch-v1:switch-group": {
                            "port-parameters": {
                                "vyatta-interfaces-switch-policy-v1:policy": {
                                    "vyatta-policy-qos-v1:qos": "policy-1",
                                    "vyatta-policy-qos-v1:ingress-map": "bill",
                                    "vyatta-policy-qos-v1:egress-map": "bill"
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
                "vyatta-policy-qos-v1:egress-map": [
                    {
                        "id": "bill",
                        "designation": [
                            {
                                "id": 0,
                                "dscp": 0
                            }, {
                                "id": 1,
                                "dscp": 1
                            }, {
                                "id": 2,
                                "dscp": 2
                            }, {
                                "id": 3,
                                "dscp": 3
                            }, {
                                "id": 4,
                                "dscp": 4
                            }, {
                                "id": 5,
                                "dscp": 5
                            }, {
                                "id": 6,
                                "dscp": 6
                            }, {
                                "id": 7,
                                "dscp": 7
                            }
                        ],
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
        # Configd mock return: If the test input has bonding groups that
        # contain dataplane interfaces (SIAD), QoS VCI component will look for
        # the LAG members in configd. In such case, the dictionary that must be
        # returned by the configd mock (containing the dataplane interfaces) can
        # be provided here.
        None,
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
                'qos lo qos lo subport 0 rate 1250000000 size 16000 period 40000',
                'qos lo subport 0 rate 1250000000 size 16000 period 40000',
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
                'qos lo qos lo profile 4 percent 100 size 16000 period 10000',
                'qos lo profile 4 percent 100 size 16000 period 10000',
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
                'qos lo qos lo profile 0 rate 12500000 size 16000 period 10000',
                'qos lo profile 0 rate 12500000 size 16000 period 10000',
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
                'qos lo qos lo profile 1 rate 25000000 msec 20 period 10000',
                'qos lo profile 1 rate 25000000 msec 20 period 10000',
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
                'qos lo qos lo profile 2 rate 37500000 msec 30 period 10000',
                'qos lo profile 2 rate 37500000 msec 30 period 10000',
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
                'qos lo qos lo profile 3 rate 50000000 size 16000 period 10000',
                'qos lo profile 3 rate 50000000 size 16000 period 10000',
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
    ),
    (
        # old_config
        {},
        # new_config - a couple of policies that only use global profiles
        {
            'vyatta-interfaces-v1:interfaces': {
                'vyatta-interfaces-dataplane-v1:dataplane': [
                    {
                        'tagnode': 'lo',
                        'vyatta-interfaces-policy-v1:policy': {
                            'vyatta-policy-qos-v1:qos': 'No-Limit'
                        },
                        'vif': [
                            {
                                'tagnode': 100,
                                'vyatta-interfaces-policy-v1:policy': {
                                    'vyatta-policy-qos-v1:qos': 'UDP-Limit'
                                }
                            }
                        ]
                    }
                ]
            },
            'vyatta-policy-v1:policy': {
                'vyatta-policy-qos-v1:qos': {
                    'name': [
                        {
                            'id': 'No-Limit',
                            'shaper': {
                                'bandwidth': 'auto',
                                'default': 'no-shaping',
                                'frame-overhead': '24'
                            }
                        }, {
                            'id': 'UDP-Limit',
                            'shaper': {
                                'bandwidth': 'auto',
                                'class': [
                                    {
                                        'id': 1,
                                        'match': [
                                            {
                                                'id': 'UDP',
                                                'action': 'pass',
                                                'protocol': 'udp'
                                            }
                                        ],
                                        'profile': '500M'
                                    }
                                ],
                                'default': 'no-shaping',
                                'frame-overhead': '24'
                            }
                        }
                    ],
                    'profile': [
                        {
                            'id': '500M',
                            'bandwidth': '500Mbit'
                        }, {
                            'id': 'no-shaping'
                        }
                    ]
                }
            }
        },
        # Configd mock return
        None,
        # expected results
        [
            (
                'qos lo qos lo port subports 2 pipes 2 profiles 2 overhead 24 ql_packets',
                'qos lo port subports 2 pipes 2 profiles 2 overhead 24 ql_packets',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 0 auto msec 4 period 40000',
                'qos lo subport 0 auto msec 4 period 40000',
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
                'qos lo qos lo vlan 0 0',
                'qos lo vlan 0 0',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo profile 0 rate 62500000 msec 4 period 10000',
                'qos lo profile 0 rate 62500000 msec 4 period 10000',
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
                'qos lo qos lo profile 1 percent 100 msec 4 period 10000',
                'qos lo profile 1 percent 100 msec 4 period 10000',
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
                'qos lo qos lo pipe 0 0 1',
                'qos lo pipe 0 0 1',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 1 auto msec 4 period 40000',
                'qos lo subport 1 auto msec 4 period 40000',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 1 queue 0 percent 100 msec 4',
                'qos lo subport 1 queue 0 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo param subport 1 0 limit packets 64',
                'qos lo param subport 1 0 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 1 queue 1 percent 100 msec 4',
                'qos lo subport 1 queue 1 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo param subport 1 1 limit packets 64',
                'qos lo param subport 1 1 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 1 queue 2 percent 100 msec 4',
                'qos lo subport 1 queue 2 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo param subport 1 2 limit packets 64',
                'qos lo param subport 1 2 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo subport 1 queue 3 percent 100 msec 4',
                'qos lo subport 1 queue 3 percent 100 msec 4',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo param subport 1 3 limit packets 64',
                'qos lo param subport 1 3 limit packets 64',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo vlan 100 1',
                'qos lo vlan 100 1',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo pipe 1 0 1',
                'qos lo pipe 1 0 1',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo pipe 1 1 0',
                'qos lo pipe 1 1 0',
                'lo',
                'SET'
            ),
            (
                'qos lo qos lo match 1 1 action=accept proto-final=17 handle=tag(1)',
                'qos lo match 1 1 action=accept proto-final=17 handle=tag(1)',
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
    ),
    (
        # old_config
        {},
        # new_config - SIAD: QoS policy attached to a bonding group
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
        # Configd mock return: Dataplane interfaces in configd.
        {
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
        },
        # expected_result
        [
            # 1st LAG member:
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
            # 2nd LAG member:
            (
                'qos dp0xe4 qos dp0xe4 port subports 1 pipes 1 profiles 1 overhead 24 ql_packets',
                'qos dp0xe4 port subports 1 pipes 1 profiles 1 overhead 24 ql_packets',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 auto size 16000 period 40000',
                'qos dp0xe4 subport 0 auto size 16000 period 40000',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 0 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 0 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 0 limit packets 64',
                'qos dp0xe4 param subport 0 0 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 1 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 1 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 1 limit packets 64',
                'qos dp0xe4 param subport 0 1 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 2 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 2 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 2 limit packets 64',
                'qos dp0xe4 param subport 0 2 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 3 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 3 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 3 limit packets 64',
                'qos dp0xe4 param subport 0 3 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 vlan 0 0',
                'qos dp0xe4 vlan 0 0',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 rate 25000000 size 16000 period 10000',
                'qos dp0xe4 profile 0 rate 25000000 size 16000 period 10000',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 0 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 0 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 1 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 1 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 2 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 2 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 3 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 3 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 pipe 0 0 0',
                'qos dp0xe4 pipe 0 0 0',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 enable',
                'qos dp0xe4 enable',
                'dp0xe4',
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
    (
        # old_config
        {},
        # new_config - SIAD: Attach QoS to LAG + Delete LAG member + Attach QoS to front-panel port
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
        # Configd mock return: Dataplane interfaces in configd.
        {
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
        },
        # expected_result
        [
            # 1st LAG member:
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
            # 2nd LAG member:
            (
                'qos dp0xe4 qos dp0xe4 port subports 1 pipes 1 profiles 2 overhead 24 ql_packets',
                'qos dp0xe4 port subports 1 pipes 1 profiles 2 overhead 24 ql_packets',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 auto size 16000 period 40000',
                'qos dp0xe4 subport 0 auto size 16000 period 40000',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 0 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 0 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 0 limit packets 64',
                'qos dp0xe4 param subport 0 0 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 1 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 1 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 1 limit packets 64',
                'qos dp0xe4 param subport 0 1 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 2 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 2 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 2 limit packets 64',
                'qos dp0xe4 param subport 0 2 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 3 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 3 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 3 limit packets 64',
                'qos dp0xe4 param subport 0 3 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 vlan 0 0',
                'qos dp0xe4 vlan 0 0',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 rate 25000000 size 16000 period 10000',
                'qos dp0xe4 profile 0 rate 25000000 size 16000 period 10000',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 0 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 0 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 1 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 1 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 2 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 2 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 3 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 3 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 1 rate 37500000 size 16000 period 10000',
                'qos dp0xe4 profile 1 rate 37500000 size 16000 period 10000',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 1 queue 0 percent 100 msec 4',
                'qos dp0xe4 profile 1 queue 0 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 1 queue 1 percent 100 msec 4',
                'qos dp0xe4 profile 1 queue 1 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 1 queue 2 percent 100 msec 4',
                'qos dp0xe4 profile 1 queue 2 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 1 queue 3 percent 100 msec 4',
                'qos dp0xe4 profile 1 queue 3 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 pipe 0 0 0',
                'qos dp0xe4 pipe 0 0 0',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 enable',
                'qos dp0xe4 enable',
                'dp0xe4',
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
    (
        # old_config
        {
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
        # new_config - SIAD: Detach policy-1 and attach policy-2 to LAG
        {
            'vyatta-interfaces-v1:interfaces': {
                'vyatta-interfaces-bonding-v1:bonding': [
                    {
                        'tagnode': 'dp0bond1',
                        'vyatta-interfaces-bonding-switch-v1:switch-group': {
                            'port-parameters': {
                                'vyatta-interfaces-switch-policy-v1:policy': {
                                    'vyatta-policy-qos-v1:qos': 'policy-2'
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
        # Configd mock return: Dataplane interfaces in configd.
        {
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
        },
        # expected_result
        [
            # Detach old policy:
            (
                'qos dp0xe3',
                'qos dp0xe3 disable',
                'dp0xe3',
                'DELETE'
            ),
            (
                'qos dp0xe4',
                'qos dp0xe4 disable',
                'dp0xe4',
                'DELETE'
            ),
            # 1st LAG member:
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
            # 2nd LAG member:
            (
                'qos dp0xe4 qos dp0xe4 port subports 1 pipes 1 profiles 2 overhead 24 ql_packets',
                'qos dp0xe4 port subports 1 pipes 1 profiles 2 overhead 24 ql_packets',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 auto size 16000 period 40000',
                'qos dp0xe4 subport 0 auto size 16000 period 40000',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 0 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 0 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 0 limit packets 64',
                'qos dp0xe4 param subport 0 0 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 1 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 1 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 1 limit packets 64',
                'qos dp0xe4 param subport 0 1 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 2 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 2 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 2 limit packets 64',
                'qos dp0xe4 param subport 0 2 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 subport 0 queue 3 percent 100 msec 4',
                'qos dp0xe4 subport 0 queue 3 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 param subport 0 3 limit packets 64',
                'qos dp0xe4 param subport 0 3 limit packets 64',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 vlan 0 0',
                'qos dp0xe4 vlan 0 0',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 rate 25000000 size 16000 period 10000',
                'qos dp0xe4 profile 0 rate 25000000 size 16000 period 10000',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 0 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 0 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 1 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 1 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 2 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 2 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 0 queue 3 percent 100 msec 4',
                'qos dp0xe4 profile 0 queue 3 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 1 rate 37500000 size 16000 period 10000',
                'qos dp0xe4 profile 1 rate 37500000 size 16000 period 10000',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 1 queue 0 percent 100 msec 4',
                'qos dp0xe4 profile 1 queue 0 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 1 queue 1 percent 100 msec 4',
                'qos dp0xe4 profile 1 queue 1 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 1 queue 2 percent 100 msec 4',
                'qos dp0xe4 profile 1 queue 2 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 profile 1 queue 3 percent 100 msec 4',
                'qos dp0xe4 profile 1 queue 3 percent 100 msec 4',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 pipe 0 0 1',
                'qos dp0xe4 pipe 0 0 1',
                'dp0xe4',
                'SET'
            ),
            (
                'qos dp0xe4 qos dp0xe4 enable',
                'qos dp0xe4 enable',
                'dp0xe4',
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

@pytest.mark.parametrize("old_config, new_config, configd_mock_ret, expected_result", TEST_DATA)
def test_provisioner(old_config, new_config, configd_mock_ret, expected_result):
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

    # Mock up a configuration object from configd
    attrs = {
        'tree_get_dict.return_value': configd_mock_ret
    }
    # Mock up configd
    mock_config = Mock(**attrs)
    attrs = {
        'Client.return_value': mock_config
    }
    configd = Mock(**attrs)
    client = configd.Client()

    prov = Provisioner(old_config, new_config, client=client)
    assert prov is not None
    # prov.commands writes the QoS config commands to the mocked controller
    prov.commands(ctrl)

    if configd_mock_ret is None:
        for call_args in expected_result:
            ctrl.store.assert_any_call(*call_args)
    else:
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
