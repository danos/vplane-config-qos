#!/usr/bin/env python3
# Copyright (c) 2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module that defines the EgressMapBinding class which provides the linkage
between EgressMap objects and the Interfaces and vlans that they are attached
to.
"""

class EgressMapBinding:
    """ Define the EgressMapBinding class """
    def __init__(self, interface, vlan_id, egress_map):
        """ Create an egress-map-binding object """
        self._interface = interface
        self._egress_map = egress_map
        self._vlan_id = vlan_id
        self._ifname = ""

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
        Return the path, command, ifname tuple necessary to bind this egress-map
        to the interface/vlan.
        """
        if self._interface.if_type == 'switch' or self._interface.if_type == 'dataplane' and self._vlan_id != 0:
            self._ifname = self._interface.ifname + '.' + str(self._vlan_id)
        else:
            self._ifname = self._interface.ifname
        return self._egress_map.create_binding(self._ifname, self._vlan_id)

    def delete_binding(self):
        """
        Return the path, command, ifname tuple necessary to unbind this egress-map
        from the interface/vlan.
        """
        if self._interface.if_type == 'switch' or self._interface.if_type == 'dataplane' and self._vlan_id != 0:
            self._ifname = self._interface.ifname + '.' + str(self._vlan_id)
        else:
            self._ifname = self._interface.ifname
        return self._egress_map.delete_binding(self._ifname, self._vlan_id)
