#!/usr/bin/env python3
"""
A module to define the Interface class of objects
"""
# Copyright (c) 2019-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

import logging

from vyatta_policy_qos_vci.ingress_map_binding import IngressMapBinding
from vyatta_policy_qos_vci.egress_map_binding import EgressMapBinding
from vyatta_policy_qos_vci.subport import Subport
from vyatta_policy_qos_vci.wred_map import byte_limits

LOG = logging.getLogger('Policy QoS VCI')

POLICY_KEY = {
    # if_type:[name, policy_namespace, vif_namespace, qos_namespace]
    'bonding': ('tagnode', 'vyatta-interfaces-policy-v1', '', 'vyatta-interfaces-bonding-qos-v1',),
    'dataplane': ('tagnode', 'vyatta-interfaces-policy-v1', '', 'vyatta-policy-qos-v1'),
    'vhost': ('name', 'vyatta-interfaces-vhost-policy-v1', 'vyatta-interfaces-vhost-vif-v1:',
              'vyatta-interfaces-vhost-qos-v1'),
    'switch': ('name', 'vyatta-interfaces-switch-vif-policy-v1', '', 'vyatta-policy-qos-v1'),
    'bond_member': ('tagnode', 'vyatta-interfaces-policy-v1', '', 'vyatta-interfaces-bonding-qos-v1'),
}


class MissingBondGroupError(Exception):
    def __init__(self):
        self.message = "bond_group not provided to interface of bond_member type"


