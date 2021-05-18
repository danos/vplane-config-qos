#!/usr/bin/env python3

# Copyright (c) 2019, 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the wred.py module.
"""

import pytest

from vyatta_policy_qos_vci.wred import Wred

TEST_DATA = [
    (
        # test_input
        {'filter-weight': 1, 'mark-probability': 2, 'max-threshold': 3,
         'min-threshold': 4},
        # expected_result
        " red 0 4 3 2 1"
    ),
    (
        # test_input
        {'filter-weight': 4, 'mark-probability': 3, 'max-threshold': 2,
         'min-threshold': 1},
        # expected_result
        " red 0 1 2 3 4"
    ),
]


@pytest.mark.parametrize("test_input, expected_result", TEST_DATA)
def test_wred(test_input, expected_result):
    """ Unit-test for the Wred class """
    wred = Wred(test_input)
    assert wred is not None
    assert wred.commands() == expected_result
