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
    1: dscp-group-name to designation/drop-precedence
    2: pcp-values to designation/drop-precedence
    Only one of these mappings can be used by any IngressMap object.
    If we have any IngressMaps, then one of them must be marked as the
    system-default.
    """
    def __init__(self, ingress_map_dict):
        """ Create an ingress-map object """
        self._in_map_dict = ingress_map_dict
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
        self._dscp_group2des = {}
        self._dscp_group2dp = {}
        if dscp_group_map_list is None:
            return

        try:
            self._map_type = 'dscp-group'
            for entry_dict in dscp_group_map_list:
                designation = entry_dict['designation']
                drop_prec = entry_dict['drop-precedence']
                self._dscp_group2des[entry_dict['id']] = designation
                self._dscp_group2dp[entry_dict['id']] = drop_prec

        except KeyError:
            LOG.error("IngressMap missing dscp-group data")


    def _handle_pcp(self, pcp_map_list):
        """ Process a list of pcp-values to designations """
        self._pcp2des = {}
        self._pcp2dp = {}
        if pcp_map_list is None:
            return

        try:
            self._map_type = 'pcp'
            for entry_dict in pcp_map_list:
                designation = entry_dict['designation']
                drop_prec = entry_dict['drop-precedence']
                self._pcp2des[entry_dict['id']] = designation
                self._pcp2dp[entry_dict['id']] = drop_prec

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

    @property
    def system_default(self):
        """ Is this ingress-map the system default? """
        if self._system_default is not None:
            return True

        return False

    def dscp_group_map(self, dscp_group_name):
        """
        Return the appropriate map-tuple for the requested dscp-group name
        """
        return self._dscp_group2des.get(dscp_group_name)

    def pcp_map(self, pcp):
        """ Return the appropriate map-tuple for the requested pcp value """
        return self._pcp2des.get(pcp)

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
        ifname = "ALL"
        cmd_prefix = f"qos 0 ingress-map {self._name}"
        if self._map_type == 'dscp-group':
            dscp_group_names = sorted(self._dscp_group2des.keys())
            for dscp_group_name in dscp_group_names:
                designation = self._dscp_group2des[dscp_group_name]
                drop_prec = self._dscp_group2dp[dscp_group_name]
                path = f"{cmd_prefix} dscp-group {dscp_group_name}"
                cmd = f"{path} designation {designation} drop-prec {drop_prec}"
                cmd_list.append((path, cmd, ifname))

        if self._map_type == 'pcp':
            for pcp in range(MIN_PCP, MAX_PCP+1):
                designation = self._pcp2des.get(pcp)
                drop_prec = self._pcp2dp.get(pcp)
                if designation is None or drop_prec is None:
                    LOG.error(f"Ingress map {self._name} missing PCP value "
                              f"{pcp}")
                else:
                    path = f"{cmd_prefix} pcp {pcp}"
                    cmd = f"{path} designation {designation} drop-prec {drop_prec}"
                    cmd_list.append((path, cmd, ifname))

        if self._system_default is not None:
            path = cmd = f"{cmd_prefix} system-default"
            cmd_list.append((path, cmd, ifname))

        path = cmd = f"{cmd_prefix} complete"
        cmd_list.append((path, cmd, ifname))
        # Add the commands required to bind this ingress map to any port/vlan
        # that it has been associated with
        for binding in self._bindings:
            cmd_list.append(binding.create_binding())

        return cmd_list

    def delete_cmd(self):
        """
        Generate the necessary path and command to delete this ingress-map
        """
        # Since we are about to delete this ingress-map we must break all
        # the bindings that it has with any interfaces/vlans
        cmd_list = []
        for binding in self._bindings:
            cmd_list.append(binding.delete_binding())

        path = f"qos 0 ingress-map {self._name}"
        cmd = f"qos 0 ingress-map {self._name} delete"
        ifname = "ALL"
        cmd_list.append((path, cmd, ifname))
        return cmd_list

    def create_binding(self, ifname, ifindex, vlan_id):
        """ Generate the command to attach this ingress-map to a port/vlan """
        path = f"qos-in-map {ifindex} ingress-map {self._name} vlan {vlan_id}"
        cmd = f"qos {ifindex} ingress-map {self._name} vlan {vlan_id}"
        return (path, cmd, ifname)

    def delete_binding(self, ifname, ifindex, vlan_id):
        """ Generate the command to detach an ingress-map from a port/vlan """
        path = f"qos-in-map {ifindex} ingress-map {self._name} vlan {vlan_id}"
        cmd = f"qos {ifindex} ingress-map {self._name} vlan {vlan_id} delete"
        return (path, cmd, ifname)
