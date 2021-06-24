#!/usr/bin/env python3
#
# Copyright (c) 2020, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
This module mocks up a limited replacement for the build_rule function from
the Perl FWHelper.pm module that is normally found in
/opt/vyatta/share/perl5/Vyatta/FWHelper.pm
"""
import ipaddress
import logging
import string

from vyatta_policy_qos_vci.dscp import str2dscp
from vyatta_policy_qos_vci.policer import Policer

LOG = logging.getLogger('Policy QoS VCI')

# Read this from /etc/ethertypes
ETHTYPE_DICT = {}

# Read this from /etc/services
PORT_DICT = {}

# Read this from /etc/protocols
PROTO_DICT = {}

def good_name(string):
    """
    Check that the string only contains alpha-numberic characters, hyphens,
    periods and underscores.
    return True if it does
    return False if it contains other characters
    """
    char_set = 'abcdefghijklmnopqrstuvxwyz0123456789-._'
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
                    if not good_name(proto_name) or not proto_number.isdecimal():
                        raise ValueError

                    PROTO_DICT[proto_name] = proto_number

    except OSError:
        LOG.error("Failed to open /etc/protocols")

    except ValueError:
        LOG.error(f"Invalid protocol name/number combination "
                  f"{proto_name}/{proto_number}")


def read_services():
    """
    Read in /etc/services and create a dictionary of port names to numbers
    """
    global PORT_DICT

    try:
        with open("/etc/services") as data_file:
            for port_line in data_file.readlines():
                # /etc/services contains one line with just a carriage-return
                if len(port_line) > 1 and not port_line.startswith('#'):
                    # format:  <port_name>     <port_number>/<l4-proto>
                    port_name = port_line.split()[0].lower()
                    port_proto = port_line.split()[1]
                    port_number = port_proto.split('/')[0]
                    if not good_name(port_name):
                        raise ValueError

                    PORT_DICT[port_name] = port_number

    except OSError:
        LOG.error("Failed to open /etc/services")

    except ValueError:
        LOG.error(f"Invalid port name/number combination "
                  f"{port_name}/{port_number}")


def is_hex(in_str):
    """ Return true is the string only contain hexadecimal characters """
    return all(char in string.hexdigits for char in in_str)


def read_ethertypes():
    """
    Read in /etc/ethertypes and create a dictionary of ethertype names to
    numbers
    """
    global ETHTYPE_DICT

    try:
        with open("/etc/ethertypes") as data_file:
            for ethtype_line in data_file.readlines():
                # /etc/ethertypes contains one line with just a carriage-return
                if not ethtype_line.startswith('#'):
                    ethtype_name = ethtype_line.split()[0].lower()
                    ethtype_number = ethtype_line.split()[1]
                    if not good_name(ethtype_name) or not is_hex(ethtype_number):
                        raise ValueError

                    ETHTYPE_DICT[ethtype_name] = int(ethtype_number, 16)

    except OSError:
        LOG.error("Failed to open /etc/ethertypes")

    except ValueError:
        LOG.error(f"Invalid ethtype name/number combination "
                  f"{ethtype_name}/{ethtype_number}")


def valid_address(address):
    """ Return true if we have a valid IPv4 or IPv6 address """
    # Remove "!" if it exists
    address = address.replace('!', '')

    # Remove the network mask if it exists
    mask_index = address.find('/')
    if mask_index != -1:
        address = address[:mask_index]

    try:
        addr = ipaddress.ip_address(address)
        return addr.version

    except ValueError:
        return None


def src_dst_rule(src_dst_dict, src_or_dst):
    """ Build part of a firewall rule for source or destination """
    rule_str = ""
    if 'mac-address' in src_dst_dict:
        mac = src_dst_dict['mac-address']
        rule_str += f"{src_or_dst}-mac={mac}"

    if 'address' in src_dst_dict:
        address = src_dst_dict['address']
        if valid_address(address) is None:
            rule_str += f"{src_or_dst}-addr-group={address}"
        else:
            rule_str += f"{src_or_dst}-addr={address}"

    if 'port' in src_dst_dict:
        port = src_dst_dict['port']
        if port.isnumeric():
            rule_str += f"{src_or_dst}-port={port}"
        else:
            # we need to be able to detect a port range, i.e. 10-25
            port_range = port.split('-')
            if len(port_range) == 2 and port_range[0].isnumeric() and port_range[1].isnumeric():
                rule_str += f"{src_or_dst}-port={port}"
            else:
                try:
                    port = PORT_DICT[port]
                    rule_str += f"{src_or_dst}-port={port}"

                except KeyError:
                    rule_str += f"{src_or_dst}-port-group={port}"

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
        self._proto_final = None
        self._protocol_group = None
        self._icmp = None
        self._ipv6_route = None
        self._tcp_flags = None
        self._fragment = None
        self._rproc = None
        self._disabled = False

        if not PROTO_DICT:
            read_protocols()

        if not PORT_DICT:
            read_services()

        if not ETHTYPE_DICT:
            read_ethertypes()

        if 'disable' in rule_dict:
            self._disabled = True
            return

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
            self._dscp = f" dscp={str2dscp(dscp)}"

        if 'pcp' in rule_dict:
            pcp = rule_dict['pcp']
            self._pcp = f" pcp={pcp}"

        if 'protocol-group' in rule_dict:
            protocol_group = rule_dict['protocol-group']
            self._protocol_group = f" protocol-group={protocol_group}"

        icmp_dict = None
        if 'icmp' in rule_dict:
            self._proto_final = " proto-final=1"
            proto = "v4"
            icmp_dict = rule_dict['icmp']

        if 'icmpv6' in rule_dict:
            self._proto_final = " proto-final=58"
            proto = "v6"
            icmp_dict = rule_dict['icmpv6']

        if icmp_dict is not None:
            if 'group' in icmp_dict:
                icmp_group = icmp_dict['group']
                self._icmp = f" icmp{proto}-group={icmp_group}"

            if 'name' in icmp_dict:
                icmp_name = icmp_dict['name']
                self._icmp = f" icmp{proto}={icmp_name}"

            if 'type' in icmp_dict:
                type_array = icmp_dict['type']
                # NPF yang enforces a single type_array entry
                type_dict = type_array[0]
                icmp_type = type_dict['type-number']
                self._icmp = f" icmp{proto}={icmp_type}"

                if 'code' in type_dict:
                    icmp_code = type_dict['code']
                    self._icmp += f":{icmp_code}"

        if 'ipv6-route' in rule_dict:
            self._proto_final = " proto-final=43"
            ipv6_route_dict = rule_dict['ipv6-route']
            route_type = ipv6_route_dict['type']
            self._ipv6_route = f" ipv6-route={route_type}"

        if 'tcp' in rule_dict:
            if self._protocol is None:
                self._proto_final = " proto-final=6"
            flags_dict = rule_dict['tcp']
            flags = flags_dict.get('flags')
            self._tcp_flags = f" tcp-flags={flags}"

        if 'fragment' in rule_dict:
            self._fragment = " fragment=y"

        self._rproc = None
        # In an rproc we can have the following combinations of markdscp,
        # policer, action-group and log:
        # - rproc=action-group()
        # - rproc=markdscp()
        # - rproc=policer()
        # - rproc=log
        # - rproc=action-group();log
        # - rproc=markdscp();log
        # - rproc=policer();log
        # - rproc=markdscp();policer()
        # - rproc=markdscp();policer();log
        # action-group cannot be mixed with markdscp or policer
        if 'mark' in rule_dict:
            mark_dict = rule_dict['mark']
            if 'dscp' in mark_dict:
                dscp_value = str2dscp(mark_dict['dscp'])
                self._rproc = f" rproc=markdscp({dscp_value})"
            if 'pcp' in mark_dict:
                pcp = mark_dict['pcp']
                self._rproc = f" rproc=markpcp({pcp},none)"
            if 'pcp-inner' in mark_dict:
                self._rproc = f" rproc=markpcp({pcp},inner)"

        if 'police' in rule_dict:
            police_dict = rule_dict['police']
            policer = Policer(police_dict)
            if policer.check():
                cmds = policer.commands()
                if self._rproc is None:
                    self._rproc = f" rproc={cmds}"
                else:
                    self._rproc += f";{cmds}"

        if 'action-group' in rule_dict:
            act_grp_name = rule_dict['action-group']
            self._rproc = f" rproc=action-group({act_grp_name})"

        if 'log' in rule_dict:
            if self._rproc is None:
                self._rproc = "rproc=log"
            else:
                self._rproc += ";log"

    def commands(self):
        """ Generate the rule command if this rule isn't disabled"""
        if self._disabled:
            return None

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
        if self._protocol_group is not None:
            result_str += self._protocol_group
        if self._ipv6_route is not None:
            result_str += self._ipv6_route
        if self._proto_final is not None:
            result_str += self._proto_final
        if self._icmp is not None:
            result_str += self._icmp
        if self._tcp_flags is not None:
            result_str += self._tcp_flags
        if self._fragment is not None:
            result_str += self._fragment
        if self._rproc is not None:
            result_str += self._rproc

        result_str += f" handle=tag({self._tag})"

        return result_str
