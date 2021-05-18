#!/usr/bin/env python3
#
# Copyright (c) 2020-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
The module that defines objects to hold platform wide params.
"""

from pathlib import Path


def is_hardware_qos_bond_enabled():
    """ Check the feature file to see if hardware-qos-bond is enabled """
    hardware_qos_bond_feature = Path(
        "/run/vyatta-platform/features/vyatta-policy-qos-v1/hardware-qos-bond")
    return hardware_qos_bond_feature.is_file()


class PlatformBufferThreshold:
    """
    Platform wide buffer threshold parameter
    """
    def __init__(self, buffer_threshold):
        """ Create a platform buffer threshold object """
        self._buffer_threshold = buffer_threshold

    @property
    def threshold(self):
        """ Return the value of the param """
        return self._buffer_threshold

    def __eq__(self, buf_thresh):
        if buf_thresh is None:
            return False
        return self._buffer_threshold == buf_thresh.threshold

    def delete_cmd(self):
        """ Generate the necessary path and command to delete this object """
        cmd_list = []
        path = f"qos buffer-threshold"
        cmd = f"qos global-object-cmd platform buffer-threshold 0 delete"
        ifname = "ALL"
        cmd_list.append((path, cmd, ifname))
        return cmd_list

    def commands(self):
        cmd_list = []

        if self._buffer_threshold is not None:
            path = f"qos buffer-threshold"
            cmd = (f"qos global-object-cmd platform buffer-threshold "
                   f"{self._buffer_threshold}")
            ifname = "ALL"
            cmd_list.append((path, cmd, ifname))

        return cmd_list


class PlatformLPDes:
    """
    Platform wide local priority designator parameter
    """
    def __init__(self, lp_des):
        """ Create an object """
        self._local_prio_des = lp_des

    @property
    def designation(self):
        """ Return the value of the param """
        return self._local_prio_des

    def __eq__(self, lp_des):
        if lp_des is None:
            return False
        return self._local_prio_des == lp_des.designation

    def delete_cmd(self):
        """ Generate the necessary path and command to delete this object """
        cmd_list = []
        path = f"qos lp-des"
        cmd = f"qos global-object-cmd lp-des delete"
        ifname = "ALL"
        cmd_list.append((path, cmd, ifname))
        return cmd_list

    def commands(self):
        cmd_list = []

        if self._local_prio_des is not None:
            path = f"qos lp-des"
            cmd = f"qos global-object-cmd lp-des {self._local_prio_des}"
            ifname = "ALL"
            cmd_list.append((path, cmd, ifname))

        return cmd_list
