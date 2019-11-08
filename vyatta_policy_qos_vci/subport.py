#!/usr/bin/env python3
"""
A module to define the Subport class of object"
"""
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

class Subport:
    """ Define the Subport class """
    def __init__(self, interface, subport_id, vlan_id, policy):
        """ Create a subport object """
        self._interface = interface
        self._id = subport_id
        self._vlan_id = vlan_id
        self._policy = policy

    @property
    def id(self):
        """ Return the subport's id """
        return self._id

    @property
    def vlan_id(self):
        """ Return the subport's vlan tag """
        return self._vlan_id

    @property
    def policy(self):
        """ Return the subport's policy object """
        return self._policy

    def build_profile_index(self, interface):
        """ Build the profile index table for this subport """
        self._policy.shaper.build_profile_index(interface, self._vlan_id)

    def commands(self, interface):
        """ Issue the required 'subport' commands """
        return self._policy.commands(interface, self._id, self._vlan_id)
