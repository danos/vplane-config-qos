#!/usr/bin/env python3
#
# Copyright (c) 2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
The module that defines the BondMembership class, which represents the
system's LAG membership state.
"""

import logging
import subprocess
import json

LOG = logging.getLogger('Policy QoS VCI')


class BondMembership:
    """
    Class that represents the system's LAG membership state. The membership
    state can be obtained either from the kernel or from a VCI notification from
    the LAG component. If 'notification' is not provided to the constructor,
    this object will obtain the LAG membership from the kernel.
    """
    def __init__(self, notification=None):
        """
        If 'notification' is not provided, the LAG membership will be obtained
        from the kernel.
        """
        if notification is None:
            self._membership = self._translate_membership(
                    self._fetch_membership())
        else:
            self._membership = self._translate_notification(notification)

    def refresh(self):
        """ Refreshes LAG membership state by fetching it from the kernel """
        self._membership = self._translate_membership(self._fetch_membership())

    def get_membership(self):
        """ Returns the LAG membership cache """
        return self._membership

    def get_bond_groups(self):
        """ Returns the list of bonding groups in the cache """
        if self._membership is None:
            return None
        bond_groups = []
        for bond_group in self._membership:
            bond_groups.append(bond_group)

        return bond_groups

    def get_members(self, bond):
        """ Returns the list of members of the provided bonding group """
        return self._membership.get(bond)

    def _fetch_bond_groups(self):
        """ Fetches from the kernel the list of bonding groups """
        shell_output = subprocess.check_output(['ls', '-1', '/sys/class/net/'])
        interfaces = shell_output.decode('ascii').split('\n')
        LOG.debug(f"kernel interfaces: {interfaces}")
        bond_groups = []
        for interface in interfaces:
            if 'bond' in interface:
                bond_groups.append(interface)
        return bond_groups

    def _fetch_membership(self):
        """ Fetches from the kernel the LAG membership state """
        membership = {}
        bond_groups = self._fetch_bond_groups()
        for bond in bond_groups:
            members = []
            membership[bond] = members
            shell_output = subprocess.check_output(['teamdctl', bond, 'config',
                'dump', 'actual'])
            shell_dict = json.loads(shell_output.decode('ascii'))
            LOG.debug(f"bond group {bond} state from kernel: {shell_dict}")
            ports = shell_dict.get('ports', {})
            for port in ports:
                members.append(port)
        return membership

    @staticmethod
    def _translate_membership(membership):
        """
        Builds the membership cache from the membership fetched from the kernel.
        Each member interface must be represented by a dictionary.
        """
        cache = {}
        for bond, members in membership.items():
            cache[bond] = []
            for member in members:
                if_dict = BondMembership._build_if_dict(bond, member)
                cache[bond].append(if_dict)
        return cache

    @staticmethod
    def _build_if_dict(bond_name, member_name):
        """ Builds an interface dictionary according to the YANG model """
        if_dict = {}
        if_dict['tagnode'] = member_name
        if_dict['bond-group'] = bond_name
        return if_dict

    @staticmethod
    def _translate_notification(notification):
        """
        Translates the membership from a VCI notification. Returns the
        membership in the format that this class stores in its cache.
        """
        membership = {}
        bond_groups = \
            notification.get('vyatta-interfaces-bonding-v1:bond-groups')
        for bond_group in bond_groups:
            bond_name = bond_group.get('bond-group')
            bond_members = bond_group.get('bond-members')
            membership[bond_name] = []
            for bond_member in bond_members:
                if_dict = BondMembership._build_if_dict(bond_name, bond_member)
                membership[bond_name].append(if_dict)
        return membership
