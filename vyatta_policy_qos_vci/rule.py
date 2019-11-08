#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
This module mocks up a very limited replacement for the Perl FWHelper.pm module
that is normally found in /opt/vyatta/share/perl5/Vyatta/FWHelper.pm
"""
import logging

LOG = logging.getLogger('Policy QoS VCI')

# Ethernet frame types.  The list can be found on:
#         http://www.iana.org/assignments/ethernet-numbers
#         http://www.iana.org/assignments/ieee-802-numbers

ETHTYPE_DICT = {
    "ipv4": 0x0800, "x25": 0x0805, "arp": 0x0806, "fr_arp": 0x0808,
    "bpq": 0x08FF, "dec": 0x6000, "dna_dl": 0x6001, "dna_rc": 0x6002,
    "dna_rt": 0x6004, "lat": 0x6005, "cust": 0x6006, "sca": 0x6007,
    "teb": 0x6558, "raw_fr": 0x6559, "rarp": 0x8035, "aarp": 0x80F3,
    "atalk": 0x809B, "802_1q": 0x8100, "ipx": 0x8137, "netbeui": 0x8191,
    "ipv6": 0x86DD, "atmmpoa": 0x884C, "ppp_disc": 0x8863, "ppp_ses": 0x8864,
    "atmfate": 0x8884, "loop": 0x9000
}

PORT_DICT = {"ftp": 21, "ssh": 22, "telnet": 23, "smtp": 25, "tacacs": 49,
             "domain": 53, "tftp": 69, "http": 80, "www": 80, "https": 443}

PROTO_DICT = {}

def good_proto_name(string):
    """
    Check that the string only contains alpha-numberic characters, hyphens and
    periods
    return True if it does
    return False if it contains other characters
    """
    char_set = 'abcdefghijklmnopqrstuvxwyz0123456789-.'
    for char in string:
        if char not in char_set:
            return False

    return True


def read_protocols():
    """
    Read in /etc/protocols and create a dictionary of protocol names to numbers
    """
    global PROTO_DICT

    try:
        with open("/etc/protocols") as data_file:
            for proto_line in data_file.readlines():
                # /etc/protocols contains one line with just a carriage-return
                if len(proto_line) > 1 and not proto_line.startswith('#'):
                    proto_name = proto_line.split()[0].lower()
                    proto_number = proto_line.split()[1]
                    if not good_proto_name(proto_name) or not proto_number.isdecimal():
                        raise ValueError

                    PROTO_DICT[proto_name] = proto_number

    except OSError:
        LOG.error("Failed to open /etc/protocols")

    except ValueError:
        LOG.error(f"Invalid protocol name/number combination "
                  f"{proto_name}/{proto_number}")


def src_dst_rule(src_dst_dict, src_or_dst):
    """ Build part of a firewall rule for source or destination """
    rule_str = ""
    if 'mac-address' in src_dst_dict:
        mac = src_dst_dict['mac-address']
        rule_str += f"{src_or_dst}-mac={mac}"

    if 'address' in src_dst_dict:
        address = src_dst_dict['address']
        rule_str += f"{src_or_dst}-addr={address}"

    if 'port' in src_dst_dict:
        port = src_dst_dict['port']
        if not port.isnumeric():
            try:
                port = PORT_DICT[port]

            except KeyError:
                LOG.error(f"Unsupported port {port}")

        rule_str += f"{src_or_dst}-port={port}"

    return rule_str


class Rule:
    """
    Define the Rule class.  A Rule object holds all the information necessary
    to describe a single NPF rule.
    """
    def __init__(self, tag, rule_dict):
        """ Create a Rule object """
        self._tag = tag
        self._action = None
        self._protocol = None
        self._source = None
        self._dest = None
        self._ethtype = None
        self._dscp_group = None
        self._dscp = None
        self._pcp = None
        self._fragment = None
        self._rproc = None

        if not PROTO_DICT:
            read_protocols()

        if 'action' in rule_dict:
            action = rule_dict['action']
            if action == "pass":
                self._action = "action=accept"
            else:
                self._action = "action=drop"

        if 'protocol' in rule_dict:
            protocol = None
            try:
                protocol = rule_dict['protocol']
                self._protocol = f" proto-final={PROTO_DICT[protocol]}"

            except KeyError:
                if protocol is not None:
                    LOG.error(f"Unsupported protocol: {protocol}")

        if 'source' in rule_dict:
            src_dict = rule_dict['source']
            self._source = f" {src_dst_rule(src_dict, 'src')}"

        if 'destination' in rule_dict:
            dst_dict = rule_dict['destination']
            self._dest = f" {src_dst_rule(dst_dict, 'dst')}"

        if 'ethertype' in rule_dict:
            ethtype = None
            try:
                ethtype = rule_dict['ethertype'].lower()
                self._ethtype = f" ether-type={ETHTYPE_DICT[ethtype]}"

            except KeyError:
                if ethtype is not None:
                    LOG.error(f"Unsupported ethtype: {ethtype}")

        if 'dscp-group' in rule_dict:
            dscp_grp_name = rule_dict['dscp-group']
            self._dscp_group = f" dscp-group={dscp_grp_name}"

        if 'dscp' in rule_dict:
            dscp = rule_dict['dscp']
            self._dscp = f" dscp={dscp}"

        if 'pcp' in rule_dict:
            pcp = rule_dict['pcp']
            self._pcp = f" pcp={pcp}"

        if 'fragment' in rule_dict:
            self._fragment = " fragment=y"

        self._rproc = None
        if 'action-group' in rule_dict:
            act_grp_name = rule_dict['action-group']
            self._rproc = f" rproc=action-group({act_grp_name})"

        if 'log' in rule_dict:
            if self._rproc is None:
                self._rproc = "rproc=log"
            else:
                self._rproc += ";log"

    def commands(self):
        """ Generate the rule command """
        result_str = self._action
        if self._protocol is not None:
            result_str += self._protocol
        if self._source is not None:
            result_str += self._source
        if self._dest is not None:
            result_str += self._dest
        if self._ethtype is not None:
            result_str += self._ethtype
        if self._dscp_group is not None:
            result_str += self._dscp_group
        if self._dscp is not None:
            result_str += self._dscp
        if self._pcp is not None:
            result_str += self._pcp
        if self._fragment is not None:
            result_str += self._fragment
        if self._rproc is not None:
            result_str += self._rproc

        result_str += f" handle=tag({self._tag})"

        return result_str
