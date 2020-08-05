#!/usr/bin/env python3
#
# Copyright (c) 2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
The module that defines objects to hold platform wide params.
"""

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
