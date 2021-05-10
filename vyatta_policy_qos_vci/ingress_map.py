#!/usr/bin/env python3
#
# Copyright (c) 2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module that defines the IngressMap class that defines different types
of ingress maps.
"""

import logging
import sys

from traceback import format_tb

LOG = logging.getLogger('Policy QoS VCI')

MIN_PCP = 0
MAX_PCP = 7
MIN_DSCP = 0
MAX_DSCP = 63


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
        """ Compare the original JSON dictionaries of two ingress-maps """
        if self._in_map_dict == ingress_map.in_map_dict:
            if len(self._bindings) == len(ingress_map.bindings):
                status = True
                for index, binding in enumerate(self._bindings):
                    if binding != ingress_map.bindings[index]:
                        status = False

                return status

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

    def check(self, config_dict):
        """ Check to see if this ingress-map is complete """
        status = True
        LOG.debug(f"ingress-map:check - {self._name}")
        if self._map_type is None:
            LOG.debug(f"ingress-map:check map-type not configured")
            status = False

        if self._map_type == 'pcp':
            for pcp in range(MIN_PCP, MAX_PCP+1):
                if self._pcp2des.get(pcp) is None:
                    LOG.debug(f"ingress-map:check pcp-value {pcp} not configured")
                    status = False

        if self._map_type == "dscp-group":
            dscp_values_set = [0] * 64

            try:
                res_dict = config_dict['vyatta-resources-v1:resources']
                misc_dict = res_dict['vyatta-resources-group-misc-v1:group']
                dscp_group_list = misc_dict['vyatta-resources-dscp-group-v1:dscp-group']

                for grp_name, _ in self._dscp_group2des.items():
                    for dscp_group_json in dscp_group_list:
                        if dscp_group_json['group-name'] == grp_name:
                            for dscp_value in dscp_group_json['dscp']:
                                dscp_values_set[int(dscp_value)] += 1

                for dscp_value in range(MIN_DSCP, MAX_DSCP+1):
                    if dscp_values_set[dscp_value] != 1:
                        LOG.debug(f"ingress-map {self._name} has dscp-value "
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
        """ Generate the necessary commands for this ingress map """
        cmd_list = []
        ifname = "ALL"
        cmd_prefix = f"qos global-object-cmd ingress-map {self._name}"
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

        path = f"qos global-object-cmd ingress-map {self._name}"
        cmd = f"qos global-object-cmd ingress-map {self._name} delete"
        ifname = "ALL"
        cmd_list.append((path, cmd, ifname))
        return cmd_list

    def create_binding(self, ifname, vlan_id):
        """ Generate the command to attach this ingress-map to a port/vlan """
        path = f"qos-in-map {ifname} ingress-map {self._name} vlan {vlan_id}"
        cmd = f"qos {ifname} ingress-map {self._name} vlan {vlan_id}"
        return (path, cmd, ifname)

    def delete_binding(self, ifname, vlan_id):
        """ Generate the command to detach an ingress-map from a port/vlan """
        path = f"qos-in-map {ifname} ingress-map {self._name} vlan {vlan_id}"
        cmd = f"qos {ifname} ingress-map {self._name} vlan {vlan_id} delete"
        return (path, cmd, ifname)
