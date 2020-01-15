#!/usr/bin/env python3
"""
A module to define the binding between an ingress map and a port/vlan
"""
# Copyright (c) 2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

class IngressMapBinding:
    """ Define the IngressMapBinding class """
    def __init__(self, interface, vlan_id, ingress_map):
        """ Create an ingress-map-binding object """
        self._interface = interface
        self._ingress_map = ingress_map
        self._vlan_id = vlan_id

    def create_binding(self):
        """
        Return the path, command tuple necessary to bind this ingress-map
        to the interface/vlan.
        """
        return self._ingress_map.create_binding(self._interface.ifindex,
                                                self._vlan_id)

    def delete_binding(self):
        """
        Return the path, command tuple necessary to unbind this ingress-map
        from the interface/vlan.
        """
        return self._ingress_map.delete_binding(self._interface.ifindex,
                                                self._vlan_id)
