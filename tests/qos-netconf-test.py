#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

#import logging

import argparse
import time

from lxml import etree
from lxml import objectify

from ncclient import manager
from ncclient.xml_ import *

QOS_URN = "{urn:vyatta.com:mgmt:vyatta-policy-qos:1}"
POLICY_URN = "{urn:vyatta.com:mgmt:vyatta-policy:1}"


def parse_qos_policy(qos_policy_elem, indent, formatted):
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    qos_policy = qos_policy_elem.text
    print "{}qos-policy: {}".format(spaces, qos_policy)


def parse_qos_class(qos_class_elem, indent, formatted):
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    qos_class = qos_class_elem.text
    print "{}qos-class: {}".format(spaces, qos_class)


def parse_qos_profile(qos_profile_elem, indent, formatted):
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    qos_profile = qos_profile_elem.text
    print "{}qos-profile: {}".format(spaces, qos_profile)


def parse_subport_name(subport_name_elem, indent, formatted):
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    subport_name = subport_name_elem.text
    print "{}subport name: {}".format(spaces, subport_name)


def parse_subport(subport_elem, indent, formatted):
    """ """
#    print "--subport--"
#    print(objectify.dump(subport_elem))
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    subport_number = subport_elem.text
    print "{}subport number: {}".format(spaces, subport_number)


