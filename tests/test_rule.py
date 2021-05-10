#!/usr/bin/env python3

# Copyright (c) 2019-2020, AT&T Intellectual Property.
# All rights reserved.

"""
Unit-tests for the rule.py module.
"""

import pytest

from vyatta_policy_qos_vci.rule import Rule

TEST_DATA = [
    (
        # test_input
        {
            "action": "pass",
            "destination": {
                "port": "http"
            },
            "dscp": "56",
            "id": "m1",
            "protocol": "tcp",
            "source": {
                "address": "10.10.0.0/24"
            }
        },
        # expected_result
        "action=accept proto-final=6 src-addr=10.10.0.0/24 dst-port=80 " \
        "dscp=56 handle=tag(1)",
    ),
    (
        # test_input
        {
            "action": "drop",
            "ethertype": "ipv4",
            "pcp": "3",
            "fragment": "yes",
            "action-group": "fred",
            "log": "yes"
        },
        # expected_result
        "action=drop ether-type=2048 pcp=3 fragment=y " \
        "rproc=action-group(fred);log handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-6',
            'action': 'pass',
            'destination': {
                'address': '10.10.10.1'
            }
        },
        # expected_output
        "action=accept dst-addr=10.10.10.1 handle=tag(1)"
    ),
    (
        # test_input
        {
            'action': 'pass',
            'destination': {
                'address': '10.10.10.0/24'
            },
            'id': 'm-6'
        },
        # expected_output
        "action=accept dst-addr=10.10.10.0/24 handle=tag(1)"
    ),
    (
        # test_input
        {
            'action': 'pass',
            'destination': {
                'address': 'addr-group-1'
            },
            'id': 'm-7'
        },
        # expected_action
        "action=accept dst-addr-group=addr-group-1 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-8',
            'action': 'pass',
            'destination': {
                'mac-address': '11:22:33:44:55:66'
            }
        },
        # expected_output
        "action=accept dst-mac=11:22:33:44:55:66 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-9',
            'action': 'pass',
            'destination': {
                'port': '1'
            },
            'protocol': 'tcp'
        },
        # expected_output
        "action=accept proto-final=6 dst-port=1 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-10',
            'action': 'pass',
            'destination': {
                'port': '10-20'
            },
            'protocol': 'udp'
        },
        # expected_output
        "action=accept proto-final=17 dst-port=10-20 handle=tag(1)"
    ),
    (
        # test_input
        {
            'action': 'pass',
            'destination': {
                'port': 'port-group-11'
            },
            'id': 'm-11',
            'protocol': 'udp'
        },
        # expected_output
        "action=accept proto-final=17 dst-port-group=port-group-11 " \
        "handle=tag(1)"
    ),
    (
        # test_input
        {
            'action': 'pass',
            'destination': {
                'port': 'ftp'
            },
            'protocol': 'tcp',
            'id': 'm-12'
        },
        # expected_output
        "action=accept proto-final=6 dst-port=21 handle=tag(1)"
    ),
    (
        # test_input
        {
            'action': 'pass',
            'destination': {
                'address': 'addr-group-2'
            },
            'disable': [None],
            'id': 'm-12'
        },
        # expected_output
        None
    ),
    (
        # test_input
        {'action': 'pass', 'dscp': '0'},
        # expected_output
        "action=accept dscp=0 handle=tag(1)"
    ),
    (
        # test_input
        {'action': 'pass', 'dscp': 'af12'},
        # expected_output
        "action=accept dscp=12 handle=tag(1)"
    ),
    (
        # test_input
        {'action': 'pass', 'dscp-group': 'dscp-group-1'},
        # expected_output
        "action=accept dscp-group=dscp-group-1 handle=tag(1)"
    ),
    (
        # test_input
        {'id': 'm-12', 'action': 'pass', 'ethertype': 'arp'},
        # expected_output
        "action=accept ether-type=2054 handle=tag(1)"
    ),
    (
        # test_input
        {'id': 'm-13', 'action': 'pass', 'ethertype': 'x25'},
        # expected_output
        "action=accept ether-type=2053 handle=tag(1)"
    ),
    (
        # test_input
        {'action': 'pass', 'fragment': [None], 'id': 'm-14'},
        # expected_output
        "action=accept fragment=y handle=tag(1)"
    ),
    (
        # test_input
        {'action': 'pass', 'icmp': {'group': 'icmp-group-15'}},
        # expected_output
        "action=accept proto-final=1 icmpv4-group=icmp-group-15 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-17',
            'action': 'pass',
            'icmp': {
                'type': [
                    {'type-number': 0}
                ]
            }
        },
        # expected_output
        "action=accept proto-final=1 icmpv4=0 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-18',
            'action': 'pass',
            'icmp': {
                'type': [
                    {'type-number': 1, 'code': 2}
                ]
            }
        },
        # expected_output
        "action=accept proto-final=1 icmpv4=1:2 handle=tag(1)"
    ),
    (
        # test_input
        {
            'action': 'pass',
            'icmpv6': {
                'group': 'icmpv6-group-19'
            },
            'id': 'm-19'
        },
        # expected_result
        "action=accept proto-final=58 icmpv6-group=icmpv6-group-19 " \
        "handle=tag(1)"
    ),
    (
        # test_input
        {
            'action': 'pass',
            'icmpv6': {
                'name': 'bad-header'
            },
            'id': 'm-20'
        },
        # expected_result
        "action=accept proto-final=58 icmpv6=bad-header " \
        "handle=tag(1)"
    ),
    (
        # test_input
        {
            'action': 'pass',
            'icmpv6': {
                'type': [
                    {'type-number': 2}
                ]
            },
            'id': 'm-21'
        },
        # expected_result
        "action=accept proto-final=58 icmpv6=2 " \
        "handle=tag(1)"
    ),
    (
        # test_input
        {'action': 'pass', 'id': 'm-22', 'ipv6-route': {'type': 0}},
        # expected_output
        "action=accept ipv6-route=0 proto-final=43 handle=tag(1)"
    ),
    (
        # test_input
        {'action': 'pass', 'id': 'm-24', 'mark': {'dscp': 'cs1'}},
        # expected_output
        "action=accept rproc=markdscp(8) handle=tag(1)"
    ),
    (
        # test_input
        {'action': 'pass', 'id': 'm-25', 'mark': {'pcp': '6'}},
        # expected_output
        "action=accept rproc=markpcp(6,none) handle=tag(1)"
    ),
    (
        # test_input
        {
            'action': 'pass',
            'id': 'm-26',
            'mark': {
                'pcp': '3',
                'pcp-inner': [None]
            }
        },
        # expected_output
        "action=accept rproc=markpcp(3,inner) handle=tag(1)"
    ),
    (
        # test_input
        {'action': 'pass', 'id': 'm-28', 'police': {'bandwidth': '1Mbit'}},
        # expected_output
        "action=accept rproc=policer(0,125000,500,drop,,0,20) handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-29',
            'action': 'pass',
            'police': {
                'bandwidth': '2Mbit',
                'burst': 12345678
            }
        },
        # expected_output
        "action=accept rproc=policer(0,250000,12345678,drop,,0,20) " \
        "handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-30',
            'action': 'pass',
            'police': {
                'bandwidth': '3Mbit',
                'frame-overhead': '-10'
            }
        },
        # expected_output
        "action=accept rproc=policer(0,375000,1500,drop,,-10,20) handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-31',
            'action': 'pass',
            'police': {
                'bandwidth': '4Mbit',
                'frame-overhead': '9'
            }
        },
        # expected_output
        "action=accept rproc=policer(0,500000,2000,drop,,9,20) handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-32',
            'action': 'pass',
            'police': {
                'bandwidth': '5Mbit',
                'frame-overhead': 'inherit'
            }
        },
        # expected_output
        "action=accept rproc=policer(0,625000,2500,drop,,inherit,20) " \
        "handle=tag(1)"
    ),
    (
        # test_input
        {'id': 'm-33', 'action': 'pass', 'police': {'ratelimit': '1Kpps'}},
        # expected_output
        "action=accept rproc=policer(1024,0,0,drop,,0,1000) handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-34',
            'action': 'pass',
            'police': {
                'ratelimit': '2Kpps',
                'tc': 123
            }
        },
        # expected_output
        "action=accept rproc=policer(2048,0,0,drop,,0,1000) handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-35',
            'action': 'pass',
            'police': {
                'ratelimit': '3Kpps',
                'then': {
                    'action': 'drop'
                }
            }
        },
        # expected_output
        "action=accept rproc=policer(3072,0,0,drop,,0,1000) handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-36',
            'action': 'pass',
            'police': {
                'ratelimit': '4Kpps',
                'then': {
                    'mark': {
                        'dscp': 'cs4'
                    }
                }
            }
        },
        # expected_output
        "action=accept rproc=policer(4096,0,0,markdscp,32,0,1000) " \
        "handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-37',
            'action': 'pass',
            'police': {
                'ratelimit': '5Kpps',
                'then': {
                    'mark': {
                        'pcp': 2
                    }
                }
            }
        },
        # expected_output
        "action=accept rproc=policer(5120,0,0,markpcp,2,0,1000,none) " \
        "handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-38',
            'action': 'pass',
            'police': {
                'ratelimit': '6Kpps',
                'then': {
                    'mark': {
                        'pcp-inner': [None]
                    }
                }
            }
        },
        # expected_output
        "action=accept rproc=policer(6144,0,0,drop,,0,1000) handle=tag(1)"
    ),
    (
        # test_input
        {'id': 'm-40', 'action': 'pass', 'protocol': 'ah'},
        # expected_output
        "action=accept proto-final=51 handle=tag(1)"
    ),
    (
        # test_input
        {'id': 'm-41', 'action': 'pass', 'protocol': 'xtp'},
        # expected_output
        "action=accept proto-final=36 handle=tag(1)"
    ),
    (
        # test_input
        {'id': 'm-42', 'action': 'pass', 'protocol-group': 'protocol-group-52'},
        # expected_output
        "action=accept protocol-group=protocol-group-52 handle=tag(1)"
    ),
    (
        # test_input
        {'id': 'm-43', 'action': 'pass', 'source': {'address': '10.10.10.1'}},
        # expected_output
        "action=accept src-addr=10.10.10.1 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-43',
            'action': 'pass',
            'source': {
                'address': '10.10.10.0/24'
            }
        },
        # expected_output
        "action=accept src-addr=10.10.10.0/24 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-44',
            'action': 'pass',
            'source': {
                'address': 'addr-group-55'
            }
        },
        # expected_output
        "action=accept src-addr-group=addr-group-55 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-45',
            'action': 'pass',
            'source': {
                'mac-address': '66:55:44:33:22:11'
            }
        },
        # expected_output
        "action=accept src-mac=66:55:44:33:22:11 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-46',
            'action': 'pass',
            'protocol': 'tcp',
            'source': {
                'port': '57'
            }
        },
        # expected_output
        "action=accept proto-final=6 src-port=57 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-47',
            'action': 'pass',
            'protocol': 'udp',
            'source': {
                'port': '37-57'
            }
        },
        # expected_output
        "action=accept proto-final=17 src-port=37-57 handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-48',
            'action': 'pass',
            'protocol': 'udp',
            'source': {
                'port': 'port-group-58'
            }
        },
        # expected_output
        "action=accept proto-final=17 src-port-group=port-group-58 " \
        "handle=tag(1)"
    ),
    (
        # test_input
        {
            'id': 'm-49',
            'action': 'pass',
            'protocol': 'tcp',
            'source': {
                'port': 'fido'
            }
        },
        # expected_output
        "action=accept proto-final=6 src-port=60179 " \
        "handle=tag(1)"
    ),
    (
        # test_input
        {'id': 'm-63', 'action': 'pass', 'tcp': {'flags': 'SYN'}},
        # expected_output
        "action=accept proto-final=6 tcp-flags=SYN handle=tag(1)"
    ),
    (
        # test_input
        {'id': 'm-64', 'action': 'pass', 'tcp': {'flags': '!ACK'}},
        # expected_output
        "action=accept proto-final=6 tcp-flags=!ACK handle=tag(1)"
    )
]

@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_rule(test_input, expected_result):
    """ Unit-test the rule class """
    rule = Rule(1, test_input)
    assert rule is not None
    assert rule.commands() == expected_result
