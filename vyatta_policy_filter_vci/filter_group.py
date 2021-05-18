#!/usr/bin/env python3
#
# Copyright (c) 2020-2021, AT&T Intellectual Property. All rights reserved.
# SPDX-License-Identifier: LGPL-2.1-only

"""
A module to define the filter group for QoS.
"""
import logging
from vyatta.proto import GPCConfig_pb2
from vyatta_policy_filter_vci.filter_action import FilterAction

LOG = logging.getLogger('POLFIL VCI')


class FilterGroup:
    """
    A filter group contains mappings between Generic Packet Classifier
    (GPC) results and QoS actions. Each filter group may be bound to
    multiple interfaces.
    """
    def __init__(self, fg_dict):
        self._name = fg_dict.get('group-name')
        self._bindings = []
        self._result_actions = {}
        self._classifier = ""
        self._counters_enabled = False

        # QoS only allows one element in this (non empty) list
        class_list = fg_dict.get('classify')
        if class_list is not None:
            lcl_classifier = class_list[0]
        # This list will only have one currently in use
        lcl_class_list = fg_dict.get('classifier')
        if lcl_class_list is not None:
            for lcl_class in lcl_class_list:
                lcl_class_name = lcl_class['classifier-name']
                if lcl_class_name == lcl_classifier:
                    self._classifier = lcl_class['import']
                    break

        map = fg_dict.get('map')
        res_list = map.get('result')
        if res_list is not None:
            for result in res_list:
                res_name = result.get('result')
                action = FilterAction(result.get('action'))
                self._result_actions[res_name] = action

        counters = fg_dict.get('counters')
        if counters is not None:
            self._counters_enabled = True
            sharing = counters.get('sharing')
            self._counters_shared = sharing == "per-group"

            ctr_type = counters.get('type')
            if ctr_type is not None and ctr_type == "auto-per-result":
                self._counters_per_result = True
            else:
                self._counters_per_result = False

            if not self._counters_per_result and not self._counters_shared:
                self._counters_auto = True
            else:
                self._counters_auto = False

    def bind(self, ifname):
        """ Bind this filter group to the given interface """
        self._bindings.append(ifname)

    @property
    def bound(self):
        """ Is this filter group bound to any interfaces """
        return self._bindings

    @property
    def name(self):
        """ Return the name of this filter group """
        return self._name

    @property
    def classifier(self):
        """ Return the name of the GPC classifier this filter group uses """
        return self._classifier

    def add_counters(self, pb_message, rules_message):
        """ Build protobuf counters relevant to this group """
        # per-interface, per-rule counters are auto created
        if not self._counters_enabled or self._counters_auto:
            return

        # always count packets and all bytes bar L1 framing etc.
        format = GPCConfig_pb2.GPCCounter.PACKETS_AND_L2_L3_BYTES

        if self._counters_shared:
            ifnames = ["all"]
        else:
            ifnames = self._bindings

        ctr_names = []
        if self._counters_per_result:
            for result in self._result_actions:
                ctr_names.append(f"result:{result}")
        else:
            for rule in rules_message.rules:
                ctr_names.append(f"rule:{rule.number}")

        for ctr_name in ctr_names:
            for ifname in ifnames:
                ctr_message = pb_message.counters.add()
                ctr_message.format = format
                ctr_message.name = f"local/{self._name}/{ctr_name}/{ifname}"

    def _build_tbl_message(self, tbl_message, rules_message):
        """ Build a protobuf GPC table for this group """
        tbl_message.location = GPCConfig_pb2.GPCTable.INGRESS
        tbl_message.table_names.append(f"{self._name}")

        # Promote the rules' traffic-type into the GPC table
        tbl_message.traffic_type = rules_message.traffic_type
        tbl_message.rules.traffic_type = rules_message.traffic_type
        for gpc_rule in rules_message.rules:
            action = self._result_actions.get(gpc_rule.result)
            if action is None:
                continue
            rule = tbl_message.rules.rules.add()
            rule.CopyFrom(gpc_rule)

            rule.table_index = 1
            rule.orig_number = rule.number
            action.add_action(rule)

            if not self._counters_enabled:
                rule.counter.counter_type = GPCConfig_pb2.RuleCounter.DISABLED
            elif self._counters_auto:
                rule.counter.counter_type = GPCConfig_pb2.RuleCounter.AUTO
            else:
                rule.counter.counter_type = GPCConfig_pb2.RuleCounter.NAMED
                if self._counters_shared:
                    if self._counters_per_result:
                        ctr_name = f"result:{rule.result}"
                    else:
                        ctr_name = f"rule:{rule.number}"
                    rule.counter.name = f"local/{self._name}/{ctr_name}/all"

    def add_tables(self, pb_message, rules_message):
        """ Build protobuf GPC tables for this group and its bindings """
        first = True
        for ifname in self._bindings:
            tbl_message = pb_message.tables.add()
            if first:
                self._build_tbl_message(tbl_message, rules_message)
                first_tbl_message = tbl_message
                first = False
            else:
                tbl_message.CopyFrom(first_tbl_message)

            if (self._counters_enabled and
                    not self._counters_auto and
                    not self._counters_shared):
                for rule in tbl_message.rules.rules:
                    cname = f"result:{rule.result}"
                    rule.counter.name = f"local/{self._name}/{cname}/{ifname}"

            tbl_message.ifname = ifname

    def check(self, gpc_class_list, cg_bindings):
        """
        Validate this filter group against the Generic Packet Classifier config
        by checking:
        - That all the results it uses are in the GPC classifier it references.
        - That no more than one classifier of each traffic type is configured on
        any interface.
        """
        errmsg = None

        # Find the GPC that this filter group references
        for gpc_classifier in gpc_class_list:
            gpc_name = gpc_classifier['classifier-name']
            if gpc_name == self._classifier:
                rules = gpc_classifier.get('rule')
                if rules is None:
                    errmsg = f"Packet classifier {gpc_name} has no rules"
                    return errmsg
                # Now check our results are all used in a rule
                for result in self._result_actions:
                    found = False
                    for rule in rules:
                        rule_result = rule.get('result')
                        if rule_result is None:
                            continue
                        if result == rule_result:
                            found = True
                            break
                    if not found:
                        errmsg = f"Result {result} is not in a rule in packet"\
                            f" classifier {gpc_name}"
                        return errmsg

                for ifname in self._bindings:
                    traffic_type = gpc_classifier.get('type')
                    exist_traffic_type = cg_bindings.get((ifname,
                                                          traffic_type))
                    if exist_traffic_type is None:
                        cg_bindings[(ifname, traffic_type)] = True
                    else:
                        errmsg = f"Only one group of type {traffic_type}"\
                            f" is allowed on interface {ifname}"
                        return errmsg

                return errmsg

        return errmsg

    def _rule_count(self, gpc_class_list):
        """
        Calculates the number of rules in the GPC classifier.
        """

        # Find the GPC group that this filter group references
        for gpc_classifier in gpc_class_list:
            gpc_name = gpc_classifier['classifier-name']
            if gpc_name == self._classifier:
                rules = gpc_classifier.get('rule')
                if rules is None:
                    return 0

                stat_count = 0
                for rule in rules:
                    # Don't count disabled rules
                    if 'disable' not in rule.keys():
                        stat_count += 1
                return stat_count

        return 0

    def stats_needed(self, gpc_class_list):
        """
        Calculates the number of statistics needed for a given GPC classifier.
        """

        stat_count = 0

        if self._counters_enabled:

            if self._counters_per_result:
                stat_count = len(self._result_actions)
            elif self._counters_auto:
                stat_count = self._rule_count(gpc_class_list)

            # If counters not shared, need to count them for each interface.
            if not self._counters_shared:
                stat_count *= len(self._bindings)

        return stat_count
