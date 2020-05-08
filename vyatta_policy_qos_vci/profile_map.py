#!/usr/bin/env python3
#
# Copyright (c) 2019-2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module that defines the ProfileMap class that defines different types
of profile maps.
"""

import logging

from vyatta_policy_qos_vci.dscp import dscp_range

LOG = logging.getLogger('Policy QoS VCI')

MIN_PCP = 0
MAX_PCP = 7
MIN_DSCP = 0
MAX_DSCP = 63
MIN_DESIGNATION = 0
MAX_DESIGNATION = 7

class ProfileMap:
    """
    The ProfileMap class provides four different types of mappings:
    1: dscp-group-name to pipe-queue-id
    2: dscp-value to pipe-queue-id
    3: pcp-value to pipe-queue-id
    4: designation to pipe-queue-id
    only one of these mappings can be used by any ProfileMap object.
    """
    def __init__(self, parent_profile, dscp_group, dscp, pcp, designation):
        """ Create a profile-map object """
        self._parent_profile = parent_profile
        self._map_type = None
        self._drop_precedence = {}
        self._next_dp = {}
        self._handle_dscp_group(dscp_group)
        self._handle_dscp(dscp)
        self._handle_pcp(pcp)
        self._handle_designation(designation)

    def _handle_dscp_group(self, dscp_group_map_list):
        """ Process a list of dscp-group names to pipe-queue-ids """
        self._dscp_group_map = {}
        if dscp_group_map_list is None:
            return

        try:
            self._map_type = 'dscp-group'
            for entry_dict in dscp_group_map_list:
                if entry_dict['to'] not in self._next_dp:
                    drop_precedence = 0
                    self._next_dp[entry_dict['to']] = 1
                else:
                    drop_precedence = self._next_dp[entry_dict['to']]
                    self._next_dp[entry_dict['to']] = drop_precedence + 1

                self._dscp_group_map[entry_dict['group-name']] = entry_dict['to']
                self._drop_precedence[entry_dict['group-name']] = drop_precedence


        except KeyError:
            LOG.error("ProfileMap missing dscp-group data")

    def _handle_dscp(self, dscp_map_list):
        """ Process a list of dscp-values to pipe-queue-ids """
        self._dscp_map = {}
        if dscp_map_list is None:
            return

        try:
            self._map_type = 'dscp'
            for entry_dict in dscp_map_list:
                dscp_values = dscp_range(entry_dict['id'])
                for dscp in dscp_values:
                    self._dscp_map[dscp] = entry_dict['to']

        except KeyError:
            LOG.error("ProfileMap missing dscp data")

    def _handle_pcp(self, pcp_map_list):
        """ Process a list of pcp-values to pipe-queue-ids """
        self._pcp_map = {}
        if pcp_map_list is None:
            return

        try:
            self._map_type = 'pcp'
            for entry_dict in pcp_map_list:
                self._pcp_map[entry_dict['id']] = entry_dict['to']

        except KeyError:
            LOG.error("ProfileMap missing pcp data")

    def _handle_designation(self, designation_map_list):
        """ Process a list of designation-values to pipe-queue-ids """
        self._designation_map = {}
        if designation_map_list is None:
            return

        try:
            self._map_type = 'designation'
            for entry_dict in designation_map_list:
                if entry_dict['to'] not in self._next_dp:
                    drop_precedence = 0
                    self._next_dp[entry_dict['to']] = 1
                else:
                    drop_precedence = self._next_dp[entry_dict['to']]
                    self._next_dp[entry_dict['to']] = drop_precedence + 1

                self._designation_map[entry_dict['id']] = entry_dict['to']
                self._drop_precedence[entry_dict['id']] = drop_precedence

        except KeyError:
            LOG.error("ProfileMap missing designation data")

    @property
    def map_type(self):
        """ Return this profile-map's map-type """
        return self._map_type

    def dscp_group_map(self, dscp_group_name):
        """
        Return the appropriate map-tuple for the requested dscp-group name
        """
        return self._dscp_group_map.get(dscp_group_name)

    def dscp_map(self, dscp):
        """ Return the appropriate map-tuple for the requested dscp value """
        return self._dscp_map.get(dscp)

    def pcp_map(self, pcp):
        """ Return the appropriate map-tuple for the requested pcp value """
        return self._pcp_map.get(pcp)

    def designation_map(self, designation):
        """
        Return the appropriate map-tuple for the requested designation value
        """
        return self._designation_map.get(designation)

    def commands(self, cmd_prefix):
        """ Generate the necessary commands for this profile map """
        cmd_list = []
        pipe_queues = self._parent_profile.pipe_queues

        if self._map_type == 'dscp-group':
            dscp_group_names = sorted(self._dscp_group_map.keys())
            for dscp_group_name in dscp_group_names:
                try:
                    pipe_queue_id = self._dscp_group_map[dscp_group_name]
                    dp = self._drop_precedence[dscp_group_name]
                    queue = pipe_queues.pipe_queue(pipe_queue_id)
                    qmap = (dp << 5 | queue.wrr_id << 2 | queue.tc_id)
                    cmd_list.append(f"{cmd_prefix} dscp-group {dscp_group_name}"
                                    f" {hex(qmap)}")

                except KeyError:
                    pass

        if self._map_type == 'dscp':
            for dscp in range(MIN_DSCP, MAX_DSCP+1):
                try:
                    pipe_queue_id = self._dscp_map[dscp]
                    # drop-precedence always 0 for numeric dscp maps
                    queue = pipe_queues.pipe_queue(pipe_queue_id)
                    qmap = (queue.wrr_id << 2 | queue.tc_id)
                    cmd_list.append(f"{cmd_prefix} dscp {dscp} {hex(qmap)}")

                except KeyError:
                    pass

        if self._map_type == 'pcp':
            for pcp in range(MIN_PCP, MAX_PCP+1):
                try:
                    pipe_queue_id = self._pcp_map[pcp]
                    queue = pipe_queues.pipe_queue(pipe_queue_id)
                    tc_id = queue.tc_id
                    wrr_id = queue.wrr_id

                except KeyError:
                    # Provide the default mapping for unconfigured pcp values
                    tc_id = int((MAX_PCP - pcp) / 2)
                    wrr_id = 0

                # drop-precedence always 0 for pcp maps
                qmap = (wrr_id << 2 | tc_id)
                cmd_list.append(f"{cmd_prefix} pcp {pcp} {hex(qmap)}")

        if self._map_type == 'designation':
            for designation in range(MIN_DESIGNATION, MAX_DESIGNATION+1):
                try:
                    pipe_queue_id = self._designation_map[designation]
                    dp = self._drop_precedence[designation]
                    queue = pipe_queues.pipe_queue(pipe_queue_id)
                    tc_id = queue.tc_id
                    wrr_id = queue.wrr_id
                    qmap = (dp << 5 | wrr_id << 2 | tc_id)
                    cmd_list.append(f"{cmd_prefix} designation {designation} "
                                    f"queue {hex(qmap)}")
                except KeyError:
                    pass

        return cmd_list
