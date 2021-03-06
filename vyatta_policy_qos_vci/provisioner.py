#!/usr/bin/env python3
#
# Copyright (c) 2019-2020, AT&T Intellectual Property.
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
import sys

from vyatta_policy_qos_vci.qos_config import QosConfig
from vyatta_policy_qos_vci.qos_config_bond_members import QosConfigBondMembers
from vyatta_policy_qos_vci.interface import get_bond_dict, get_dataplane_if_dict

LOG = logging.getLogger('Policy QoS VCI')


#
# We have single config file that contains all the config information that
# QoS VCI was able to apply at the last commit point.
#
POLICY_QOS_CONFIG_FILE = '/etc/vyatta/policy-qos.json'


def get_config():
    """ Try to return a JSON QoS configuration file """
    filename = POLICY_QOS_CONFIG_FILE
    config = {}
    try:
        with open(filename) as json_data:
            config = json.load(json_data)

    except OSError:
        LOG.info(f"Failed to open JSON config file {filename} {sys.exc_info()[0]}")

    except json.JSONDecodeError:
        LOG.error(f"Failed to decode JSON config file {filename}")

    return config


def save_config(config):
    """ Save the JSON QoS configuration to the appropriate QoS config file """
    filename = POLICY_QOS_CONFIG_FILE
    with open(filename, "w") as write_file:
        write_file.write(json.dumps(config, indent=4, sort_keys=True))


