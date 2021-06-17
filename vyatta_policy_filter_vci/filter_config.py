#!/usr/bin/env python3
#
# Copyright (c) 2020-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
Config for Policy Filter Classification
"""
import logging
import zmq
import sys
from vplaned import Controller, ControllerException

# Note - this addition to path is to cater for the way
#        dataplane constructs nested protobuf imports
# This causes a flake8 E402: module level import not at top of file error
sys.path.append('/usr/lib/python3/dist-packages/vyatta/proto')
from vyatta.proto import GPCConfig_pb2                            # noqa: E402
from vyatta_policy_filter_vci.filter_group import FilterGroup     # noqa: E402

LOG = logging.getLogger('POLFIL VCI')

POL_NAMESPACE = 'vyatta-policy-v1'
POLFIL_NAMESPACE = 'vyatta-policy-filter-classification-v1'
IF_NAMESPACE = 'vyatta-interfaces-v1'
IFPOL_NAMESPACE = 'vyatta-interfaces-policy-v1'


class FilterConfig:
    """
    A class to represent the Policy Filter Classification groups
    which use the Generic Packet Classifier to classify packets
    and perform specific actions based on the classifier results.
    The entire config is packed into a protobuf config message
    and sent to vplaned.
    """
    def __init__(self, config_dict):
        """ Create the config """
        self._filter_groups = {}

        policy_dict = config_dict.get(f'{POL_NAMESPACE}:policy')
        if policy_dict is None:
            return

        filter_dict = policy_dict.get(
            f'{POLFIL_NAMESPACE}:filter-classification')
        self._create_groups(filter_dict)

        if_dict = config_dict.get(f'{IF_NAMESPACE}:interfaces')
        self._bind_groups(if_dict)

    def _create_groups(self, filter_dict):
        """ Create filter groups from config """
        if filter_dict is not None:
            filter_group_list = filter_dict.get('group')
            if filter_group_list is not None:
                for group_dict in filter_group_list:
                    group = FilterGroup(group_dict)
                    self._filter_groups[group.name] = group

    def _bind_groups(self, if_dict):
        """ Create bindings between filter groups and interfaces """
        if if_dict is not None:
            for key, interfaces in if_dict.items():
                if_type = key.split(':')[1]
                if if_type != "dataplane":
                    continue
                for interface in interfaces:
                    ifname = interface.get('tagnode')
                    if_policy_dict = interface.get(f'{IFPOL_NAMESPACE}:policy')
                    bound_groups = if_policy_dict.get(
                        f'{POLFIL_NAMESPACE}:filter-classification-group')
                    for group in bound_groups:
                        self._filter_groups[group].bind(ifname)

    @property
    def groups(self):
        """ Return the filter groups """
        return self._filter_groups

    def build_protobuf(self):
        """
        Build a protobuf message for this config and send
        it to the dataplane via the vplaned controller
        """
        pb_message = GPCConfig_pb2.GPCConfig()
        pb_message.feature_type = GPCConfig_pb2.GPCConfig.QOS

        context = zmq.Context()
        req = context.socket(zmq.REQ)
        req.connect("ipc://tmp/gpc_update.socket")

        for group in self._filter_groups.values():
            if not group.bound:
                continue
            req.send_string(f"{group.classifier}")
            reply = req.recv()
            if reply == b"None":
                LOG.error(f"No GPC group {group.classifier}")
                return

            rules_message = GPCConfig_pb2.Rules()
            rules_message.ParseFromString(reply)

            group.add_counters(pb_message, rules_message)
            group.add_tables(pb_message, rules_message)

        LOG.debug(f"MESSAGE {pb_message}")

        try:
            with Controller() as ctrl:
                ctrl.store("gpf_feature qos", pb_message, "ALL", "SET",
                           cmd_name="vyatta:gpc-config")

        except ControllerException:
            LOG.error("Failed to connect to vplane-controller")
