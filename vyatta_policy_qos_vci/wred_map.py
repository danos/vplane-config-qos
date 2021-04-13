#!/usr/bin/env python3
#
# Copyright (c) 2019-2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define a class of object to hold Wred parameters
"""

from pathlib import Path

def byte_limits():
    """ Check the feature file to see if we are using byte or packet limits? """
    byte_limit_feature = Path(
        "/run/vyatta-platform/features/vyatta-policy-qos-groupings-v1/byte-limits")
    return byte_limit_feature.is_file()

def get_limit_time(limit_value, is_time):
    if limit_value is not None:
        if is_time:
            return int(float(limit_value) * 1000)
        else:
            return limit_value

def check_threshold(is_time, max_th, is_ql_time, qlimit):
    """ Validate threshold values """
    if qlimit and max_th and (is_time == is_ql_time):
        if (int(max_th) > qlimit):
            if is_time:
                limits = "usec"
            else:
                limits = "bytes" if byte_limits() else "packets"
            raise ThresholdError(f"max-threshold {max_th}{limits} must be less than queue-limit {qlimit}{limits}")

class ThresholdError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class WredMap():
    """ Define the wred-map class """
    def __init__(self, wred_map_dict, is_dscp, is_time, tc_qlimit, is_ql_time):
        """ Create a wred-map object """
        self._is_dscp = is_dscp
        self._is_time = is_time
        if is_dscp:
            self._group_name = wred_map_dict['group-name']
        else:
            self._colour = wred_map_dict['colour']
        self._mark_prob = wred_map_dict['mark-probability']
        self._min_th = get_limit_time(wred_map_dict['min-threshold'], is_time)
        self._max_th = get_limit_time(wred_map_dict['max-threshold'], is_time)
        check_threshold(is_time, self._max_th, is_ql_time, tc_qlimit)

    def commands(self, cmd_prefix):
        """ Generate the necessary command for this wred-map object """
        if self._is_time:
            limits = "usec"
        else:
            limits = "bytes" if byte_limits() else "packets"

        if self._is_dscp:
            return (f"{cmd_prefix} dscp-group {self._group_name} {limits} "
                    f"{self._max_th} {self._min_th} {self._mark_prob}")
        else:
            return (f"{cmd_prefix} drop-prec {self._colour} {limits} "
                    f"{self._max_th} {self._min_th} {self._mark_prob}")