def parse_dscp_to_queue_map(dscp_to_queue_map_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print "{}--dscp-to-queue-map--".format(spaces)
#    print(objectify.dump(dscp_to_queue_map_elem))
    dscp_value = dscp_to_queue_map_elem.find(QOS_URN + "dscp")
    queue = dscp_to_queue_map_elem.find(QOS_URN + "queue")
    tc = dscp_to_queue_map_elem.find(QOS_URN + "traffic-class")

    print "{}dscp: {}, queue: {}, traffic-class: {}".format(spaces, dscp_value, queue, tc)


def parse_pcp_to_queue_map(pcp_to_queue_map_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print "{}--pcp-to-queue-map--".format(spaces)
#    print(objectify.dump(pcp_to_queue_map_elem))
    pcp_value = pcp_to_queue_map_elem.find(QOS_URN + "pcp")
    queue = pcp_to_queue_map_elem.find(QOS_URN + "queue")
    tc = pcp_to_queue_map_elem.find(QOS_URN + "traffic-class")

    print "{}pcp: {}, queue: {}, traffic-class: {}".format(spaces, pcp_value, queue, tc)


def parse_queue_statistics(queue_stats_elem, tc, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print "{}--queue-statistics--".format(spaces)
#    print(objectify.dump(queues_stats_elem))
    queue = queue_stats_elem.find(QOS_URN + "queue")
    databytes = queue_stats_elem.find(QOS_URN + "bytes")
    dropped = queue_stats_elem.find(QOS_URN + "dropped")
    packets = queue_stats_elem.find(QOS_URN + "packets")
    qlen = queue_stats_elem.find(QOS_URN + "qlen")
    random_drops = queue_stats_elem.find(QOS_URN + "random-drop")

    print "{}tc/queue {}/{} - bytes: {}, dropped: {}, packets: {}, random-drops: {}, qlen: {}".format(spaces, tc, queue, databytes, dropped,
                                                                                                      packets, random_drops, qlen)


def parse_traffic_class_queues_list(tc_queues_list_elem, indent, formatted):
    """ """
    spaces = "".ljust(indent)
#    print "--{}traffic-class-queues-list--".format(indent)
#    print(objectify.dump(tc_queues_list_elem))
    tc = tc_queues_list_elem.find(QOS_URN + "traffic-class")
    queue_stats_elem = tc_queues_list_elem.find(QOS_URN + "queue-statistics")
    parse_queue_statistics(queue_stats_elem, tc, indent+2, formatted)


def parse_traffic_class_rates(tc_rates_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print "{}--traffic-class-rates--".format(indent)
#    print(objectify.dump(tc_rates_elem))
    tc = tc_rates_elem.find(QOS_URN + "traffic-class")
    rate = tc_rates_elem.find(QOS_URN + "rate")
    print "{}traffic-class: {}, rate: {}".format(spaces, tc, rate)
    rate = tc_rates_elem.find(QOS_URN + "rate-64")
    print "{}traffic-class: {}, rate: {}".format(spaces, tc, rate)


def parse_weighted_round_robin_weights(wrr_weights_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print "{}--weighted-round-robin-weights--".format(spaces)
#    print(objectify.dump(wrr_weights_elem))
    queue = wrr_weights_elem.find(QOS_URN + "queue")
    weight = wrr_weights_elem.find(QOS_URN + "weight")
    print "{}queue: {}, weight: {}".format(spaces, queue, weight)


def parse_token_bucket_rate(tb_rate_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    tb_rate = tb_rate_elem.text
    print "{}token-bucket-rate: {}".format(spaces, tb_rate)
    print "{}token-bucket-rate-64: {}".format(spaces, tb_rate)


def parse_token_bucket_size(tb_size_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    tb_size = tb_size_elem.text
    print "{}token-bucket-size: {}".format(spaces, tb_size)


def parse_traffic_class_period(tc_period_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    tc_period = tc_period_elem.text
    print "{}traffic-class-period: {}".format(spaces, tc_period)


def parse_pipe(pipe_elem, indent, formatted):
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    pipe_number = pipe_elem.text
    print "{}pipe: {}".format(spaces, pipe_number)


def parse_pipe_list(pipe_list_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    pipe_number = pipe_list_elem.find(QOS_URN + "pipe").text
    print "{}--pipe-list-- {}".format(spaces, pipe_number)
#    print(objectify.dump(pipe_list_elem))

    for child_elem in pipe_list_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def parse_rule(name, rules_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print "{}--rule--".format(spaces)
#    print(objectify.dump(rules_elem))
    rule_number = rules_elem.find(QOS_URN + "rule-number")
    qos_class = rules_elem.find(QOS_URN + "qos-class")
    action_group = rules_elem.find(QOS_URN + "action-group")
    policer_pkts_excd = rules_elem.find(QOS_URN + "exceeded-packets")
    policer_byts_excd = rules_elem.find(QOS_URN + "exceeded-bytes")
    databytes = rules_elem.find(QOS_URN + "bytes")
    packets = rules_elem.find(QOS_URN + "packets")
    print "{}rule: {}, qos-class: {}, rule-number: {} - packets: {}, bytes: {}".format(spaces, name, qos_class, rule_number, packets, databytes)
    print "action-group: {}, policer_pkts_excd: {}, policer_byts_excd: {}".format(action_group, policer_pkts_excd, policer_byts_excd)


def parse_groups(groups_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print "{}--groups--".format(spaces)
#    print(objectify.dump(groups_elem))
    name = groups_elem.find(QOS_URN + "name")
    direction = groups_elem.find(QOS_URN + "direction")
    ifindex = groups_elem.find(QOS_URN + "ifindex")
    for child_elem in groups_elem.iterchildren():
        if child_elem.tag == QOS_URN + "rule":
            parse_rule(name, child_elem, indent+2, formatted)


def parse_rules(rules_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print "{}--rules--".format(spaces)
#    print(objectify.dump(rules_elem))
    for child_elem in rules_elem.iterchildren():
        if child_elem.tag == QOS_URN + "groups":
            parse_groups(child_elem, indent+2, formatted)
        else:
            print "--unknown rules element: %s" % child_elem.tag


def parse_traffic_class_list(traffic_class_list_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print "{}--traffic-class-list--".format(spaces)
#    print(objectify.dump(traffic_class_list_elem))
    tc = traffic_class_list_elem.find(QOS_URN + "traffic-class")
    data_bytes = traffic_class_list_elem.find(QOS_URN + "bytes")
    dropped = traffic_class_list_elem.find(QOS_URN + "dropped")
    packets = traffic_class_list_elem.find(QOS_URN + "packets")
    random_drops = traffic_class_list_elem.find(QOS_URN + "random-drop")

    print "{}tc: {}, bytes: {}, dropped: {}, packets: {}, random-drops: {}".format(spaces, tc, data_bytes, dropped, packets, random_drops)


def parse_subport_list(subport_list_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    subport_number = subport_list_elem.find(QOS_URN + "subport")
    print "{}--subport-list-- {}".format(spaces, subport_number)
#    print(objectify.dump(subport_list_elem))

    for child_elem in subport_list_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def parse_vlan_list(vlan_list_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print "{}--vlan-list--".format(spaces)
#    print(objectify.dump(vlan_list_elem))

    for child_elem in vlan_list_elem.iterchildren():
        if child_elem.tag == QOS_URN + "tag":
            vlan_tag = child_elem.text
        elif child_elem.tag == QOS_URN + "subport":
            subport_number = child_elem.text
        else:
            print "--unknown vlan-list element: {}".format(child_elem.tag)

    print "{}vlan-tag: {}, subport: {}".format(spaces, vlan_tag, subport_number)


def parse_shaper(ifname, shaper_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print "{}--{} shaper--".format(spaces, ifname)
#    print(objectify.dump(shaper_elem))

    for child_elem in shaper_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def parse_if_list(if_list_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print "{}--if-list--".format(spaces)
#    print(objectify.dump(if_list_elem))
    ifname = if_list_elem.find(QOS_URN + "ifname")
    shaper = if_list_elem.find(QOS_URN + "shaper")
    if ifname is not None and shaper is not None:
        parse_shaper(ifname, shaper, indent+2, formatted)
    else:
        print "--Failed to parse if-list - ifname: {}, shaper: {}".format(ifname, shaper)


def parse_state(state_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print "{}--state--".format(spaces)
#    print(objectify.dump(state_elem))
    for child_elem in state_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def parse_qos(qos_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print "{}--qos--".format(spaces)
#    print(objectify.dump(qos_elem))
    for child_elem in qos_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def parse_policy(policy_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print "{}--policy--".format(spaces)
#    print(objectify.dump(policy_elem))
    for child_elem in policy_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def strip_name_space(tag, namespace):
    """ """
    if tag.startswith(namespace):
        return tag.replace(namespace, "")
    else:
        return None


def parse_child_element(child_elem, indent, formatted):
    """ """
#    print child_elem.tag

    tag = strip_name_space(child_elem.tag, QOS_URN)
    if tag is None:
        tag = strip_name_space(child_elem.tag, POLICY_URN)

    if tag not in functionDict.keys():
        print "--Failed to find parse function for {}".format(child_elem.tag)
    else:
        functionDict[tag](child_elem, indent, formatted)


functionDict = {
    "qos-policy": parse_qos_policy,
    "qos-class": parse_qos_class,
    "qos-profile": parse_qos_profile,
    "subport-name": parse_subport_name,
    "subport": parse_subport,
    "dscp-to-queue-map": parse_dscp_to_queue_map,
    "pcp-to-queue-map": parse_pcp_to_queue_map,
    "queue-statistics": parse_queue_statistics,
    "traffic-class-queues-list": parse_traffic_class_queues_list,
    "traffic-class-rates": parse_traffic_class_rates,
    "weighted-round-robin-weights": parse_weighted_round_robin_weights,
    "token-bucket-rate": parse_token_bucket_rate,
    "token-bucket-size": parse_token_bucket_size,
    "traffic-class-period": parse_traffic_class_period,
    "pipe": parse_pipe,
    "pipe-list": parse_pipe_list,
    "rule": parse_rule,
    "groups": parse_groups,
    "rules": parse_rules,
    "traffic-class-list": parse_traffic_class_list,
    "subport-list": parse_subport_list,
    "vlan-list": parse_vlan_list,
    "shaper": parse_shaper,
    "if-list": parse_if_list,
    "state": parse_state,
    "qos": parse_qos,
    "policy": parse_policy,
}


def main():
    """  """
    print "Hello world\n"
    parser = argparse.ArgumentParser(description='Collect QoS op-mode data')
    parser.add_argument('-i', '--ip', help='ip-address of vRouter')
    parser.add_argument('-x', '--xml', action="store_true",
                        help='print XML output')
    parser.add_argument('-f', '--formatted', action="store_true",
                        help='print formatted output')
    args = parser.parse_args()

    manager.logging.basicConfig(filename="ncclient.log",
                                level=manager.logging.WARNING)
    with manager.connect_ssh(args.ip, username="vyatta", password="vyatta",
                             port=22, hostkey_verify=False, allow_agent=False,
                             look_for_keys=False) as m:
        before = time.time()
        get_elem = new_ele('get')
        filter_elem = sub_ele(get_elem, 'filter', {"type": "subtree"})
        policy_elem = sub_ele(filter_elem, 'policy', {"xmlns": QOS_URN})
        qos_elem = sub_ele(policy_elem, 'qos', {"xmlns": QOS_URN})
        state_elem = sub_ele(qos_elem, 'state', {"xmlns": QOS_URN})
        print to_xml(get_elem, pretty_print=args.formatted)

        qos_stats_xml = m.dispatch(get_elem)

        after = time.time()

        if args.xml:
            print qos_stats_xml
        else:
            qos_stats_tree = objectify.fromstring(qos_stats_xml.data_xml)

            print(objectify.dump(qos_stats_tree))

            for child_elem in qos_stats_tree.iterchildren():
                parse_child_element(child_elem, 0, args.formatted)

    time_diff = after - before
    print "\nTime to dispatch 1 RPC request: {} seconds\n".format(time_diff)


if __name__ == "__main__":
    main()
