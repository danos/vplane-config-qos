#!/usr/bin/env python3
#
# Copyright (c) 2019-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define the mark_map class
"""


class MarkMap:
    """
    Define the MarkMap class
    """
    def __init__(self, map_dict):
        """ Create a mark-map object """
        self._map_dict = map_dict
        self._name = map_dict['id']
        self._dscp_groups = {}
        self._des_mappings = {}
        self._shapers = []

        dscp_group_list = map_dict.get('dscp-group')
        if dscp_group_list is not None:
            for dscp_group in dscp_group_list:
                group_name = dscp_group['group-name']
                pcp_mark = dscp_group['pcp-mark']
                self._dscp_groups[group_name] = pcp_mark

        # Designation mappings can be either
        #  Des->PCP
        #     or
        #  Des/DP->PCP
        designation_list = map_dict.get('designation')
        if designation_list is not None:
            for designation in designation_list:
                des = designation['designation-type']
                pcp_mark = designation.get('pcp-mark')
                if pcp_mark is None:
                    dp_list = designation['drop-precedence']
                    for drop_prec in dp_list:
                        dp = drop_prec['colour']
                        pcp_mark = drop_prec['pcp-mark']
                        self._des_mappings[des, dp] = pcp_mark
                else:
                    self._des_mappings[des, 'green'] = pcp_mark
                    self._des_mappings[des, 'yellow'] = pcp_mark
                    self._des_mappings[des, 'red'] = pcp_mark

    def __eq__(self, mark_map):
        """ Compare the JSON of two mark-maps """
        return self._map_dict == mark_map.map_dict

    @property
    def map_dict(self):
        """ Return the original JSON for this mark-map """
        return self._map_dict

    @property
    def name(self):
        """ Return the name of this mark-map """
        return self._name

    @property
    def dscp_group_names(self):
        """ Return the list of dscp-group names """
        return self._dscp_groups.keys()

    def pcp(self, group_name):
        """ Return the pcp-mark value for the named group """
        return self._dscp_groups[group_name]

    @property
    def shapers(self):
        """ Return the list of shapers using this mark-map """
        return self._shapers

    def commands(self):
        """ Generate the necessary paths and commands for this mark-map """
        cmd_list = []
        if self._dscp_groups:
            for group_name, pcp_mark in sorted(self._dscp_groups.items()):
                path = f"qos mark-map {self._name} dscp-group {group_name}"
                cmd = (f"qos global-object-cmd mark-map {self._name} dscp-group {group_name} "
                       f"pcp {pcp_mark}")
                ifname = "ALL"
                cmd_list.append((path, cmd, ifname))

        if self._des_mappings:
            for des, dp in self._des_mappings:
                pcp_mark = self._des_mappings[des, dp]

                path = f"qos mark-map {self._name} designation {des} drop-prec {dp}"
                cmd = (f"qos global-object-cmd mark-map {self._name} designation {des} drop-prec {dp} "
                       f"pcp {pcp_mark}")
                ifname = "ALL"
                cmd_list.append((path, cmd, ifname))

        return cmd_list

    def delete_cmd(self):
        """ Generate the necessary path and command to delete this mark-map """
        cmd_list = []
        path = f"qos mark-map {self._name}"
        cmd = f"qos global-object-cmd mark-map {self._name} delete"
        ifname = "ALL"
        cmd_list.append((path, cmd, ifname))
        return cmd_list
