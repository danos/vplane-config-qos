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


class WredMap():
    """ Define the wred-map class """
    def __init__(self, wred_map_dict, is_dscp):
        """ Create a wred-map object """
        self._is_dscp = is_dscp
        if is_dscp:
            self._group_name = wred_map_dict['group-name']
        else:
            self._colour = wred_map_dict['colour']
        self._mark_prob = wred_map_dict['mark-probability']
        self._min_th = wred_map_dict['min-threshold']
        self._max_th = wred_map_dict['max-threshold']

    def commands(self, cmd_prefix):
        """ Generate the necessary command for this wred-map object """
        limits = "bytes" if byte_limits() else "packets"

        if self._is_dscp:
            return (f"{cmd_prefix} dscp-group {self._group_name} {limits} "
                    f"{self._max_th} {self._min_th} {self._mark_prob}")
        else:
            return (f"{cmd_prefix} drop-prec {self._colour} bytes "
                    f"{self._max_th} {self._min_th} {self._mark_prob}")
