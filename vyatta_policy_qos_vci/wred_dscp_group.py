#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define a class of Wred Dscp-Group objects
"""

from pathlib import Path

def byte_limits():
    """ Check the feature file to see if we are using byte or packet limits? """
    byte_limit_feature = Path(
        "/run/vyatta-platform/features/vyatta-policy-qos-groupings-v1/byte-limits")
    return byte_limit_feature.is_file()


class WredDscpGroup():
    """ Define the wred-dscp-group class """
    def __init__(self, wred_group_dict):
        """ Create a wred-dscp-group object """
        self._group_name = wred_group_dict['group-name']
        self._mark_prob = wred_group_dict['mark-probability']
        self._min_th = wred_group_dict['min-threshold']
        self._max_th = wred_group_dict['max-threshold']

    def commands(self, cmd_prefix):
        """ Generate the necessary command for this wred-dscp-group object """
        limits = "bytes" if byte_limits() else "packets"

        return (f"{cmd_prefix} dscp-group {self._group_name} {limits} "
                f"{self._max_th} {self._min_th} {self._mark_prob}")
