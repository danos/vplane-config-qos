#!/usr/bin/env python3
# Copyright (c) 2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module that defines the IngressMapBinding class which provides the linkage
between IngressMap objects and the Interfaces and vlans that they are attached
to.
"""


class IngressMapBinding:
    """ Define the IngressMapBinding class """
    def __init__(self, interface, vlan_id, ingress_map):
        """ Create an ingress-map-binding object """
        self._interface = interface
        self._ingress_map = ingress_map
        self._vlan_id = vlan_id

    def __eq__(self, binding):
        """
        Return true if the two bindings go to the same interface and vlan
        """
        if self._interface.ifname == binding.interface.ifname and self._vlan_id == binding.vlan_id:
            return True

        return False

    @property
    def interface(self):
        """ Return the interface that this binding connects to """
        return self._interface

    @property
    def vlan_id(self):
        """ Return the vlan-id that this binding connects to """
        return self._vlan_id

    def create_binding(self):
        """
        Return the path, command, ifname tuple necessary to bind this ingress-map
        to the interface/vlan.
        """
        return self._ingress_map.create_binding(self._interface.ifname,
                                                self._vlan_id)

    def delete_binding(self):
        """
        Return the path, command, ifname tuple necessary to unbind this ingress-map
        from the interface/vlan.
        """
        return self._ingress_map.delete_binding(self._interface.ifname,
                                                self._vlan_id)
