#!/usr/bin/env python3

# Copyright (c) 2019 - 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
Unit-tests for the qos_op_mode.py module.
"""

import json
from unittest.mock import patch
import vyatta_policy_qos_vci.qos_op_mode
import pathlib


def test_qos_op_mode():
    """
    Unit-test this module

    The following test_data and expected_results were generated by loading
    the following configuration onto a standard Vyatta VM:

       set interfaces dataplane dp0s4 policy qos policy-2
       set interfaces dataplane dp0s5 policy qos policy-1
       set interfaces dataplane dp0s6 policy qos policy-3
       set policy qos name policy-1 shaper class 1 match m1 source address 10.10.10.0/24
       set policy qos name policy-1 shaper class 1 profile profile-2
       set policy qos name policy-1 shaper default profile-1
       set policy qos name policy-1 shaper profile profile-1 bandwidth 300Mbit
       set policy qos name policy-1 shaper profile profile-2 bandwidth 200Mbit
       set policy qos name policy-2 shaper default profile-2
       set policy qos name policy-2 shaper profile profile-2 bandwidth 100Mbit
       set policy qos name policy-2 shaper traffic-class 1 queue-limit 8192
       set policy qos name policy-2 shaper traffic-class 1 random-detect filter-weight 10
       set policy qos name policy-2 shaper traffic-class 1 random-detect mark-probability 50
       set policy qos name policy-2 shaper traffic-class 1 random-detect max-threshold 8191
       set policy qos name policy-2 shaper traffic-class 1 random-detect min-threshold 4096
       set policy action name act-grp-1 police ratelimit 300Kpps
       set policy qos name policy-3 shaper class 1 match m1 police bandwidth 123Mbit
       set policy qos name policy-3 shaper class 1 match m1 source address 10.10.0.0/24
       set policy qos name policy-3 shaper class 1 profile profile-1
       set policy qos name policy-3 shaper class 2 match m2 action-group act-grp-1
       set policy qos name policy-3 shaper class 2 match m2 destination address 20.20.0.0/24
       set policy qos name policy-3 shaper class 2 profile profile-1
       set policy qos name policy-3 shaper default default-profile
       set policy qos name policy-3 shaper profile default-profile bandwidth 500Mbit
       set policy qos name policy-3 shaper profile profile-1 bandwidth 300Mbit

    then using '/opt/vyatta/bin/vplsh -lc "qos optimised-show" | json_pp' to
    generate test_data, and '/opt/vyatta/bin/qos-op-mode.pl --all | json_pp' to
    generate expected_results.
    """

    script_location = pathlib.Path(__file__).parent
    with open(script_location / "qos_op_mode_config.json") as config_data:
        config = json.load(config_data)

    with open(script_location / "qos_op_mode_test_data.json") as test_data:
        test_data = json.load(test_data)

    with open(script_location / "qos_op_mode_expected_results.json") as results_data:
        expected_results = json.load(results_data)

    with patch('vyatta_policy_qos_vci.qos_op_mode.get_config') as mock_get_config:
        mock_get_config.return_value = config
        with patch('vyatta_policy_qos_vci.qos_op_mode.get_sysfs_value') as mock_get_sysfs_value:
            mock_get_sysfs_value.return_value = "8"

            yang_dict = {}
            yang_dict['if-list'] = (
                vyatta_policy_qos_vci.qos_op_mode.convert_if_list('all',
                                                                  test_data)
            )

            expected_if_list = expected_results['state']
            assert yang_dict == expected_if_list
