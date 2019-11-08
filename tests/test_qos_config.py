#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the qos_config.py module.
"""

from vyatta_policy_qos_vci.qos_config import QosConfig

TEST_DATA = {
    "vyatta-interfaces-v1:interfaces": {
        "vyatta-interfaces-dataplane-v1:dataplane": [
            {
                "tagnode": "lo",
                "vif": [
                    {
                        "tagnode": 10,
                        "vyatta-interfaces-policy-v1:policy": {
                            "vyatta-policy-qos-v1:qos": "policy-1"
                        }
                    }
                ],
                "vyatta-interfaces-policy-v1:policy": {
                    "vyatta-policy-qos-v1:qos": "policy-1"
                }
            }
        ]
    },
    "vyatta-policy-v1:policy": {
        "vyatta-policy-action-v1:action": {
            "name": [
                {
                    "id": "action-group-2",
                    "mark": {
                        "pcp": 3
                    }
                },
                {
                    "id": "action-group-1",
                    "mark": {
                        "dscp": "cs6"
                    }
                }
            ]
        },
        "vyatta-policy-qos-v1:qos": {
            "mark-map": [
                {
                    "dscp-group": [
                        {
                            "group-name": "default-group-high-drop",
                            "pcp-mark": 2
                        },
                        {
                            "group-name": "default-group-low-drop",
                            "pcp-mark": 3
                        },
                        {
                            "group-name": "priority-group-high-drop",
                            "pcp-mark": 4
                        },
                        {
                            "group-name": "priority-group-low-drop",
                            "pcp-mark": 5
                        },
                        {
                            "group-name": "real-time-group",
                            "pcp-mark": 6
                        },
                        {
                            "group-name": "synch-group",
                            "pcp-mark": 7
                        }
                    ],
                    "id": "test123"
                }
            ],
            "name": [
                {
                    "id": "policy-1",
                    "shaper": {
                        "bandwidth": "10Gbit",
                        "default": "profile-1",
                        "frame-overhead": "24",
                        "profile": [
                            {
                                "id": "profile-1"
                            }
                        ]
                    }
                }
            ],
            "profile": [
                {
                    "bandwidth": "600Mbit",
                    "id": "global-profile-1"
                }
            ]
        }
    }
}

def test_qosconfig():
    """ Simple Unit Test for the QoSConfig class """
    config = QosConfig(TEST_DATA)
    assert config is not None
    assert len(config.interfaces) == 1
    assert config.find_interface("lo") is not None
    assert len(config.global_profiles) == 1
    assert config.find_global_profile("global-profile-1") is not None
    assert config.get_policy("policy-1") is not None
    assert config.get_mark_map("test123") is not None
    assert config.get_action_group("action-group-1") is not None
    assert config.get_action_group("action-group-2") is not None
