#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define the Bandwidth class of objects
"""

import logging
import re

from vyatta_policy_qos_vci.policer import parse_bandwidth

LOG = logging.getLogger('Policy QoS VCI')

DEFAULT_BURST_MS = 4


class Bandwidth:
    """ A class for bandwidth objects """
    def __init__(self, config_dict, parent_bw_obj):
        """
        Create a bandwidth object and calculate its bandwidth in
        bytes-per-second (which may be a percentage of a parent bandwidth
        object).  Calculate a default burst size in bytes if it isn't
        defined.
        """
        bandwidth = None
        self._burst = None
        self._burst_msec = None
        self._bps = 0
        self._percent = None
        self._auto = False

        if config_dict is not None:
            bandwidth = config_dict.get('bandwidth')
            self._burst = config_dict.get('burst')

        if bandwidth is None:
            bandwidth = '100%'
        search_obj = re.search(r'^([0-9]*\.?[0-9]+)%$', bandwidth, flags=0)
        if search_obj:
            self._percent = search_obj.group(1)
            if parent_bw_obj is not None:
                self._bps = int(parent_bw_obj.bps * int(search_obj.group(1)) / 100)
        else:
            if parent_bw_obj is None:
                if bandwidth == 'auto':
                    self._auto = True
                else:
                    self._bps = parse_bandwidth(bandwidth)
            else:
                self._bps = parse_bandwidth(bandwidth)

        if self._burst is None:
            self._burst_msec = DEFAULT_BURST_MS
        else:
            burst_str = str(self._burst)
            search_obj = re.search(r'^([0-9]*\.?[0-9]+)ms[ec]*$', burst_str,
                                   flags=0)
            if search_obj:
                self._burst_msec = search_obj.group(1)
                self._burst = None

    @property
    def bps(self):
        """
        Return the actual bandwidth in bytes-per-second or Zero if percentage
        bandwidth is being used.
        """
        return self._bps

    def commands(self, cmd_prefix, period):
        """ Return the required command strings for this bandwidth object """
        if self._percent is None:
            if self._auto:
                cmd = f"{cmd_prefix} auto"
            else:
                cmd = f"{cmd_prefix} rate {self._bps}"
        else:
            cmd = f"{cmd_prefix} percent {self._percent}"

        if self._burst_msec is not None:
            cmd += f" msec {self._burst_msec}"
        else:
            cmd += f" size {self._burst}"

        if period is not None:
            cmd += f" period {period}"

        return cmd