class Provisioner:
    """
    Define the provisioner class.  The provisioner object has to determine what
    has changed (if anything) between the old configuration and the new one.
    Based on the changes it decides which interfaces need to disabled and
    then re-enabled with the new configuration.  Changes to global objects
    like global profiles, mark-maps or action-groups may affect multiple
    interfaces.
    """
    def __init__(self, old, new, bonding_ntfy=None, client=None):
        """ Create a provisioner object """
        self._is_hardware_qos_bond_enabled = bonding_ntfy is not None or \
                                             client is not None
        self._if_deletes = []
        self._if_updates = []
        self._if_creates = []
        self._in_map_deferred = []
        self._eg_map_deferred = []

        self._obj_delete = []
        self._obj_update = []
        self._obj_create = []

        # Now process the QoS config
        if bonding_ntfy is None:
            if self._is_hardware_qos_bond_enabled:
                old_config = QosConfigBondMembers(old, client=client)
                new_config = QosConfigBondMembers(new, client=client)
            else:
                old_config = QosConfig(old)
                new_config = QosConfig(new)

            self._check_platform_params(old_config, new_config)
            self._check_interfaces(old_config, new_config)
            self._check_policies(old_config, new_config)
            self._check_global_profiles(old_config, new_config)
            self._check_mark_maps(old_config, new_config)
            self._check_action_groups(old_config, new_config)
            self._check_ingress_maps(old_config, new_config)
            self._check_egress_maps(old_config, new_config)
        else:
            # Provisioner is being created due to a notification of a LAG
            # membership change from the LAG component:

            bond_group = bonding_ntfy.get('vyatta-interfaces-bonding-v1:bond-group')
            member_interface = bonding_ntfy.get('vyatta-interfaces-bonding-v1:member-interface')
            operation_add = bonding_ntfy.get('vyatta-interfaces-bonding-v1:operation-add')
            LOG.debug(f"Received notification from bond-group: {bond_group}")
            LOG.debug(f"member-interface: {member_interface}")
            LOG.debug(f"operation-add: {operation_add}")

            # Find the bonding group in the QoS configuration
            bond_dict = get_bond_dict(old, bond_group)

            # Notification for a LAG that does not exist in the QoS
            # configuration. Ignore it.
            if bond_dict is None:
                return

            if_dict = get_dataplane_if_dict(old, member_interface)

            if if_dict is None:
                # Attach the LAG policy on the interface reported in the
                # notification, or detach the LAG policy from it.

                # Create QoS configuration objects with no interfaces. Since there
                # is not a new QoS configuration (this is a LAG membership change),
                # both objects are created from the current configuration (old):
                old.pop('vyatta-interfaces-v1:interfaces', None)
                old_config = QosConfigBondMembers(old)
                new_config = QosConfigBondMembers(old)

                # Add the LAG member to the appropriate QoS configuration object
                # so the difference between the objects reflect the LAG membership
                # change:
                if operation_add:
                    new_config.add_bond_member(member_interface, bond_dict)
                else:
                    old_config.add_bond_member(member_interface, bond_dict)

                self._check_interfaces(old_config, new_config)
            else:
                # The LAG membership notification is for a physical port that
                # exists in the JSON configuration file. That means that a QoS
                # policy was attached to a LAG (LAG policy), the physical port
                # was removed from LAG and a QoS policy was attached to the
                # physical port (port policy), all in the same CLI commit.
                # In such case, configd will apply the LAG and QoS changes as
                # follows:
                #
                # Since VCI components are always processed before legacy
                # components, configd first applied the QoS configuration
                # change: a QoS policy was attached to LAG (i.e. it was
                # attached to all LAG members, including the one that is being
                # removed). The QoS configuration on the physical port was
                # ignored (since the port is still a LAG member),
                # but its configuration was saved in the JSON file.
                #
                # Then, Configd applies the LAG configuration change (member
                # removal). The LAG component has sent the notification to us
                # removing the member. We have found the interface from the
                # notification in the JSON configuration file and we must now
                # detach the LAG policy from the interface and attach the
                # port policy to it.

                # Create a QoS configuration object with a single interface (the
                # interface from the notification)
                old.pop('vyatta-interfaces-v1:interfaces', None)
                ifs_dict = {
                    'vyatta-interfaces-v1:interfaces': {
                        'vyatta-interfaces-dataplane-v1:dataplane': [if_dict]
                    }
                }
                old.update(ifs_dict)
                config = QosConfigBondMembers(old)

                interface = config.find_interface(member_interface)
                self._if_updates.append(interface)

    def _check_interfaces(self, old_config, new_config):
        """ Check for any changes to interface config """
        for name, interface in new_config.interfaces.items():
            old_interface = old_config.find_interface(name)
            if old_interface is not None:
                if interface != old_interface:
                    # This interface has been modified, delete the old
                    # version, add the new one
                    self._if_deletes.append(old_interface)
                    self._if_creates.append(interface)
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
                    # Is this mark-map used in any shaper?
                    for interface in new_config.interfaces.values():
                        for policy in interface.policies:
                            if policy.shaper in mark_map.shapers:
                                if interface not in self._if_updates:
                                    self._if_updates.append(interface)
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

    def _check_platform_params(self, old_config, new_config):
        """ Check for any changes to platform params """
        if new_config.plat_buf_thresh is not None:
            self._obj_create.append(new_config.plat_buf_thresh)
        elif old_config.plat_buf_thresh is not None:
            self._obj_delete.append(old_config.plat_buf_thresh)

        lp_des_changed = False
        if new_config.plat_lp_des is not None:
            if new_config.plat_lp_des != old_config.plat_lp_des:
                self._obj_create.append(new_config.plat_lp_des)
                lp_des_changed = True
        elif old_config.plat_lp_des is not None:
            self._obj_delete.append(old_config.plat_lp_des)
            lp_des_changed = True

        # If the local prio designator changes, then all policies need
        # an update
        if lp_des_changed:
            for interface in new_config.interfaces.values():
                if (interface not in self._if_creates and
                   interface not in self._if_updates):
                    self._if_updates.append(interface)

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

    def _check_ingress_maps(self, old_config, new_config):
        """ Check for any changes to ingress_maps """
        for ingress_map in new_config.ingress_maps.values():
            old_ingress_map = old_config.get_ingress_map(ingress_map.name)
            if old_ingress_map is not None:
                # We have an existing ingress_map, has it changed?
                if ingress_map != old_ingress_map:
                    # It has changed, delete the old, create the new one if it
                    # is being used by any vlan or it is the system-default
                    self._obj_delete.append(old_ingress_map)
                    if ingress_map.bindings or ingress_map.system_default:
                        self._obj_create.append(ingress_map)
            else:
                # We have a new ingress-map - is it being used by any port or
                # vlan, or is it the system-default?
                if ingress_map.bindings or ingress_map.system_default:
                    self._obj_create.append(ingress_map)
                else:
                    self._in_map_deferred.append(ingress_map.name)

        for ingress_map in old_config.ingress_maps.values():
            new_ingress_map = new_config.get_ingress_map(ingress_map.name)
            if new_ingress_map is None:
                # Delete the old ingress-map
                self._obj_delete.append(ingress_map)

    @property
    def deferred_ingress_maps(self):
        """ Return the list of ingress-map names that have been deferred """
        return self._in_map_deferred

    def _check_egress_maps(self, old_config, new_config):
        """ Check for any changes to egress_maps """
        for egress_map in new_config.egress_maps.values():
            old_egress_map = old_config.get_egress_map(egress_map.name)
            if old_egress_map is not None:
                # We have an existing egress_map, has it changed?
                if egress_map != old_egress_map:
                    # It has changed, delete the old, create the new one if it
                    # is being used by any vlan or port
                    self._obj_delete.append(old_egress_map)
                    if egress_map.bindings:
                        self._obj_create.append(egress_map)
            else:
                # We have a new egress-map - is it being used by any port or
                # vlan
                if egress_map.bindings:
                    self._obj_create.append(egress_map)
                else:
                    self._eg_map_deferred.append(egress_map.name)

        for egress_map in old_config.egress_maps.values():
            new_egress_map = new_config.get_egress_map(egress_map.name)
            if new_egress_map is None:
                # Delete the old egress-map
                self._obj_delete.append(egress_map)

    @property
    def deferred_egress_maps(self):
        """ Return the list of egress-map names that have been deferred """
        return self._eg_map_deferred

    def _detach_policy(self, ctrl, interface):
        """
        Detach the QoS policy from the specified interface.
        """
        cmd_count = 0
        if interface.policies:
            key = f"qos {interface.ifname}"
            cmd = f"{key} disable"
            for dataplane in ctrl.get_dataplanes():
                with dataplane:
                    ctrl.store(key, cmd, interface.ifname, "DELETE")
                    LOG.debug(f"delete: {cmd}")
                    cmd_count += 1

        return cmd_count

    def _delete_interfaces(self, ctrl):
        """
        Disable QoS policies from all the interfaces on the deletes list
        """
        cmd_count = 0
        for interface in self._if_deletes:
            cmd_count += self._detach_policy(ctrl, interface)

        return cmd_count

    def _attach_policy(self, ctrl, interface):
        """
        Attach a QoS policy to the specified interface
        """
        cmd_count = 0
        key = f"qos {interface.ifname}"
        for dataplane in ctrl.get_dataplanes():
            with dataplane:
                # Attach any QoS policies to this interface and its vlans
                for cmd in interface.commands():
                    path = f"{key} {cmd}"
                    ctrl.store(path, cmd, interface.ifname, "SET")
                    LOG.debug(f"set: {cmd}")
                    cmd_count += 1

        return cmd_count

    def _create_interfaces(self, ctrl):
        """
        Attach QoS policies to interfaces that didn't have them before
        """
        cmd_count = 0
        for interface in self._if_creates:
            cmd_count += self._attach_policy(ctrl, interface)

        return cmd_count

    def _update_interfaces(self, ctrl):
        """
        Update the interfaces with modified QoS policies, by first detaching the
        old policy, then attaching the new policy
        """
        cmd_count = 0
        for interface in self._if_updates:
            cmd_count += self._detach_policy(ctrl, interface)
            cmd_count += self._attach_policy(ctrl, interface)

        return cmd_count

    def _delete_objects(self, ctrl):
        """ Delete any old action-groups,ingress-maps,egress-maps,mark-maps """
        cmd_count = 0
        for dataplane in ctrl.get_dataplanes():
            with dataplane:
                for obj in self._obj_delete:
                    for (path, cmd, ifname) in obj.delete_cmd():
                        ctrl.store(path, cmd, ifname, "DELETE")
                        LOG.debug(f"delete: {cmd}")
                        cmd_count += 1

        return cmd_count

    def _create_objects(self, ctrl):
        """
        Create any new or modified action-groups,ingress-maps,egress-maps or
        mark-maps.
        """
        cmd_count = 0
        for dataplane in ctrl.get_dataplanes():
            with dataplane:
                for obj in self._obj_create:
                    for (path, cmd, ifname) in obj.commands():
                        ctrl.store(path, cmd, ifname, "SET")
                        LOG.debug(f"set: {cmd}")
                        cmd_count += 1

        return cmd_count

    def _qos_commit(self, ctrl):
        """
        Send the final 'qos commit' command to tell the vyatta-dataplane that
        this batch of commands is complete.
        """
        for dataplane in ctrl.get_dataplanes():
            with dataplane:
                ctrl.store("qos commit", "qos commit", "ALL", "SET")
                LOG.debug("set: qos commit")

    def commands(self, ctrl):
        """
        Write the necessary commands to vplaned's cstore to delete, modify
        and create the required QoS objects
        """
        cmd_count = 0
        cmd_count += self._delete_objects(ctrl)
        cmd_count += self._create_objects(ctrl)
        cmd_count += self._delete_interfaces(ctrl)
        cmd_count += self._update_interfaces(ctrl)
        cmd_count += self._create_interfaces(ctrl)
        if cmd_count != 0:
            self._qos_commit(ctrl)

        return
