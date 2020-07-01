#!/usr/bin/env python3
#
# Copyright (c) 2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module that defines the EgressMap class that defines different types
of egress maps.
"""

import logging

LOG = logging.getLogger('Policy QoS VCI')

MIN_DESG = 0
MAX_DESG = 7
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
        designation = egress_map_dict.get('designation')
        self._handle_dscp_pcp_mark(designation)

    def _handle_dscp_pcp_mark(self, dscp_pcp_map_list):
        """ Process a list of designation value to dscp """
        self._des2dscp = {}
        self._des2pcp = {}
        if dscp_pcp_map_list is None:
            return

        try:

            for entry_dict in dscp_pcp_map_list:
                if 'dscp' in entry_dict:
                    self._map_type = 'des2dscp'
                    dscp_mark = entry_dict['dscp']
                    self._des2dscp[entry_dict['id']] = dscp_mark

                if 'pcp' in entry_dict:
                    self._map_type = 'pcp'
                    pcp = entry_dict['pcp']
                    self._des2pcp[entry_dict['id']] = pcp

        except KeyError:
            LOG.error(f"EgressMap missing dscp or pcp data")

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

    def des_dscp_map(self, des):
        """
        Return the appropriate map-tuple for the requested designation
        value
        """
        return self._des2dscp.get(des)

    def des_pcp_map(self, des):
        """
        Return the appropriate map-tuple for the requested designation
        value
        """
        return self._des2pcp.get(des)

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
        cnt = 0
        LOG.debug(f"egress-map:check - {self._name}")
        if self._map_type == 'pcp':
            for des in range(MIN_DESG, MAX_DESG+1):
                if self._des2pcp.get(des) is None:
                    LOG.debug(f"egress-map:check pcp-value {des} not configured")

                else:
                    cnt += 1

        if self._map_type == 'des2dscp':
            for des in range(MIN_DESG, MAX_DESG+1):
                if self._des2dscp.get(des) is None:
                    LOG.debug(f"egress-map:check dscp-value {des} not configured")

                else:
                    cnt += 1

        if cnt == 0:
            LOG.debug(f"egress-map:check Empty egress-map")
            status = False

        return status

    def commands(self):
        """ Generate the necessary commands for this egress map """
        cmd_list = []
        ifname = "ALL"
        cmd_prefix = f"qos global-object-cmd egress-map {self._name}"
        if self._map_type == 'des2dscp':
            for des in range(MIN_DESG, MAX_DESG+1):
                dscp = self._des2dscp.get(des)
                if dscp is None:
                    LOG.error(f"Egress map {self._name} missing DSCP mark value "
                              f"{dscp}")
                else:
                    path = f"{cmd_prefix} designation {des}"
                    cmd = f"{path} dscp {dscp}"
                    cmd_list.append((path, cmd, ifname))

        if self._map_type == 'pcp':
            for des in range(MIN_DESG, MAX_DESG+1):
                pcp = self._des2pcp.get(des)
                if pcp is None:
                    LOG.error(f"Egress map {self._name} missing PCP value "
                              f"{des}")
                else:
                    path = f"{cmd_prefix} designation {des}"
                    cmd = f"{path} pcp {pcp}"
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
