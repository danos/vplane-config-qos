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

LOG = logging.getLogger('POLFIL VCI')


class FilterAction:
    """
    A filter action contains actions to be applied to packets matching
    a result in a Generic Packet Classifier match.
    """
    def __init__(self, fa_dict):
        self._designation = None
        self._drop_prec = None
        self._pass = False

        if fa_dict is None:
            self._pass = True  # default if no action given
            return

        mark_dict = fa_dict.get('mark')
        if mark_dict is not None:
            self._designation = mark_dict.get('designation')
            self._drop_prec = mark_dict.get('drop-precedence')

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
