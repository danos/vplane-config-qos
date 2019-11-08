#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define a block of four TrafficClass objects
"""

from vyatta_policy_qos_vci.traffic_class import TrafficClass
from vyatta_policy_qos_vci.wred_dscp_group import byte_limits

MAX_TRAFFIC_CLASS = 4

def get_default_queue_limit_dict():
    """
    Return the default queue-limit dictionary depending upon whether or not
    the byte-limit if-feature is enabled
    """
    if byte_limits():
        return {"queue-limit-bytes": 65536}

    return {"queue-limit": 64}


class TrafficClassBlock:
    """ Define a block of up to four TrafficClass objects """
    def __init__(self, tc_list, parent_bw_obj):
        """ Create a new traffic-class-block object """
        self._tcs = {}

        if tc_list is not None:
            for tc_dict in tc_list:
                try:
                    # Create a TrafficClass object for each of those specified
                    tc_id = tc_dict['id']
                    self._tcs[tc_id] = TrafficClass(tc_id, tc_dict,
                                                    parent_bw_obj)
                except KeyError:
                    pass

        default_dict = get_default_queue_limit_dict()
        # Create TrafficClass objects for those not specified
        for tc_id in range(0, MAX_TRAFFIC_CLASS):
            try:
                _ = self._tcs[tc_id]

            except KeyError:
                self._tcs[tc_id] = TrafficClass(tc_id, default_dict,
                                                parent_bw_obj)

    def add_pipe_queue(self, tc_id, pipe_queue_id, priority_local):
        """ Add a new pipe-queue to the TC and return queue's wrr-id """
        return self._tcs[tc_id].add_pipe_queue(pipe_queue_id, priority_local)

    def commands(self, cmd_prefix):
        """ Generate commands for this traffic-class-block object """
        cmd_list = []
        _, ifindex, _, subport = cmd_prefix.split()
        for tc_id in range(0, MAX_TRAFFIC_CLASS):
            queue_prefix = f"{cmd_prefix} queue {tc_id}"
            cmd_list.append(self._tcs[tc_id].bandwidth_commands(queue_prefix))
            if "subport" in cmd_prefix:
                cmd = f"qos {ifindex} param subport {subport} {tc_id}"
                cmd += self._tcs[tc_id].queuelimit_commands()

                wred = self._tcs[tc_id].wred
                if wred is not None:
                    cmd += wred.commands()

                cmd_list.append(cmd)

        return cmd_list
