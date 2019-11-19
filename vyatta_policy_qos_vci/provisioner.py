#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define the provisioner class.

It is responsible for comparing the new configuration against the
old configuration and working out what objects needs to be deleted,
what objects needs to be updated, and what objects need to be
created.

Once it has figured out the changes, it write QoS and NPF
vyatta-dataplane configuration commands to vplaned's cstore.
"""

import logging
import json

from vyatta_policy_qos_vci.qos_config import QosConfig

LOG = logging.getLogger('Policy QoS VCI')

POLICY_QOS_CONFIG_FILE = '/etc/vyatta/policy-qos.json'

def get_existing_config():
    """ Try to return the existing JSON QoS configuration """
    existing_config = {}
    try:
        with open(POLICY_QOS_CONFIG_FILE) as json_data:
            existing_config = json.load(json_data)

    except OSError:
        pass

    except json.JSONDecodeError:
        LOG.error(f"Failed to decode JSON config file {POLICY_QOS_CONFIG_FILE}")

    return existing_config


def save_new_config(new_config):
    """ Save the new JSON QoS configuration to the QoS config file """
    with open(POLICY_QOS_CONFIG_FILE, "w") as write_file:
        write_file.write(json.dumps(new_config, indent=4, sort_keys=True))


class Provisioner:
    """
    Define the provisioner class.  The provisioner object has to determine what
    has changed (if anything) between the old configuration and the new one.
    Based on the changes it decides which interfaces need to disabled and
    then re-enabled with the new configuration.  Changes to global objects
    like global profiles, mark-maps or action-groups make affect multiple
    interfaces.
    """
    def __init__(self, old, new):
        """ Create a provisioner object """
        self._if_deletes = []
        self._if_updates = []
        self._if_creates = []

        self._obj_delete = []
        self._obj_update = []
        self._obj_create = []

        old_config = QosConfig(old)
        new_config = QosConfig(new)

        self._check_interfaces(old_config, new_config)
        self._check_policies(old_config, new_config)
        self._check_global_profiles(old_config, new_config)
        self._check_mark_maps(old_config, new_config)
        self._check_action_groups(old_config, new_config)

    def _check_interfaces(self, old_config, new_config):
        """ Check for any changes to interface config """
        for name, interface in new_config.interfaces.items():
            old_interface = old_config.find_interface(name)
            if old_interface is not None:
                if interface != old_interface:
                    # This interface has been modified
                    self._if_updates.append(interface)
            else:
                # We have a new interface
                self._if_creates.append(interface)

        for name, interface in old_config.interfaces.items():
            new_interface = new_config.find_interface(name)
            if new_interface is None:
                self._if_deletes.append(interface)

    def _check_policies(self, old_config, new_config):
        """ Check for any changes to policy config """
        for policy in new_config.policies.values():
            old_policy = old_config.get_policy(policy.name)
            if old_policy is not None:
                if policy != old_policy:
                    for interface in policy.interfaces:
                        if interface not in self._if_updates:
                            self._if_updates.append(interface)
            else:
                # A new policy that might not be attached to an interface
                for interface in policy.interfaces:
                    # Update if the interface is not on _if_creates list
                    if interface not in self._if_creates:
                        self._if_updates.append(interface)

    def _check_global_profiles(self, old_config, new_config):
        """ Check for any changes to global profiles """
        for name, profile in new_config.global_profiles.items():
            old_profile = old_config.find_global_profile(name)
            if old_profile is not None and profile != old_profile:
                # Is this global-profile being used by any shaper?
                for interface in new_config.interfaces.values():
                    for policy in interface.policies:
                        if policy.shaper.get_profile_id(name) is not None:
                            if interface not in self._if_updates:
                                self._if_updates.append(interface)

    def _check_mark_maps(self, old_config, new_config):
        """ Check for any changes to mark-maps """
        for mark_map in new_config.mark_maps.values():
            old_mark_map = old_config.get_mark_map(mark_map.name)
            if old_mark_map is not None:
                # We have an existing mark-map, has it changed?
                if mark_map != old_mark_map:
                    # It has so delete the old, and create the new
                    self._obj_delete.append(old_mark_map)
                    self._obj_create.append(mark_map)
            else:
                # We have a new mark-map
                self._obj_create.append(mark_map)

        for mark_map in old_config.mark_maps.values():
            new_mark_map = new_config.get_mark_map(mark_map.name)
            if new_mark_map is None:
                # Delete the old mark-map
                self._obj_delete.append(mark_map)

    def _check_action_groups(self, old_config, new_config):
        """ Check for any changes to action-groups """
        for action_group in new_config.action_groups.values():
            old_action_group = old_config.get_action_group(action_group.name)
            if old_action_group is not None:
                # We have an existing action-group, has it changed?
                if action_group != old_action_group:
                    # It has changed, delete the old, create the new
                    self._obj_delete.append(old_action_group)
                    self._obj_create.append(action_group)
            else:
                # We have a new action-group
                self._obj_create.append(action_group)

        for action_group in old_config.action_groups.values():
            new_action_group = new_config.get_action_group(action_group.name)
            if new_action_group is None:
                # Delete the old action-group
                self._obj_delete.append(action_group)

    def _detach_policy(self, ctrl, interface):
        """
        Detach the QoS policy from the specified interface.
        """
        key = f"qos {interface.ifindex}"
        cmd = f"{key} disable"
        for dataplane in ctrl.get_dataplanes():
            with dataplane:
                ctrl.store(key, cmd, interface.name, action="DELETE")

    def _delete_interfaces(self, ctrl):
        """
        Disable QoS policies from all the interfaces on the deletes list
        """
        for interface in self._if_deletes:
            self._detach_policy(ctrl, interface)

    def _attach_policy(self, ctrl, interface):
        """
        Attach a QoS policy to the specified interface
        """
        key = f"qos {interface.ifindex}"
        for dataplane in ctrl.get_dataplanes():
            with dataplane:
                for cmd in interface.commands():
                    path = f"{key} {cmd}"
                    ctrl.store(path, cmd, interface.name, "SET")

    def _create_interfaces(self, ctrl):
        """
        Attach QoS policies to interfaces that didn't have them before
        """
        for interface in self._if_creates:
            self._attach_policy(ctrl, interface)

    def _update_interfaces(self, ctrl):
        """
        Update the interfaces with modified QoS policies, by first detaching the
        old policy, then attaching the new policy
        """
        cmd_list = []
        for interface in self._if_updates:
            self._detach_policy(ctrl, interface)
            self._attach_policy(ctrl, interface)

        return cmd_list

    def _delete_objects(self, ctrl):
        """ Delete any old mark-maps or action-groups"""
        for dataplane in ctrl.get_dataplanes():
            with dataplane:
                for obj in self._obj_delete:
                    (path, cmd) = obj.delete_cmd()
                    ctrl.store(path, cmd, "ALL", "DELETE")

    def _create_objects(self, ctrl):
        """ Create any new or modified mark-maps or action-groups"""
        for dataplane in ctrl.get_dataplanes():
            with dataplane:
                for obj in self._obj_create:
                    for (path, cmd) in obj.commands():
                        ctrl.store(path, cmd, "ALL", "SET")

    def _qos_commit(self, ctrl):
        """
        Send the final 'qos commit' command to tell the vyatta-dataplane that
        this batch of commands is complete.
        """
        for dataplane in ctrl.get_dataplanes():
            with dataplane:
                ctrl.store("qos commit", "qos commit", "ALL", "SET")

    def commands(self, ctrl):
        """
        Write the necessary commands to vplaned's cstore to delete, modify
        and create the required QoS objects
        """
        self._delete_objects(ctrl)
        self._create_objects(ctrl)
        self._delete_interfaces(ctrl)
        self._update_interfaces(ctrl)
        self._create_interfaces(ctrl)
        self._qos_commit(ctrl)