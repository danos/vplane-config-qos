#!/usr/bin/env python3
#
# Copyright (c) 2020-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module that defines the EgressMap class that defines different types
of egress maps.
"""

import logging
import sys

from traceback import format_tb

LOG = logging.getLogger('Policy QoS VCI')

MIN_DSCP = 0
MAX_DSCP = 63


class EgressMap:
    """
    The EgressMap class provides two different types of mappings:
    1: designation to dscp
    2: designation to pcp
    Only one of these mappings can be used by any EgressMap object.
    """
    def __init__(self, egress_map_dict):
        """ Create an egress-map object """
        self._eg_map_dict = egress_map_dict
        self._name = egress_map_dict['id']
        self._map_type = None
        self._bindings = []
        self._dscp_groups = {}
        dscp_group_list = egress_map_dict.get('dscp-group')
        self._handle_dscp_mark(dscp_group_list)

    def _handle_dscp_mark(self, dscp_grp_list):
        """ Process a list of dscp-group list to egress dscp """
        self._dscpgrp2dscp = {}
        if dscp_grp_list is None:
            return

        try:
            self._map_type = 'dscpgrp2dscp'
            for entry_dict in dscp_grp_list:
                dscp_mark = entry_dict['dscp']
                self._dscpgrp2dscp[entry_dict['id']] = dscp_mark

        except KeyError:
            LOG.error(f"EgressMap missing dscp data")

    def __eq__(self, egress_map):
        """ Compare the original JSON dictionaries of two egress-maps """
        if self._eg_map_dict == egress_map.eg_map_dict:
            if len(self._bindings) == len(egress_map.bindings):
                status = True
                for index, binding in enumerate(self._bindings):
                    if binding != egress_map.bindings[index]:
                        status = False

                return status

        return False

    @property
    def name(self):
        """ Return this egress-map's name """
        return self._name

    @property
    def eg_map_dict(self):
        """ Return the original JSON for this egress-map """
        return self._eg_map_dict

    def dscpgrp_dscp_map(self, dscp):
        """
        Return the appropriate map-tuple for the requested dscp value
        """
        return self._dscpgrp2dscp.get(dscp)

    def add_binding(self, binding):
        """
        Add the binding to the list of bindings using this egress map
        """
        self._bindings.append(binding)

    @property
    def bindings(self):
        """
        Return the list of bindings that this egress map is attached to
        """
        return self._bindings

    def check(self, config_dict):
        """ Check to see if this egress-map is complete """
        status = True
        LOG.debug(f"egress-map:check - {self._name}")
        if self._map_type is None:
            LOG.debug(f"egress-map:check map-type not configured")
            status = False

        if self._map_type == "dscpgrp2dscp":
            dscp_values_set = [0] * 64

            try:
                res_dict = config_dict['vyatta-resources-v1:resources']
                misc_dict = res_dict['vyatta-resources-group-misc-v1:group']
                dscp_group_list = misc_dict['vyatta-resources-dscp-group-v1:dscp-group']

                for grp_name, _ in self._dscpgrp2dscp.items():
                    for dscp_group_json in dscp_group_list:
                        if dscp_group_json['group-name'] == grp_name:
                            for dscp_value in dscp_group_json['dscp']:
                                dscp_values_set[int(dscp_value)] += 1

                for dscp_value in range(MIN_DSCP, MAX_DSCP+1):
                    if dscp_values_set[dscp_value] != 1:
                        LOG.debug(f"egress-map {self._name} has dscp-value "
                                  f"{dscp_value} assigned "
                                  f"{dscp_values_set[dscp_value]} times")
                        status = False

            except KeyError:
                LOG.debug(f"failed to find {sys.exc_info()[1]} in config")
                status = False

            except Exception:
                tb_type = sys.exc_info()[0]
                tb_value = sys.exc_info()[1]
                tb_info = format_tb(sys.exc_info()[2])
                tb_output = ""
                for line in tb_info:
                    tb_output += line

                LOG.error(f"Unhandled exception: {tb_type}\n{tb_value}\n{tb_output}")
                status = False

        return status

    def commands(self):
        """ Generate the necessary commands for this egress map """
        cmd_list = []
        ifname = "ALL"
        cmd_prefix = f"qos global-object-cmd egress-map {self._name}"
        dscp_group_names = sorted(self._dscpgrp2dscp.keys())
        for dscp_group_name in dscp_group_names:
            dscp_mark = self._dscpgrp2dscp[dscp_group_name]
            path = f"{cmd_prefix} dscp-group {dscp_group_name}"
            cmd = f"{path} dscp {dscp_mark}"
            cmd_list.append((path, cmd, ifname))

        path = cmd = f"{cmd_prefix} complete"
        cmd_list.append((path, cmd, ifname))
        # Add the commands required to bind this egress map to any port/vlan
        # that it has been associated with
        for binding in self._bindings:
            cmd_list.append(binding.create_binding())

        return cmd_list

    def delete_cmd(self):
        """
        Generate the necessary path and command to delete this egress-map
        """
        # Since we are about to delete this egress-map we must break all
        # the bindings that it has with any interfaces/vlans
        cmd_list = []
        for binding in self._bindings:
            cmd_list.append(binding.delete_binding())

        path = f"qos global-object-cmd egress-map {self._name}"
        cmd = f"qos global-object-cmd egress-map {self._name} delete"
        ifname = "ALL"
        cmd_list.append((path, cmd, ifname))
        return cmd_list

    def create_binding(self, ifname, vlan_id):
        """ Generate the command to attach this egress-map to a port/vlan """
        path = f"qos-in-map {ifname} egress-map {self._name} vlan {vlan_id}"
        cmd = f"qos {ifname} egress-map {self._name} vlan {vlan_id}"
        return (path, cmd, ifname)

    def delete_binding(self, ifname, vlan_id):
        """ Generate the command to detach an egress-map from a port/vlan """
        path = f"qos-in-map {ifname} egress-map {self._name} vlan {vlan_id}"
        cmd = f"qos {ifname} egress-map {self._name} vlan {vlan_id} delete"
        return (path, cmd, ifname)
