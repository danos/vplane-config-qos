#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define Policy objects
"""

from vyatta_policy_qos_vci.shaper import Shaper


class Policy:
    """ A class for policy objects """
    def __init__(self, policy_dict, global_profiles, mark_maps):
        """ Create a policy object """
        # fields set up during initialization
        self._policy_dict = policy_dict
        self._name = policy_dict['id']

        # fields set up later, after initialization
        self._interfaces = []

        shaper_dict = policy_dict['shaper']
        self._shaper = Shaper(shaper_dict, global_profiles, mark_maps)

    def __eq__(self, policy):
        """ Compare the original JSON of two policies """
        if self._policy_dict == policy.policy_dict:
            return True

        return False

    @property
    def policy_dict(self):
        """ Return the original JSON for this policy """
        return self._policy_dict

    @property
    def name(self):
        """ Return the name of the policy """
        return self._name

    @property
    def shaper(self):
        """ Return the policy's shaper object """
        return self._shaper

    def max_pipes(self, max_pipes):
        """ How many pipes does this policy use? """
        if self._shaper.max_pipes > max_pipes:
            max_pipes = self._shaper.max_pipes

        return max_pipes

    def max_profiles(self, max_profiles):
        """ How many profiles does this policy have? """
        if self._shaper.max_profiles > max_profiles:
            max_profiles = self._shaper.max_profiles

        return max_profiles

    @property
    def interfaces(self):
        """ Return the list of interfaces attached to this policy """
        return self._interfaces

    @property
    def overhead(self):
        """ Return the policy's frame-overhead """
        return self._shaper.overhead

    def check(self, path_prefix):
        """ Check if policy configuration is valid """
        return self._shaper.check(path_prefix)

    def commands(self, interface, subport_id, vlan_id):
        """ Generate the commands required by this policy object """
        return self._shaper.commands(interface, subport_id, vlan_id)

    def add_interface(self, interface):
        """
        Add the interface object to the list of interfaces using this policy
        """
        self._interfaces.append(interface)

    def delete_interface(self, interface):
        """
        Remove the interface object from the list of interfaces using this
        policy
        """
        try:
            self._interfaces.remove(interface)

        except ValueError:
            pass
