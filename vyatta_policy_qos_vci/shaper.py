#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
The module to define the Shaper class
"""

from vyatta_policy_qos_vci.bandwidth import Bandwidth
from vyatta_policy_qos_vci.qclass import Class
from vyatta_policy_qos_vci.profile import Profile
from vyatta_policy_qos_vci.traffic_class_block import TrafficClassBlock

PERIOD_DEFAULT_MS = 40

class Shaper:
    """ Define the shaper class """
    def __init__(self, policy_name, shaper_dict, global_profiles, mark_maps):
        """ Create a shaper object """
        self._global_profiles = global_profiles
        self._classes = []
        self._local_profiles = {}
        self._profile_index = {}

        self._bandwidth = Bandwidth(shaper_dict, None)
        self._default = shaper_dict.get('default')

        for name, global_profile in global_profiles.items():
            if name == self._default:
                global_profile.shapers.append(self)

        self._overhead = shaper_dict.get('frame-overhead')
        self._period = shaper_dict.get('period')
        self._mark_map = shaper_dict.get('mark-map')
        if self._mark_map is not None:
            mark_map = mark_maps.get(self._mark_map)
            if mark_map is not None:
                mark_map.shapers.append(self)

        if self._period is None:
            self._period = PERIOD_DEFAULT_MS

        class_list = shaper_dict.get('class')
        if class_list is not None:
            for class_item in class_list:
                qos_class = Class(policy_name, class_item)
                self._classes.append(qos_class)
                for name, global_profile in global_profiles.items():
                    if name == qos_class.profile_name:
                        global_profile.shapers.append(self)

        profile_id = len(global_profiles)
        profile_list = shaper_dict.get('profile')
        if profile_list is not None:
            for profile_dict in profile_list:
                profile = Profile(profile_id, profile_dict, self._bandwidth)
                self._local_profiles[profile.name] = profile
                profile_id += 1

        tc_list = shaper_dict.get('traffic-class')
        self._tcs = TrafficClassBlock(tc_list, self._bandwidth)

    @property
    def max_pipes(self):
        """ Return the number of pipes that this shaper uses """
        # + 1 for the default class
        return len(self._classes) + 1

    @property
    def max_profiles(self):
        """ Return the number of profiles that this shaper references """
        return len(self._global_profiles) + len(self._local_profiles)

    @property
    def overhead(self):
        """ Return the size of this shaper's frame overhead """
        return self._overhead

    def build_profile_index(self, interface, vlan_id):
        """ Add the shaper's profiles to the interface's profile index """
        # First check to see if any global profiles need added
        base_pid = 0
        for profile_name in self._global_profiles.keys():
            key = f"global {profile_name}"

            if interface.profile_index_get(key) is None:
                interface.profile_index_set(key, base_pid)
                base_pid += 1

        # Now add the local profiles
        index = 0
        for profile_name in self._local_profiles.keys():
            # Check for a global profile
            key = f"global {profile_name}"
            pid = interface.profile_index_get(key)
            if pid is None:
                # Get the next free profile index
                pid = interface.profile_index_size

            key = f"{vlan_id} {profile_name}"
            interface.profile_index_set(key, pid)
            index += 1

    def get_profile_id(self, profile_name):
        """ Return the named profile's profile id """
        profile = self._global_profiles.get(profile_name)
        if profile is not None:
            return profile.id

        profile = self._local_profiles.get(profile_name)
        if profile is not None:
            return profile.id

        return None

    def commands(self, interface, subport_id, vlan_id):
        """ Generate the shaper's commands """
        cmd_prefix = f"qos {interface.ifindex}"
        subport_prefix = f"{cmd_prefix} subport {subport_id}"

        cmd_list = []
        cmd_list.append(self._bandwidth.commands(subport_prefix, self._period))
        cmd_list.extend(self._tcs.commands(subport_prefix))

        # Add the mark-map command if necessary
        if self._mark_map is not None:
            cmd_list.append(f"{subport_prefix} mark-map {self._mark_map}")

        # vlan to subport mapping
        cmd_list.append(f"{cmd_prefix} vlan {vlan_id} {subport_id}")

        # add vlan profiles
        profile_prefix = f"{cmd_prefix} profile"

        for name, profile in self._local_profiles.items():
            if name == self._default:
                cmd_list += profile.commands(profile_prefix, interface, vlan_id)
                break

        for name, profile in self._local_profiles.items():
            if name != self._default:
                cmd_list += profile.commands(profile_prefix, interface, vlan_id)

        # add global profiles
        for profile in self._global_profiles.values():
            cmd_list += profile.commands(profile_prefix, interface, "global")

        # mapping default profile
        default_profile_key = f"{vlan_id} {self._default}"
        default_profile_id = interface.profile_index_get(default_profile_key)
        if default_profile_id is None:
            default_profile_key = f"global {self._default}"
            default_profile_id = interface.profile_index_get(default_profile_key)
        cmd_list.append(f"{cmd_prefix} pipe {subport_id} 0 {default_profile_id}")
        for class_item in self._classes:
            cmd_list += class_item.commands(interface, cmd_prefix, subport_id,
                                            vlan_id)

        return cmd_list
