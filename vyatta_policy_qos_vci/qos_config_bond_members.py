#!/usr/bin/env python3
#
# Copyright (c) 2019-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
The module that defines the QosConfigBondMembers class. This class is a
specialization of the QosConfig class that splits the QoS configuration of
bonding groups (LAG) into each individual LAG member.
"""

import logging

from vyatta_policy_qos_vci.qos_config import QosConfig
from vyatta_policy_qos_vci.interface import Interface
from vyatta_policy_qos_vci.interface import get_bonding_members

LOG = logging.getLogger('Policy QoS VCI')


class QosConfigBondMembers(QosConfig):
    """
    A class to represent all the chunks of config that QoS is interested in.
    The JSON configuration is broken down into bits that are mapped onto the
    QoS object model.
    This is a specialization of the QosConfig class. The QoS configuration of
    a bonding groups is split into each bonding member (i.e. cstore commands
    for each bonding member are sent to the dataplane, instead of the
    bonding interface).
    """
    def __init__(self, config_dict, client=None):
        """ Create a QosConfigBondMembers object """
        self._action_groups = {}
        self._mark_maps = {}
        self._global_profiles = {}
        self._ingress_maps = {}
        self._egress_maps = {}
        self._interfaces = {}
        self._policies = {}
        self._plat_buf_thresh = None
        self._plat_lp_des = None

        policy_dict = config_dict.get('vyatta-policy-v1:policy')
        if policy_dict is None:
            return

        action_dict = policy_dict.get('vyatta-policy-action-v1:action')
        self._process_action(action_dict)

        qos_dict = policy_dict.get('vyatta-policy-qos-v1:qos')
        self._process_qos(qos_dict)

        in_map_dict = policy_dict.get('vyatta-policy-qos-v1:ingress-map')
        self._process_ingress_map(in_map_dict)

        eg_map_dict = policy_dict.get('vyatta-policy-qos-v1:egress-map')
        self._process_egress_map(eg_map_dict)

        if_dict = config_dict.get('vyatta-interfaces-v1:interfaces')
        self._process_interfaces(if_dict, client=client)

    def _process_interfaces(self, if_dict, client=None):
        """
        Process interfaces that have QoS policies attached to them, in
        platforms that support the hardware-qos-bond feature
        """
        if if_dict is not None:
            # Process bonding groups first. We have to know all the physical
            # interfaces that are bonding members before processing the other
            # interface types.
            bond_groups = if_dict.get('vyatta-interfaces-bonding-v1:bonding')
            if bond_groups is not None:
                for interface in bond_groups:
                    members = get_bonding_members(client, interface)
                    for member in members:
                        int_obj = Interface('bond_member', member,
                                            self._policies,
                                            self._ingress_maps,
                                            self._egress_maps,
                                            bond_dict=interface)
                        LOG.debug(f"Created Interface obj for member "
                                f"{member.get('tagnode')} of "
                                f"LAG {member.get('tagnode')}")
                        self._interfaces[int_obj.ifname] = int_obj

            # Process all the other interface types
            for key, interfaces in if_dict.items():
                if_type = key.split(':')[1]
                if if_type == 'bonding':
                    # Bonding groups have been already processed
                    continue
                for interface in interfaces:
                    # Check if the interface has been already processed as a
                    # bonding member. If so, ignore it.
                    # The QoS config contains a physical port as a bonding
                    # member and as a dataplane port. This case will happen when
                    # a CLI commit is attaching a QoS policy to a bonding group,
                    # removing a bonding member and attaching another policy to
                    # the dataplane port (former bonding member).
                    # Configd will first apply the QoS config and at this moment
                    # we must favour the QoS policy on the bonding group (i.e.
                    # all its members), ignoring the policy on the dataplane
                    # port.
                    # Once the QoS config has been applied, configd will apply
                    # the bonding configuration, The bonding component will
                    # send a VCI notification to us and it is only then that
                    # the policy on the dataplane port will be processed.
                    ifname = interface.get('tagnode')
                    if self.find_interface(ifname) is not None:
                        continue

                    int_obj = Interface(if_type, interface, self._policies,
                                        self._ingress_maps,
                                        self._egress_maps)
                    self._interfaces[int_obj.ifname] = int_obj

    def add_bond_member(self, if_name, bond_dict):
        """
        Creates an Interface of type 'bond_member' with the provided name
        and bonding group.
        """
        member_dict = {
            'tagnode': if_name,
            'bond-group': bond_dict.get('tagnode')
        }
        interface = Interface('bond_member', member_dict, self._policies,
                              self._ingress_maps, self._egress_maps,
                              bond_dict=bond_dict)
        LOG.debug(f"Created Interface obj for member {if_name} of "
                f"LAG {bond_dict.get('tagnode')}")
        self._interfaces[interface.ifname] = interface
