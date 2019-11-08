#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A simple class to hold the attributes of a WRED queue.
"""

GREEN = 0

class Wred:
    """
    A class to define WRED queue objects
    """
    def __init__(self, wred_dict):
        self._filter_weight = wred_dict.get('filter-weight')
        self._mark_prob = wred_dict.get('mark-probability')
        self._max_th = wred_dict.get('max-threshold')
        self._min_th = wred_dict.get('min-threshold')
        self._colour = GREEN

    def commands(self):
        """
        Return a string to define a WRED queue and its attributes.
        """
        return (f" red {self._colour} {self._min_th} {self._max_th} "
                f"{self._mark_prob} {self._filter_weight}")
