#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define a QoS "Class" objects
"""

from vyatta_policy_qos_vci.rule import Rule

class Class:
    """
    Define the QoS "Class" class.  A QoS class object defines the linkage
    between a QoS class number, its match rules and the profile that
    is applied to packets that conform to the match rules.
    """
    def __init__(self, class_dict):
        """ Create a QoS class object """
        self._id = class_dict.get('id')
        self._profile_name = class_dict.get('profile')
        self._rules = []
        match_list = class_dict.get('match')
        if match_list is not None:
            for rule in match_list:
                self._rules.append(Rule(self._id, rule))

    @property
    def profile_name(self):
        """ Return the profile name that it attached to this qos class """
        return self._profile_name

    def commands(self, interface, cmd_prefix, subport_id, vlan_id):
        """ Generate the necessary QoS config commands for this class object """
        cmd_list = []
        # add the class/pipe to profile mapping
        profile_key = f"{vlan_id} {self._profile_name}"
        profile_id = interface.profile_index_get(profile_key)

        cmd_list.append(f"{cmd_prefix} pipe {subport_id} {self._id} "
                        f"{profile_id}")

        for rule in self._rules:
            cmd_list.append(f"{cmd_prefix} match {subport_id} {self._id} "
                            f"{rule.commands()}")
        return cmd_list
