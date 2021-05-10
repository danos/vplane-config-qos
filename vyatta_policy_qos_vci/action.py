#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
The module that defines the Action class.
"""

from vyatta_policy_qos_vci.dscp import str2dscp
from vyatta_policy_qos_vci.policer import Policer


class Action:
    """
    A class to represent QoS action groups.
    """
    def __init__(self, action_dict):
        """ Create an action-group object """
        self._action_dict = action_dict
        self._name = action_dict['id']
        self._pcp_mark = None
        self._pcp_inner = "none"
        self._dscp_mark = None
        self._policer = None

        mark_dict = action_dict.get('mark')
        if mark_dict is not None:
            if mark_dict.get('pcp-inner') is not None:
                self._pcp_inner = "inner"
            self._pcp_mark = mark_dict.get('pcp')
            dscp = mark_dict.get('dscp')
            if dscp is not None:
                self._dscp_mark = str2dscp(dscp)

            # Yang allows a pcp and dscp mark simulatenously but the
            # npf-cfg add action-group command just sets the pcp mark

        police_dict = action_dict.get('police')
        if police_dict is not None:
            self._policer = Policer(police_dict)

    def __eq__(self, action_group):
        """ Compare the original JSON of two action groups """
        return self._action_dict == action_group.action_dict

    @property
    def action_dict(self):
        """
        Return the original JSON that was used to create this action group
        """
        return self._action_dict

    @property
    def name(self):
        """ Return the name of this action group """
        return self._name

    def rproc(self):
        """ Generate the necessary NPF rproc command for this action group """
        mark = None
        policer = None

        if self._dscp_mark is not None:
            mark = f"markdscp({self._dscp_mark})"

        if self._pcp_mark is not None:
            mark = f"markpcp({self._pcp_mark},{self._pcp_inner})"

        if self._policer is not None:
            policer = self._policer.commands()

        if mark is not None and policer is not None:
            return f"rproc={mark};{policer}"

        if mark is not None and policer is None:
            return f"rproc={mark}"

        if mark is None and policer is not None:
            return f"rproc={policer}"

        return None

    def commands(self):
        """ Generate the necessary path and command for this action group """
        cmd_list = []
        rproc = self.rproc()
        if rproc is not None:
            path = f"policy action name {self._name}"
            cmd = f"npf-cfg add action-group:{self._name} 0 {rproc}"
            ifname = "ALL"
            cmd_list.append((path, cmd, ifname))

        return cmd_list

    def delete_cmd(self):
        """
        Generate the necessary path and command to delete this action-group
        """
        cmd_list = []
        path = f"policy action name {self._name}"
        cmd = f"npf-cfg delete action-group:{self._name}"
        ifname = "ALL"
        cmd_list.append((path, cmd, ifname))

        return cmd_list
