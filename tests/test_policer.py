#!/usr/bin/env python3

# Copyright (c) 2019, 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the policer.py module.
"""

import pytest

from vyatta_policy_qos_vci.policer import parse_bandwidth, parse_ratelimit, Policer

TEST_DATA_BANDWIDTH = [
    # each tuple contains (<test_input>, <expected_result>)
    # good values - bits per second
    (None, None),
    ("1", 125),
    ("1kbit", 125),
    ("2Kbit", 250),
    ("4mbit", 500000),
    ("16Mbit", 2000000),
    ("2Gbit", 250000000),
    ("4kibit", 512),
    ("8Mibit", 1048576),
    ("10gibit", 1342177280),
    ("0.1Gbit", 12500000),
    ("1.3Gbit", 162500000),
    ("123.456mbit", 15432000),
    # good values - bytes per second
    ("1bps", 1),
    ("2kbps", 2000),
    ("4Kbps", 4000),
    ("8mbps", 8000000),
    ("10Mbps", 10000000),
    ("2gbps", 2000000000),
    ("4Kibps", 4096),
    ("8mibps", 8388608),
    ("16Gibps", 17179869184),
    ("2.8kbps", 2800),
    # bad values
    ("a", None),
    ("1a", None)
]


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA_BANDWIDTH)
def test_parse_bandwidth(test_input, expected_result):
    """ Simple unit-test function for parse_bandwidth """
    assert parse_bandwidth(test_input) == expected_result


TEST_DATA_RATELIMIT = [
    # each tuple contains (<test_input>, <expected_result>)
    # Good values
    (None, (None, False)),
    ("1234", (1234, False)),
    ("400pps", (400, True)),
    ("1kpps", (1024, True)),
    ("2Kpps", (2048, True)),
    ("34Mpps", (34000000, True)),
    ("567mpps", (567000000, True)),
    # Bad values
    ("abc", (None, False)),
    ("123apps", (None, False)),
    ("123abc", (None, False))
]


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA_RATELIMIT)
def test_parse_ratelimit(test_input, expected_result):
    """ Simple unit-test function for parse_ratelimit """
    assert parse_ratelimit(test_input) == expected_result


# We need to define null as None because null is a valid JSON field
# value, but it isn't defined by python
null = None

TEST_DATA_POLICER = [
    (
        # Start with a simple policer with a Kbits/sec bandwidth
        # test_input
        {
            "bandwidth": "1000"
        },
        # expected_result
        "policer(0,125000,500,drop,,0,20)"
    ),
    (
        # Change the bandwidth to Mbytes/sec and add a burst rate
        {
            "bandwidth": "2Mbps",
            "burst": 12345
        },
        "policer(0,2000000,12345,drop,,0,20)"
    ),
    (
        # Change the bandwidth and add a frame-overhead
        {
            "bandwidth": "56789Kibit",
            "burst": 12345,
            "frame-overhead": "10"
        },
        "policer(0,7268992,12345,drop,,10,20)"
    ),
    (
        # Change the bandwidth and add a tc - the token bucket period
        {
            "bandwidth": "1Gbps",
            "burst": 12345,
            "frame-overhead": "10",
            "tc": 250
        },
        "policer(0,1000000000,12345,drop,,10,250)"
    ),
    (
        # Add a "then-action-drop" into the mix
        {
            "bandwidth": "1Gbps",
            "burst": 12345,
            "frame-overhead": "10",
            "tc": 250,
            "then": {
                "action": "drop"
            }
        },
        "policer(0,1000000000,12345,drop,,10,250)"
    ),
    (
        # Change the "then-action-drop" to a "mark dscp 0"
        {
            "bandwidth": "1Gbps",
            "burst": 12345,
            "frame-overhead": "10",
            "tc": 250,
            "then": {
                "mark": {
                    "dscp": "0"
                }
            }
        },
        "policer(0,1000000000,12345,markdscp,0,10,250)"
    ),
    (
        # Change the numerical dscp value to a diff-serv name - cs6 = 48
        {
            "bandwidth": "1Gbps",
            "burst": 12345,
            "frame-overhead": "10",
            "tc": 250,
            "then": {
                "mark": {
                    "dscp": "cs6"
                }
            }
        },
        "policer(0,1000000000,12345,markdscp,48,10,250)"
    ),
    (
        # Change the then-mark from dscp to pcp
        {
            "bandwidth": "1Gbps",
            "burst": 12345,
            "frame-overhead": "10",
            "tc": 250,
            "then": {
                "mark": {
                    "pcp": 3
                }
            }
        },
        "policer(0,1000000000,12345,markpcp,3,10,250,none)"
    ),
    (
        # Start with a simple ratelimit
        {
            "ratelimit": "1000"
        },
        "policer(1000,0,0,drop,,0,1000)"
    ),
    (
        # Add a ratelimit pps suffix
        {
            "ratelimit": "500kpps"
        },
        "policer(512000,0,0,drop,,0,1000)"
    ),
    (
        # Add a burst rate which should be ignored
        {
            "burst": 4321,
            "ratelimit": "500kpps"
        },
        "policer(512000,0,0,drop,,0,1000)"
    ),
    (
        # Add a frame-overhead which should also be ignored
        {
            "burst": 4321,
            "frame-overhead": "-5",
            "ratelimit": "500kpps"
        },
        "policer(512000,0,0,drop,,0,1000)"
    ),
    (
        # Remove the ratelimit's "kpps" suffix and add a tc-period which
        # will be set
        {
            "burst": 4321,
            "frame-overhead": "-5",
            "ratelimit": "500",
            "tc": 345
        },
        "policer(500,0,0,drop,,0,345)"
    ),
    (
        # Replace the ratelimit's "kpps", this time the tc-period will be
        # ignored
        {
            "burst": 4321,
            "frame-overhead": "-5",
            "ratelimit": "500kpps",
            "tc": 345
        },
        "policer(512000,0,0,drop,,0,1000)"
    ),
    (
        # Add a then-action-drop, which also makes no difference
        {
            "burst": 4321,
            "frame-overhead": "-5",
            "ratelimit": "500kpps",
            "tc": 345,
            "then": {
                "action": "drop"
            }
        },
        "policer(512000,0,0,drop,,0,1000)"
    ),
    (
        # Add a then-mark-pcp which is overrided then-action-drop
        {
            "burst": 4321,
            "frame-overhead": "-5",
            "ratelimit": "500kpps",
            "tc": 345,
            "then": {
                "action": "drop",
                "mark": {
                    "pcp": 4
                }
            }
        },
        "policer(512000,0,0,drop,,0,1000)"
    ),
    (
        # Remove the then-action-drop to expose then-mark-pcp
        {
            "burst": 4321,
            "frame-overhead": "-5",
            "ratelimit": "500kpps",
            "tc": 345,
            "then": {
                "mark": {
                    "pcp": 4
                }
            }
        },
        "policer(512000,0,0,markpcp,4,0,1000,none)"
    ),
    (
        # Add pcp-inner
        {
            "burst": 4321,
            "frame-overhead": "-5",
            "ratelimit": "500kpps",
            "tc": 345,
            "then": {
                "mark": {
                    "pcp": 4,
                    "pcp-inner": [
                        null
                    ]
                }
            }
        },
        "policer(512000,0,0,markpcp,4,0,1000,inner)"
    )
]


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA_POLICER)
def test_policer_class(test_input, expected_result):
    """ Simple unit-test for policer class """
    policer = Policer(test_input)
    assert policer is not None
    assert policer.commands() == expected_result
