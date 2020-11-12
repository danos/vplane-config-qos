#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define the TrafficClass class
"""

from vyatta_policy_qos_vci.bandwidth import Bandwidth
from vyatta_policy_qos_vci.wred import Wred
from vyatta_policy_qos_vci.wred_map import get_limit_time

class TrafficClass:
    """
    Define the TrafficClass class.  A TrafficClass object defines its share
    of the parent bandwidth, its maximum queue length and any WRED
    configuration.  It also keeps a record of all the pipe-queues that are
    assigned to it.
    """
    def __init__(self, tc_id, tc_dict, parent_bw_obj):
        """ Create a traffic-class object """
        self._id = tc_id
        self._wred = None
        self._queue_limit_time = None

        if tc_dict is not None:
            self._queue_limit_bytes = tc_dict.get('queue-limit-bytes')
            self._queue_limit_packets = tc_dict.get('queue-limit')
            self._queue_limit_time = get_limit_time(tc_dict.get('queue-limit-time'), 1)

            wred_dict = tc_dict.get('random-detect')
            if wred_dict is not None:
                self._wred = Wred(wred_dict)

        self._bandwidth = Bandwidth(tc_dict, parent_bw_obj)
        self._pipe_queue_list = []

    @property
    def id(self):
        """ Return the traffic-class id """
        return self._id

    @property
    def queue_limit(self):
        """ Return the traffic-class's queue-limit """
        if self._queue_limit_bytes is not None:
            return self._queue_limit_bytes

        if self._queue_limit_time is not None:
            return self._queue_limit_time

        if self._queue_limit_packets is not None:
            return self._queue_limit_packets

        return None

    @property
    def wred(self):
        """ Return the traffic-class's wred object if is exists """
        return self._wred

    def add_pipe_queue(self, pipe_queue_id, priority_local):
        """
        Add a new pipe queue to this traffic-class and return it's wrr-id
        """
        wrr_id = len(self._pipe_queue_list)
        self._pipe_queue_list.append(pipe_queue_id)

        # Don't use qindex 0 for the local queue so it is always separate
        # from default
        if priority_local is not None and wrr_id == 0:
            wrr_id += 1

        return wrr_id

    def checks(self):
        """ Sanity check this object """
        # Can't have both queue-limit-packets and queue-limit-bytes
        if self._queue_limit_packets is not None and self._queue_limit_bytes is not None:
            return False

        # traffic-class wred is SW-only
        if self._queue_limit_bytes is not None and self._wred is not None:
            return False

        return True

    def bandwidth_commands(self, cmd_prefix):
        """ Generate this traffic-class's bandwidth commands """
        return self._bandwidth.commands(cmd_prefix, None)

    def queuelimit_commands(self):
        """ Generate this traffic-class's queue-limit commands """
        if self._queue_limit_bytes is not None:
            return f" limit bytes {self._queue_limit_bytes}"

        if self._queue_limit_time is not None:
            return f" limit usec {self._queue_limit_time}"

        if self._queue_limit_packets is not None:
            return f" limit packets {self._queue_limit_packets}"

        return ""
