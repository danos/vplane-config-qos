#!/usr/bin/env python3
#
# Copyright (c) 2019-2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define Profile objects
"""

from vyatta_policy_qos_vci.bandwidth import Bandwidth
from vyatta_policy_qos_vci.profile_map import ProfileMap
from vyatta_policy_qos_vci.pipe_queue import PipeQueues
from vyatta_policy_qos_vci.traffic_class_block import TrafficClassBlock

PERIOD_DEFAULT_MS = 10

class Profile:
    """
    Define the Profile class.  A Profile object accumulates all the
    traffic-class, mapping information and pipe-queues.
    Profiles can either be local to a policy, or global and therefore can
    be used by multiple policies.
    """
    def __init__(self, profile_id, profile_dict, parent_bw):
        """ Create a profile object """
        self._profile_dict = profile_dict
        self._id = profile_id
        self._profile_name = profile_dict.get('id')
        self._bandwidth = Bandwidth(profile_dict, parent_bw)
        self._period = profile_dict.get('period')
        if self._period is not None:
            # period now specified in microseconds
            self._period = int(self._period) * 1000
        else:
            self._period = profile_dict.get('micro-seconds-period')
            if self._period is not None:
                self._period = int(self._period)
            else:
                self._period = PERIOD_DEFAULT_MS * 1000

        # _shapers only used for global profiles
        self._shapers = []

        tc_list = profile_dict.get('traffic-class')
        self._tcs = TrafficClassBlock(tc_list, self._bandwidth)

        self._policy_map = None

        # Cross-link the pipe-queues to the traffic-classes to generate the
        # traffic-classes's wrr-queues
        self._pipe_queues = PipeQueues(profile_dict.get("queue"), self._tcs)

        map_dict = profile_dict.get("map")
        if map_dict is not None:
            dscp_group = map_dict.get('dscp-group')
            dscp = map_dict.get('dscp')
            pcp = map_dict.get('pcp')
            designation = map_dict.get('designation')
            self._policy_map = ProfileMap(self, dscp_group, dscp, pcp,
                                          designation)

    def __eq__(self, profile):
        """ Compare the original JSON of two profiles """
        return self._profile_dict == profile.profile_dict

    @property
    def profile_dict(self):
        """ Return the original JSON for this profile """
        return self._profile_dict

    @property
    def id(self):
        """ Return the profile's id """
        return self._id

    @id.setter
    def id(self, value):
        """ Set the profile's id """
        self._id = value

    @property
    def name(self):
        """ Return the profile's name """
        return self._profile_name

    @property
    def pipe_queues(self):
        """ Return this profile's pipe queue object """
        return self._pipe_queues

    @property
    def shapers(self):
        """ Return the list of shapers using this global profile """
        return self._shapers

    def commands(self, cmd_prefix, interface, vlan_id):
        """ Generate the list of profile commands """
        profile_key = f"{vlan_id} {self._profile_name}"
        profile_id = interface.profile_index_get(profile_key)
        cmd_prefix = f"{cmd_prefix} {profile_id}"
        cmd_list = []
        period = PERIOD_DEFAULT_MS
        if self._period is not None:
            period = self._period
        cmd_list.append(self._bandwidth.commands(cmd_prefix, period))
        cmd_list = cmd_list + self._tcs.commands(cmd_prefix)
        if self._policy_map is not None:
            cmd_list = cmd_list + self._policy_map.commands(cmd_prefix)
        cmd_list = cmd_list + self._pipe_queues.commands(cmd_prefix)
        return cmd_list