class Interface:
    """
    A class for interface objects.  We will have one Interface object for
    each physical port that has QoS configured on it.
    """
    def __init__(self, if_type, if_dict, qos_policy_dict, ingress_map_dict,
                 egress_map_dict, bond_dict=None):
        """
        Create an interface object for a physical port
        if_type is one of "dataplane", "bonding", "vhost", "switch" or
        "bond_member"
        """
        if if_type == 'bond_member' and bond_dict is None:
            raise MissingBondGroupError
        self._if_dict = if_dict
        self._if_type = if_type
        self._bond_dict = bond_dict
        self._subports = []
        self._ingress_map_bindings = []
        self._egress_map_bindings = []
        self._policies = []
        self._profile_index = {}

        if if_type in POLICY_KEY:
            self._name = if_dict.get(POLICY_KEY[if_type][0])
            policy_namespace = POLICY_KEY[if_type][1]
            vif_namespace = POLICY_KEY[if_type][2]
            qos_namespace = POLICY_KEY[if_type][3]
        else:
            self._name = if_dict.get('tagnode')
            policy_namespace = 'vyatta-interfaces-policy-v1'
            vif_namespace = ''
            qos_namespace = ''

        if_policy_dict = None
        port_params_dict = None
        # Get the trunk's QoS policy name
        try:
            if if_type == 'bond_member':
                # Check if policy is on L3 bonding interface
                if_policy_dict = bond_dict[f"{policy_namespace}:policy"]
            else:
                # Try the normal vyatta VM style
                if_policy_dict = if_dict[f"{policy_namespace}:policy"]

        except KeyError:
            try:
                # Try the hardware-switch platform style
                if if_type == 'bond_member':
                    # No policy on L3 bonding interface,
                    # check if policy is on L2 LAG interface
                    # L2 and L3 LAG QoS policies are in different namespaces
                    qos_namespace = 'vyatta-policy-qos-v1'
                    if_policy_dict = bond_dict[
                        'vyatta-interfaces-bonding-switch-v1:switch-group']
                else:
                    if_policy_dict = if_dict[
                        'vyatta-interfaces-dataplane-switch-v1:switch-group']
                port_params_dict = if_policy_dict['port-parameters']
                if_policy_dict = port_params_dict[
                    'vyatta-interfaces-switch-policy-v1:policy']
            except KeyError:
                pass

        # If there is just an ingress map attached at the vif/vlan
        # level then there might be nothing on the interface itself.
        if if_policy_dict is not None:
            try:
                if_policy_name = if_policy_dict.get(f'{qos_namespace}:qos')
                policy = None
                if if_policy_name is not None:
                    policy = qos_policy_dict[if_policy_name]
                    if policy is not None:
                        subport = Subport(self, 0, 0, policy)
                        self._subports.append(subport)
                        # cross-link the policy and the interface
                        self._policies.append(policy)
                        policy.add_interface(self)
            except KeyError:
                # Maybe there is no policy on this interface
                pass

            try:
                ingress_map_name = if_policy_dict['vyatta-policy-qos-v1:ingress-map']
                ingress_map = ingress_map_dict[ingress_map_name]
                binding = IngressMapBinding(self, 0, ingress_map)
                # cross-link the ingress-map and the binding
                self._ingress_map_bindings.append(binding)
                ingress_map.add_binding(binding)

            except KeyError:
                # Maybe there is no ingress map for this interface
                pass

            try:
                egress_map_name = if_policy_dict['vyatta-policy-qos-v1:egress-map']
                egress_map = egress_map_dict[egress_map_name]
                binding = EgressMapBinding(self, 0, egress_map)
                # cross-link the egress-map and the binding
                self._egress_map_bindings.append(binding)
                egress_map.add_binding(binding)

            except KeyError:
                # Maybe there is no egress map for this interface
                pass

        # Look for subports

        # Try the normal vyatta VM style
        vif_list = if_dict.get(f"{vif_namespace}vif")
        if vif_list is not None:
            subport_id = 1
            for vif in vif_list:
                vlan_id = vif['tagnode']
                if_policy_dict = vif[f"{policy_namespace}:policy"]
                try:
                    if_policy_name = if_policy_dict[f'{qos_namespace}:qos']
                    policy = None
                    if if_policy_name is not None:
                        policy = qos_policy_dict[if_policy_name]
                        if policy is not None:
                            subport = Subport(self, subport_id, vlan_id, policy)
                            self._subports.append(subport)
                            # cross-link the policy and interface
                            self._policies.append(policy)
                            policy.add_interface(self)
                            subport_id += 1

                except KeyError:
                    # Maybe there's no policy on this vif
                    pass

                try:
                    ingress_map_name = if_policy_dict['vyatta-policy-qos-v1:ingress-map']
                    ingress_map = ingress_map_dict[ingress_map_name]
                    binding = IngressMapBinding(self, vlan_id, ingress_map)
                    # cross-link the ingress-map and the binding
                    self._ingress_map_bindings.append(binding)
                    ingress_map.add_binding(binding)

                except KeyError:
                    # Maybe there's no ingress map for this vif
                    pass

                try:
                    egress_map_name = if_policy_dict['vyatta-policy-qos-v1:egress-map']
                    egress_map = egress_map_dict[egress_map_name]
                    binding = EgressMapBinding(self, vlan_id, egress_map)
                    # cross-link the egress-map and the binding
                    self._egress_map_bindings.append(binding)
                    egress_map.add_binding(binding)

                except KeyError:
                    # Maybe there's no egress map for this vif
                    pass

        # Try the SIAD hardware-switch platform style
        vlan_list = None
        if port_params_dict is not None:
            try:
                vlan_params_dict = port_params_dict['vlan-parameters']
                qos_params_dict = vlan_params_dict['qos-parameters']
                vlan_list = qos_params_dict['vlan']

            except KeyError:
                pass

        if vlan_list is not None:
            subport_id = 1
            for vlan in vlan_list:
                vlan_id = vlan['vlan-id']
                if_policy_dict = vlan['vyatta-interfaces-switch-policy-v1:policy']
                if_policy_name = if_policy_dict.get(f'{qos_namespace}:qos')
                policy = None
                if if_policy_name is not None:
                    policy = qos_policy_dict[if_policy_name]

                if policy is not None:
                    subport = Subport(self, subport_id, vlan_id, policy)
                    self._subports.append(subport)
                    # cross-link the policy and interface
                    self._policies.append(policy)
                    policy.add_interface(self)
                    subport_id += 1

                try:
                    ingress_map_name = if_policy_dict['vyatta-policy-qos-v1:ingress-map']
                    ingress_map = ingress_map_dict[ingress_map_name]
                    binding = IngressMapBinding(self, vlan_id, ingress_map)
                    # cross-link the ingress-map and the binding
                    self._ingress_map_bindings.append(binding)
                    ingress_map.add_binding(binding)

                except KeyError:
                    # Maybe there's no ingress map for this vlan
                    pass

                try:
                    egress_map_name = if_policy_dict['vyatta-policy-qos-v1:egress-map']
                    egress_map = egress_map_dict[egress_map_name]
                    binding = EgressMapBinding(self, vlan_id, egress_map)
                    # cross-link the egress-map and the binding
                    self._egress_map_bindings.append(binding)
                    egress_map.add_binding(binding)

                except KeyError:
                    # Maybe there's no egress map for this vlan
                    pass

        for subport in self._subports:
            subport.build_profile_index(self)

    def __eq__(self, interface):
        """ Compare the original JSON dictionaires of two interfaces """
        if self._if_type != 'bond_member':
            if self._if_dict == interface.if_dict:
                return True
        else:
            if self._if_dict.get('tagnode') != interface.if_dict.get('tagnode'):
                return False
            if self._if_dict.get('bond-group') != interface.if_dict.get('bond-group'):
                return False
            if self._bond_dict != interface.bond_dict:
                return False
            return True

        return False

    @property
    def if_dict(self):
        """ Return the original JSON for this interface """
        return self._if_dict

    @property
    def bond_dict(self):
        """ Return the original JSON for the bonding group to which this
        interface belongs to
        """
        return self._bond_dict

    @property
    def if_type(self):
        """ Return the interface type for this interface """
        return self._if_type

    @property
    def ifname(self):
        """ Return the name of this interface """
        return self._name

    def profile_index_get(self, key):
        """
        Get the named profile's index.
        Each interface gets a profile-index dictionary built for it.
        The first profile added to the profile-index gets an index of
        zero, the second profile an index of one, and so on.
        The global profiles get added to the dictionary first, and
        hence have the lowest indicies.
        The key for each global profile is "global <profile-name>"
        Then each subport policy on the interface adds its local
        profiles to the profile-index.
        The key for each subport profile is "<vlan-id> <profile-name>".
        The trunk port is identified by vlan-id 0.
        So we could end up with the following profile-index:
        {"global bill": 0,
         "global fred": 1,
         "0 paul": 2,
         "0 bert": 3,
         "10 alan": 4,
         "20 pete": 5}
        """
        return self._profile_index.get(key)

    def profile_index_set(self, key, value):
        """ Set the named profile's index """
        self._profile_index[key] = value

    @property
    def profile_index_size(self):
        """ How many profiles does this interface have? """
        return len(self._profile_index)

    @property
    def policies(self):
        """
        Return the list of policies (trunk and vlan) attached to this
        interface
        """
        return self._policies

    @property
    def ingress_map_bindings(self):
        """
        Return the list of ingress-maps that are bound to this interface or
        any vlans associated with this interface.
        """
        return self._ingress_map_bindings

    @property
    def egress_map_bindings(self):
        """
        Return the list of egress-maps that are bound to this interface or
        any vlans associated with this interface.
        """
        return self._egress_map_bindings

    def commands(self):
        """
        Issue the QoS config to the vyatta-dataplane commands for QoS policy
        attached to this interface.
        """
        cmd_list = []
        cmd_prefix = f"qos {self._name}"
        max_subports = len(self._subports)
        max_pipes = 0
        queue_limit_type = "ql_bytes" if byte_limits() else "ql_packets"

        for subport in self._subports:
            if subport.policy is not None:
                max_pipes = subport.policy.max_pipes(max_pipes)
                # Only the trunk policy on subport 0 has a frame-overhead
                if subport.id == 0:
                    overhead = subport.policy.overhead

        if max_pipes != 0:
            cmd = (f"{cmd_prefix} port subports {max_subports} "
                   f"pipes {max_pipes} profiles {self.profile_index_size} "
                   f"overhead {overhead} {queue_limit_type}")
            cmd_list.append(cmd)

        for subport in self._subports:
            cmd_list += subport.commands(self)

        if max_pipes != 0:
            cmd_list.append(f"{cmd_prefix} enable")

        return cmd_list
