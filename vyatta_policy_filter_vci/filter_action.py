#!/usr/bin/env python3
#
# Copyright (c)2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define the filter action for QoS.
"""
import logging
from vyatta.proto import GPCConfig_pb2
from vyatta_policy_qos_vci.policer import parse_bandwidth

LOG = logging.getLogger('POLFIL VCI')


class FilterAction:
    """
    A filter action contains actions to be applied to packets matching
    a result in a Generic Packet Classifier match.
    """
    def __init__(self, fa_dict):
        self._designation = None
        self._drop_prec = None
        self._bandwidth = None
        self._burst = None
        self._excess_bandwidth = None
        self._excess_burst = None
        self._colour_aware = None
        self._pass = False

        if fa_dict is None:
            self._pass = True  # default if no action given
            return

        mark_dict = fa_dict.get('mark')
        if mark_dict is not None:
            self._designation = mark_dict.get('designation')
            self._drop_prec = mark_dict.get('drop-precedence')

        police_dict = fa_dict.get('police')
        if police_dict is not None:
            self._bandwidth = parse_bandwidth(police_dict.get('bandwidth'))
            self._burst = police_dict.get('burst')
            self._excess_bandwidth = parse_bandwidth(
                police_dict.get('excess-bandwidth'))
            self._excess_burst = police_dict.get('excess-burst')
            self._colour_aware = police_dict.get('colour-awareness')

    def add_action(self, rule_message):
        """ Build protobuf actions for a rule """
        if self._pass:
            action_message = rule_message.actions.add()
            action_message.decision = GPCConfig_pb2.RuleAction.PASS
            return

        if self._designation:
            action_message = rule_message.actions.add()
            action_message.designation = self._designation

        if self._drop_prec:
            colour_dict = {
                'green': GPCConfig_pb2.RuleAction.GREEN,
                'yellow': GPCConfig_pb2.RuleAction.YELLOW,
                'red': GPCConfig_pb2.RuleAction.RED,
            }
            action_message = rule_message.actions.add()
            action_message.colour = colour_dict.get(self._drop_prec)

        # If burst values are not set, default them to 10% of
        # the relevant configured bandwidth, ie. 100ms of burst.
        if self._bandwidth is not None:
            if self._burst is None:
                self._burst = int(self._bandwidth/10)
            if self._excess_bandwidth is None:
                self._excess_bandwidth = 0
                self._excess_burst = 0
            elif self._excess_burst is None:
                self._excess_burst = int(self._excess_bandwidth/10)

            action_message = rule_message.actions.add()
            action_message.policer.bw = self._bandwidth
            action_message.policer.excess_bw = self._excess_bandwidth
            action_message.policer.burst = self._burst
            action_message.policer.excess_burst = self._excess_burst
            if self._colour_aware == "colour-aware":
                action_message.policer.awareness = GPCConfig_pb2.COLOUR_AWARE
            else:
                action_message.policer.awareness = GPCConfig_pb2.COLOUR_UNAWARE
