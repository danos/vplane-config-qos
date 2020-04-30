#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
This module mocks up a Policer object that is part of the Perl FWHelper.pm
module that is normally found in /opt/vyatta/share/perl5/Vyatta/FWHelper.pm
"""

import logging
import re

from vyatta_policy_qos_vci.dscp import str2dscp

LOG = logging.getLogger('Policy QoS VCI')

def parse_bandwidth(bandwidth):
    """
    Convert bandwidth string into a bytes-per-second integer value.
    <<number><suffix>>
    Suffixes are either 'bit' for bits-per-second or 'bps' for bytes-per-second.
    These can be preceded by a decimal (K,M,G) or binary (Ki,Mi,Gi)
    multiplier. No suffix implies Kbit (1000 bits per second).
    """
    if bandwidth is None:
        return None

    match = re.match(r"(0*\.?[0-9]+)([a-z]+)", bandwidth, flags=re.IGNORECASE)
    if match:
        items = match.groups()
        prefix = items[0]
        suffix = items[1]
    else:
        prefix = bandwidth
        suffix = None

    multiplier_map = {
        'k': 1000,
        'm': 1000000,
        'g': 1000000000,
        'ki': 1024,
        'mi': 1048576,
        'gi': 1073741824
    }

    if suffix is None:
        multiplier_symbol = 'k'
        bitbytes = 'bit'
    elif len(suffix) < 2:
        multiplier_symbol = None
        bitbytes = None
    elif suffix[0] == 'b':
        multiplier_symbol = None
        bitbytes = suffix
    elif suffix[1] == 'i':
        multiplier_symbol = suffix[0:2]
        bitbytes = suffix[2:]
    else:
        multiplier_symbol = suffix[0]
        bitbytes = suffix[1:]

    bit_divisor = 0
    if bitbytes == 'bps':
        bit_divisor = 1
    elif bitbytes == 'bit':
        bit_divisor = 8

    multiplier = 1
    if multiplier_symbol is not None:
        multiplier = multiplier_map[multiplier_symbol.lower()]

    result = None
    try:
        result = int((float(prefix) * multiplier) // bit_divisor)

    except ValueError:
        pass

    except ZeroDivisionError:
        pass

    return result


def parse_ratelimit(rate_str):
    """
    Convert a ratelimit string into a packets/second integer.
    The format of rate_str is <number>[<suffix>] where the optional suffix
    is one of the following: pps, Kpps, kpps, Mpps or mpps.
    """
    if rate_str is None:
        return None

    if rate_str.isdigit():
        return int(rate_str)

    index = rate_str.find('pps')
    multiplier_symbol = rate_str[index-1]

    if multiplier_symbol.isdigit():
        multiplier = 1
    else:
        index -= 1
        # We should have a K, k, M or m to deal with
        multiplier_symbol = multiplier_symbol.lower()
        if multiplier_symbol == 'k':
            multiplier = 1024
        elif multiplier_symbol == 'm':
            multiplier = 1000000
        else:
            LOG.error(f"Invalid rate-limit string: {rate_str}")
            return None

    rate = int(rate_str[:index])

    return rate * multiplier


class Policer:
    """
    Define the Policer class.  A Policer object holds all the information
    necessary to generate the appropriate NPF policer command to the
    vyatta-dataplane.
    """
    def __init__(self, policer_dict):
        """ Create a policer object """
        self._bandwidth = parse_bandwidth(policer_dict.get('bandwidth'))
        self._burst = policer_dict.get('burst')
        self._overhead = policer_dict.get('frame-overhead')
        self._ratelimit = parse_ratelimit(policer_dict.get('ratelimit'))
        self._tc = policer_dict.get('tc')
        self._then_action = "drop"
        self._mark_value = ""
        self._pcp_inner = False
        if 'then' in policer_dict:
            then_dict = policer_dict['then']
            action = then_dict.get('action')
            if action is not None:
                self._then_action = action
            else:
                # We can have both 'action' and 'mark' in the then_dict
                # but 'action' always trumps 'mark'
                if 'mark' in then_dict:
                    mark_dict = then_dict['mark']
                    for key, value in mark_dict.items():
                        if key == "pcp-inner":
                            self._pcp_inner = True
                        else:
                            if key == "dscp":
                                # convert dscp value string which may contain
                                # a diff-serv name (af11, cs6) into a numeric
                                # value
                                value = str2dscp(value)

                            self._then_action = "mark{}".format(key)
                            self._mark_value = value

    def check(self):
        """ Carry out basic config sanity testing """
        # Can't have both a bandwidth and ratelimit
        if self._bandwidth is not None and self._ratelimit is not None:
            return False

        return True

    def commands(self):
        """ Generate the commands necessary to define this policer """
        output = "policer"
        if self._bandwidth:
            # We have a bandwidth policer to configure
            bandwidth = self._bandwidth

            if self._burst is None:
                # The default burst is 4 msecs worth of bandwidth
                # bandwidth is in bits/second
                # 250 = 1000 milliseconds / 4 milliseconds
                burst = int(bandwidth / 250)
            else:
                burst = self._burst

            if self._overhead is None:
                overhead = 0
            else:
                overhead = self._overhead

            if self._tc is None:
                tcsize = 20
            else:
                tcsize = self._tc

            output += (f"(0,{bandwidth},{burst},{self._then_action},"
                       f"{self._mark_value},{overhead},{tcsize}")
        else:
            # We have a ratelimit policer to configure
            # The burst, overhead and tc parameters are ignored
            output += (f"({self._ratelimit},0,0,{self._then_action},"
                       f"{self._mark_value},0,1000")

        if self._then_action == "markpcp":
            if not self._pcp_inner:
                output += ",none)"
            else:
                output += ",inner)"
        else:
            output += ")"

        return output
