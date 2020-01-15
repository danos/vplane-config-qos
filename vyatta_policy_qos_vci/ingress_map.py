#!/usr/bin/env python3
#
# Copyright (c) 2020, AT&T Intellectual Property.
# All rights reserved.
"""
A module that defines the IngressMap class that defines different types
of ingress maps.
"""

import logging

LOG = logging.getLogger('Policy QoS VCI')

MIN_PCP = 0
MAX_PCP = 7

class IngressMap:
    """
    The IngressMap class provides two different types of mappings:
    1: dscp-group-name to designation
    2: pcp-values to designation
    Only one of these mappings can be used by any IngressMap object.
    If we hae any IngressMaps, then one of them must be marked as the
    system-default.
    """
    def __init__(self, ingress_map_dict):
        """ Create an ingress-map object """
        self._in_map_dict = ingress_map_dict
        self._drop_precedence = [0, 0, 0, 0, 0, 0, 0, 0]
        self._name = ingress_map_dict['id']
        self._map_type = None
        self._bindings = []
        pcp = ingress_map_dict.get('pcp')
        dscp_group = ingress_map_dict.get('dscp-group')
        self._handle_pcp(pcp)
        self._handle_dscp_group(dscp_group)
        self._system_default = ingress_map_dict.get('system-default')

    def _handle_dscp_group(self, dscp_group_map_list):
        """ Process a list of dscp-group names to designations """
        self._dscp_group_map = {}
        if dscp_group_map_list is None:
            return

        try:
            self._map_type = 'dscp-group'
            for entry_dict in dscp_group_map_list:
                designation = entry_dict['designation']
                self._dscp_group_map[entry_dict['id']] = designation
                self._drop_precedence[designation] += 1

        except KeyError:
            LOG.error("IngressMap missing dscp-group data")


    def _handle_pcp(self, pcp_map_list):
        """ Process a list of pcp-values to designations """
        self._pcp_map = {}
        if pcp_map_list is None:
            return

        try:
            self._map_type = 'pcp'
            for entry_dict in pcp_map_list:
                designation = entry_dict['designation']
                self._pcp_map[entry_dict['id']] = designation
                self._drop_precedence[designation] += 1

        except KeyError:
            LOG.error("IngressMap missing pcp data")

    def __eq__(self, ingress_map):
        """ Compare the original JSON dictionaries of two interfaces """
        if self._in_map_dict == ingress_map.in_map_dict:
            return True

        return False

    @property
    def name(self):
        """ Return this ingress-map's name """
        return self._name

    @property
    def in_map_dict(self):
        """ Return the original JSON for this ingress-map """
        return self._in_map_dict

    def dscp_group_map(self, dscp_group_name):
        """
        Return the appropriate map-tuple for the requested dscp-group name
        """
        return self._dscp_group_map.get(dscp_group_name)

    def pcp_map(self, pcp):
        """ Return the appropriate map-tuple for the requested pcp value """
        return self._pcp_map.get(pcp)

    def add_binding(self, binding):
        """
        Add the binding to the list of bindings using this ingress map
        """
        self._bindings.append(binding)

    @property
    def bindings(self):
        """
        Return the list of bindings that this ingress map is attached to
        """
        return self._bindings

    def commands(self):
        """ Generate the necessary commands for this ingress map """
        cmd_list = []
        cmd_prefix = f"qos 0 ingress-map {self._name}"
        if self._map_type == 'dscp-group':
            dscp_group_names = sorted(self._dscp_group_map.keys())
            for dscp_group_name in dscp_group_names:
                designation = self._dscp_group_map[dscp_group_name]
                path = f"{cmd_prefix} dscp-group {dscp_group_name}"
                cmd = f"{path} designation {designation}"
                cmd_list.append((path, cmd))

        if self._map_type == 'pcp':
            for pcp in range(MIN_PCP, MAX_PCP+1):
                designation = self._pcp_map[pcp]
                path = f"{cmd_prefix} pcp {pcp}"
                cmd = f"{path} designation {designation}"
                cmd_list.append((path, cmd))

        if self._system_default is not None:
            path = cmd = f"{cmd_prefix} system-default"
            cmd_list.append((path, cmd))

        return cmd_list

    def delete_cmd(self):
        """
        Generate the necessary path and command to delete this ingress-map
        """
        path = f"qos 0 ingress-map {self._name}"
        cmd = f"qos 0 ingress-map {self._name} delete"
        return (path, cmd)

    def create_binding(self, ifindex, vlan_id):
        """ Generate the command to attach this ingress-map to a port/vlan """
        path = f"qos-in-map {ifindex} ingress-map {self._name} vlan {vlan_id}"
        cmd = f"qos {ifindex} ingress-map {self._name} vlan {vlan_id}"
        return (path, cmd)

    def delete_binding(self, ifindex, vlan_id):
        """ Generate the command to detach an ingress-map from a port/vlan """
        path = f"qos-in-map {ifindex} ingress-map {self._name} vlan {vlan_id}"
        cmd = f"qos {ifindex} ingress-map {self._name} vlan {vlan_id} delete"
        return (path, cmd)
