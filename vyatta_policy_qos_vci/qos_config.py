#!/usr/bin/env python3
#
# Copyright (c) 2019-2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
The module that defines the QosConfig class.
"""

import logging

from vyatta_policy_qos_vci.action import Action
from vyatta_policy_qos_vci.ingress_map import IngressMap
from vyatta_policy_qos_vci.egress_map import EgressMap
from vyatta_policy_qos_vci.interface import Interface
from vyatta_policy_qos_vci.interface import get_bonding_members
from vyatta_policy_qos_vci.mark_map import MarkMap
from vyatta_policy_qos_vci.policy import Policy
from vyatta_policy_qos_vci.profile import Profile
from vyatta_policy_qos_vci.platform import PlatformBufferThreshold
from vyatta_policy_qos_vci.platform import PlatformLPDes

LOG = logging.getLogger('Policy QoS VCI')


class QosConfig:
    """
    A class to represent all the chunks of config that QoS is interested in.
    The JSON configuration is broken down into bits that are mapped onto the
    QoS object model.
    """
    def __init__(self, config_dict, client=None):
        """ Create a QosConfig object """
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

    def _process_action(self, action_dict):
        """ Process the action dictionary to create action objects """
        if action_dict is not None:
            action_list = action_dict.get('name')
            if action_list is not None:
                for act_dict in action_list:
                    action = Action(act_dict)
                    self._action_groups[action.name] = action

    def _process_qos(self, qos_dict):
        """
        Process the qos dictionary to create mark-map, global-profile and
        policy objects
        """
        if qos_dict is None:
            return

        # Process platform params
        platform = qos_dict.get('platform')
        if platform is not None:
            buf_thresh = platform.get('buffer-threshold')
            if buf_thresh is not None:
                self._plat_buf_thresh = PlatformBufferThreshold(buf_thresh)
            lp_des = platform.get('priority-local-designation')
            if lp_des is not None:
                self._plat_lp_des = PlatformLPDes(lp_des)

        # Process mark-maps
        mark_maps_list = qos_dict.get('mark-map')
        if mark_maps_list is not None:
            for mark_map_dict in mark_maps_list:
                mark_map = MarkMap(mark_map_dict)
                self._mark_maps[mark_map.name] = mark_map

        # Process global QoS profiles
        global_profiles_list = qos_dict.get('profile')
        if global_profiles_list is not None:
            profile_id = 0
            for profile_dict in global_profiles_list:
                profile = Profile(profile_id, profile_dict, None)
                self._global_profiles[profile.name] = profile
                profile_id += 1

        # Process QoS policies that have been defined
        policy_name_list = qos_dict.get('name')
        if policy_name_list is not None:
            for policy_dict in policy_name_list:
                policy = Policy(policy_dict, self._global_profiles,
                                self._mark_maps)
                self._policies[policy.name] = policy

    def _process_interfaces(self, if_dict, client=None):
        """ Process interfaces that have QoS policies attached to them """
        if if_dict is not None:
            for key, interfaces in if_dict.items():
                if_type = key.split(':')[1]

                if if_type != 'bonding':
                    for interface in interfaces:
                        int_obj = Interface(if_type, interface, self._policies,
                                            self._ingress_maps,
                                            self._egress_maps)
                        self._interfaces[int_obj.ifname] = int_obj
                else:
                    for interface in interfaces:
                        members = get_bonding_members(client, interface)
                        for member in members:
                            int_obj = Interface('bond_member', member,
                                                self._policies,
                                                self._ingress_maps,
                                                self._egress_maps,
                                                bond_dict=interface)
                            LOG.debug('Created Interface obj for member {} of '
                                      'LAG {}'.format(member.get('tagnode'),
                                      interface.get('tagnode')))
                            self._interfaces[int_obj.ifname] = int_obj

    def _process_ingress_map(self, ingress_map_list):
        """ Process the ingress-map list """
        if ingress_map_list is not None:
            for ingress_map_dict in ingress_map_list:
                in_map_obj = IngressMap(ingress_map_dict)
                self._ingress_maps[in_map_obj.name] = in_map_obj

    def _process_egress_map(self, egress_map_list):
        """ Process the egress-map list """
        if egress_map_list is not None:
            for egress_map_dict in egress_map_list:
                eg_map_obj = EgressMap(egress_map_dict)
                self._egress_maps[eg_map_obj.name] = eg_map_obj

    @property
    def interfaces(self):
        """ Return a dictionary of interface objects """
        return self._interfaces

    def find_interface(self, name):
        """ Return the named interface object """
        return self._interfaces.get(name)

    @property
    def global_profiles(self):
        """ Return a list of global QoS profile objects """
        return self._global_profiles

    def find_global_profile(self, name):
        """ Return the named global profile """
        return self._global_profiles.get(name)

    @property
    def policies(self):
        """ Return the dictionary of policy objects """
        return self._policies

    def get_policy(self, name):
        """ Return the named policy object or None """
        return self._policies.get(name)

    @property
    def plat_buf_thresh(self):
        """ Return the platform buffer threshold """
        return self._plat_buf_thresh

    @property
    def plat_lp_des(self):
        """ Return the platform local priority designator """
        return self._plat_lp_des

    @property
    def mark_maps(self):
        """ Return the dictionary of mark-map objects """
        return self._mark_maps

    def get_mark_map(self, name):
        """ Return the named mark-map or None """
        return self._mark_maps.get(name)

    @property
    def action_groups(self):
        """ Return the dictionary of action-group objects """
        return self._action_groups

    def get_action_group(self, name):
        """ Return the named action-group object or None """
        return self._action_groups.get(name)

    @property
    def ingress_maps(self):
        """ Return the dictionary of ingress-map objects """
        return self._ingress_maps

    def get_ingress_map(self, name):
        """ Return the named ingress-map or None """
        return self._ingress_maps.get(name)

    @property
    def egress_maps(self):
        """ Return the dictionary of egress-map objects """
        return self._egress_maps

    def get_egress_map(self, name):
        """ Return the named egress-map or None """
        return self._egress_maps.get(name)
