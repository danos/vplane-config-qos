#!/usr/bin/env python3
#
# Copyright (c) 2019, 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define a class of Queue objects
"""

from vyatta_policy_qos_vci.wred_map import WredMap

import logging
LOG = logging.getLogger('Policy QoS VCI')


class Queue:
    """
    Define the Queue class.  A Queue object always defines the tc-id and wrr-id
    of the queue and the queue's wrr-weight.  It may also optionally have its
    priority-local bit set and a number of different wred-maps objects
    attached to it.
    """
    def __init__(self, tc_id, wrr_id, wrr_weight, priority_local, wred_map_dict, qunits, shaper_tc_block):
        """ Create a Queue object """
        self._tc_id = tc_id
        self._wrr_id = wrr_id
        self._wrr_weight = wrr_weight
        self._priority_local = priority_local
        self._wred_maps = []
        self._wred_filter_weight = None

        tc_qlimit = None
        if shaper_tc_block is not None:
            tc_qlimit = shaper_tc_block.get_q_limit(tc_id)

        LOG.debug(f"Queue init tc_id {tc_id} wrr_id {wrr_id} weight {wrr_weight} lpq {priority_local}\n")
        if wred_map_dict is not None:
            self._wred_filter_weight = wred_map_dict['filter-weight']
            try:
                dscp_group_list = wred_map_dict['dscp-group']
                for wred_group_dict in dscp_group_list:
                    self._wred_maps.append(WredMap(wred_group_dict, 1,
                                                   qunits, tc_qlimit))

            except KeyError:
                pass

            try:
                drop_prec_list = wred_map_dict['drop-precedence']
                for wred_dp_dict in drop_prec_list:
                    self._wred_maps.append(WredMap(wred_dp_dict, 0,
                                                   qunits, tc_qlimit))

            except KeyError:
                pass

    @property
    def tc_id(self):
        """ Return the queue's traffic-class id """
        return self._tc_id

    @property
    def wrr_id(self):
        """ Return the queue's wrr queue id """
        return self._wrr_id

    @property
    def wrr_weight(self):
        """ Return the queue's wrr weight """
        return self._wrr_weight

    @property
    def priority_local(self):
        """ Return whether or not this is the priority-local queue """
        return self._priority_local

    def check(self, path_prefix):
        """ Check if configuration is valid """
        for wred_map in self._wred_maps:
            result, error, path = wred_map.check(path_prefix)
            if not result:
                return result, error, path

        return True, None, None

    def commands(self, cmd_prefix, pipe_queue_id):
        """ Generate the necessary commands for this Queue object """
        cmd_list = []

        qmap = (self._wrr_id << 2 | self._tc_id)
        if qmap != 0:
            qmap = hex(qmap)

        cmd_prefix = f"{cmd_prefix} queue {qmap}"

        cmd = f"{cmd_prefix} wrr-weight {self._wrr_weight} {pipe_queue_id}"
        if self._priority_local:
            cmd += " prio-loc"

        cmd_list.append(cmd)

        # Add any wred-map commands
        for wred_map in self._wred_maps:
            cmd_list.append(wred_map.commands(cmd_prefix))

        if self._wred_filter_weight is not None:
            cmd = f"{cmd_prefix} wred-weight {self._wred_filter_weight}"
            cmd_list.append(cmd)

        return cmd_list
