#!/usr/bin/env python3
#
# Copyright (c) 2019-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define a class of object to hold Wred parameters
"""

from pathlib import Path
from enum import Enum


def byte_limits():
    """ Check the feature file to see if we are using byte or packet limits? """
    byte_limit_feature = Path(
        "/run/vyatta-platform/features/vyatta-policy-qos-groupings-v1/byte-limits")
    return byte_limit_feature.is_file()


def get_limit(limit_value, qunits):
    """ Convert queue_limit/threshold values from msec to usec """
    if limit_value is not None:
        if qunits == WredMap.Units.TIME:
            return int(float(limit_value) * 1000)
        return int(limit_value)


def check_threshold(max_th, qlimit):
    """ Validate threshold values """
    if qlimit and max_th:
        if max_th >= qlimit:
            return False

    return True


class WredMap():
    """ Define the wred-map class """
    def __init__(self, wred_map_dict, is_dscp, qunits, tc_qlimit):
        """ Create a wred-map object """
        self._is_dscp = is_dscp
        self._qunits = qunits
        self._tc_qlimit = tc_qlimit
        if is_dscp:
            self._group_name = wred_map_dict['group-name']
        else:
            self._colour = wred_map_dict['colour']
        self._mark_prob = wred_map_dict['mark-probability']
        self._min_th = get_limit(wred_map_dict['min-threshold'], qunits)
        self._max_th = get_limit(wred_map_dict['max-threshold'], qunits)

    class Units(Enum):
        TIME = 1
        BYTES = 2
        PACKETS = 3

    def check(self, path_prefix):
        """ Check limit values and return appropriate error message for vci.exception """
        status = check_threshold(self._max_th, self._tc_qlimit)
        if not status:
            if self._qunits == WredMap.Units.TIME:
                limits = "wred-map-time"
                unit = "usec"
            elif self._qunits == WredMap.Units.BYTES:
                limits = "wred-map-bytes"
                unit = "bytes"
            else:
                limits = "wred-map"
                unit = "packets"

            if self._is_dscp:
                path = (f"{path_prefix}/{limits}/dscp-group/"
                        f"{self._group_name}/max-threshold/{self._max_th}")
            else:
                path = (f"{path_prefix}/{limits}/drop-precedence/"
                        f"{self._colour}/max-threshold/{self._max_th}")

            error = (f"max-threshold {self._max_th} {unit} "
                     f"must be less than queue-limit {self._tc_qlimit} {unit}")
            return False, error, path

        return True, None, None

    def commands(self, cmd_prefix):
        """ Generate the necessary command for this wred-map object """
        if self._qunits == WredMap.Units.TIME:
            limits = "usec"
        elif self._qunits == WredMap.Units.BYTES:
            limits = "bytes"
        else:
            limits = "packets"

        if self._is_dscp:
            return (f"{cmd_prefix} dscp-group {self._group_name} {limits} "
                    f"{self._max_th} {self._min_th} {self._mark_prob}")
        else:
            return (f"{cmd_prefix} drop-prec {self._colour} {limits} "
                    f"{self._max_th} {self._min_th} {self._mark_prob}")
