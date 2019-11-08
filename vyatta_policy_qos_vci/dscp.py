#!/usr/bin/env python3

# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

"""
A library to turn a string of DSCP values and Diff-Serv names into an ordered
list of DSCP integers
"""

import logging

LOG = logging.getLogger('Policy QoS VCI')

DIFF_SERV = {
    'default': 0,
    'cs0':     0,
    'cs1':     8,
    'cs2':     16,
    'cs3':     24,
    'cs4':     32,
    'cs5':     40,
    'cs6':     48,
    'cs7':     56,
    'af11':    10,
    'af12':    12,
    'af13':    14,
    'af21':    18,
    'af22':    20,
    'af23':    22,
    'af31':    26,
    'af32':    28,
    'af33':    30,
    'af41':    34,
    'af42':    36,
    'af43':    38,
    'ef':      46,
    'va':      44
}


def str2dscp(dscp_str):
    """
    Turn a single string token representing a DSCP value into an integer.
    Return None if something goes wrong.
    """
    try:
        value = DIFF_SERV[dscp_str]

    except KeyError:
        if dscp_str.startswith('0x'):
            try:
                value = int(dscp_str, base=16)

            except ValueError:
                LOG.error(f"Bad hexadecimal DSCP value: {dscp_str}")
                return None
        else:
            try:
                value = int(dscp_str)

            except ValueError:
                LOG.error(f"Bad decimal DSCP value: {dscp_str}")
                return None

    if value < 0 or value > 63:
        LOG.error(f"DSCP value out of range: {dscp_str}")
        return None

    return value


def dscp_range(input_str):
    """
    Take a string expressing range of DSCP values in the form:

       "1,cs7,0x3,5-9"

    and return an ordered list of integer DSCP values:

        ( 1, 3, 5, 6, 7, 6, 8, 9, 56 )

    return None if problem with input string.
    """
    dscp_values = []
    elements = input_str.split(',')
    for element in elements:
        if '-' in element:
            start_value, end_value = element.split('-')
            start_dscp = str2dscp(start_value)
            end_dscp = str2dscp(end_value)
            if start_dscp is None or end_dscp is None:
                LOG.error(f"Problem with DSCP range: {element}")
                return None

            if start_dscp >= end_dscp:
                LOG.error(f"Wrong DSCP order: {start_dscp} {end_dscp}")
                return None

            dscp_values.extend(list(range(start_dscp, end_dscp+1)))
        else:
            dscp = str2dscp(element)
            if dscp is None:
                LOG.error(f"Problem with single DSCP element: {element}")
                return None

            dscp_values.append(dscp)

    if not dscp_values:
        LOG.error(f"No DSCP values added for: {input_str}")
        return None

    dscp_values.sort()
    return dscp_values
