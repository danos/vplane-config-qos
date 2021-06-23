#!/usr/bin/env python3
# Copyright (c) 2021, AT&T Intellectual Property. All rights reserved.
# SPDX-License-Identifier: LGPL-2.1-only

# -*- coding: utf-8 -*-


import argparse
import time

from lxml import objectify

from ncclient import manager
from ncclient.xml_ import new_ele, sub_ele, to_xml

QOS_URN = "{urn:vyatta.com:mgmt:vyatta-policy-qos:1}"
POLICY_URN = "{urn:vyatta.com:mgmt:vyatta-policy:1}"


def parse_qos_policy(qos_policy_elem, indent, formatted):
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    qos_policy = qos_policy_elem.text
    print(f"{spaces}qos-policy: {qos_policy}")


def parse_qos_class(qos_class_elem, indent, formatted):
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    qos_class = qos_class_elem.text
    print(f"{spaces}qos-class: {qos_class}")


def parse_qos_profile(qos_profile_elem, indent, formatted):
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    qos_profile = qos_profile_elem.text
    print(f"{spaces}qos-profile: {qos_profile}")


def parse_subport_name(subport_name_elem, indent, formatted):
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    subport_name = subport_name_elem.text
    print(f"{spaces}subport name: {subport_name}")


def parse_subport(subport_elem, indent, formatted):
    """ """
#    print("--subport--")
#    print(objectify.dump(subport_elem))
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    subport_number = subport_elem.text
    print(f"{spaces}subport number: {subport_number}")


def parse_dscp_to_queue_map(dscp_to_queue_map_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print(f"{spaces}--dscp-to-queue-map--")
#    print(objectify.dump(dscp_to_queue_map_elem))
    dscp_value = dscp_to_queue_map_elem.find(QOS_URN + "dscp")
    queue = dscp_to_queue_map_elem.find(QOS_URN + "queue")
    tc = dscp_to_queue_map_elem.find(QOS_URN + "traffic-class")

    print(f"{spaces}dscp: {dscp_value}, queue: {queue}, traffic-class: {tc}")


def parse_pcp_to_queue_map(pcp_to_queue_map_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print(f"{spaces}--pcp-to-queue-map--")
#    print(objectify.dump(pcp_to_queue_map_elem))
    pcp_value = pcp_to_queue_map_elem.find(QOS_URN + "pcp")
    queue = pcp_to_queue_map_elem.find(QOS_URN + "queue")
    tc = pcp_to_queue_map_elem.find(QOS_URN + "traffic-class")

    print(f"{spaces}pcp: {pcp_value}, queue: {queue}, traffic-class: {tc}")


def parse_queue_statistics(queue_stats_elem, tc, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print(f"{spaces}--queue-statistics--")
#    print(objectify.dump(queues_stats_elem))
    queue = queue_stats_elem.find(QOS_URN + "queue")
    databytes = queue_stats_elem.find(QOS_URN + "bytes")
    dropped = queue_stats_elem.find(QOS_URN + "dropped")
    packets = queue_stats_elem.find(QOS_URN + "packets")
    qlen = queue_stats_elem.find(QOS_URN + "qlen")
    random_drops = queue_stats_elem.find(QOS_URN + "random-drop")

    print(f"{spaces}tc/queue {tc}/{queue} - bytes: {databytes}, "
          f"dropped: {dropped}, packets: {packets}, "
          f"random-drops: {random_drops}, qlen: {qlen}")


def parse_traffic_class_queues_list(tc_queues_list_elem, indent, formatted):
    """ """
#    spaces = "".ljust(indent)
#    print(f"{spaces}--traffic-class-queues-list--")
#    print(objectify.dump(tc_queues_list_elem))
    tc = tc_queues_list_elem.find(QOS_URN + "traffic-class")
    queue_stats_elem = tc_queues_list_elem.find(QOS_URN + "queue-statistics")
    parse_queue_statistics(queue_stats_elem, tc, indent+2, formatted)


def parse_traffic_class_rates(tc_rates_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print(f"{spaces}--traffic-class-rates--")
#    print(objectify.dump(tc_rates_elem))
    tc = tc_rates_elem.find(QOS_URN + "traffic-class")
    rate = tc_rates_elem.find(QOS_URN + "rate")
    print(f"{spaces}traffic-class: {tc}, rate: {rate}")
    rate = tc_rates_elem.find(QOS_URN + "rate-64")
    print(f"{spaces}traffic-class: {tc}, rate: {rate}")


def parse_weighted_round_robin_weights(wrr_weights_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print(f"{spaces}--weighted-round-robin-weights--")
#    print(objectify.dump(wrr_weights_elem))
    queue = wrr_weights_elem.find(QOS_URN + "queue")
    weight = wrr_weights_elem.find(QOS_URN + "weight")
    print(f"{spaces}queue: {queue}, weight: {weight}")


def parse_token_bucket_rate(tb_rate_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    tb_rate = tb_rate_elem.text
    print(f"{spaces}token-bucket-rate: {tb_rate}")


def parse_token_bucket_rate_64(tb_rate_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    tb_rate = tb_rate_elem.text
    print(f"{spaces}token-bucket-rate-64: {tb_rate}")


def parse_token_bucket_size(tb_size_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    tb_size = tb_size_elem.text
    print(f"{spaces}token-bucket-size: {tb_size}")


def parse_traffic_class_period(tc_period_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    tc_period = tc_period_elem.text
    print(f"{spaces}traffic-class-period: {tc_period}")


def parse_traffic_class_period_usec(tc_period_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    tc_period = tc_period_elem.text
    print(f"{spaces}traffic-class-period-usec: {tc_period}")


def parse_pipe(pipe_elem, indent, formatted):
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    pipe_number = pipe_elem.text
    print(f"{spaces}pipe: {pipe_number}")


def parse_pipe_list(pipe_list_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    pipe_number = pipe_list_elem.find(QOS_URN + "pipe").text
    print(f"{spaces}--pipe-list--{pipe_number}")
#    print(objectify.dump(pipe_list_elem))

    for child_elem in pipe_list_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def parse_rule(name, rules_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print(f"{spaces}--rule--")
#    print(objectify.dump(rules_elem))
    rule_number = rules_elem.find(QOS_URN + "rule-number")
    qos_class = rules_elem.find(QOS_URN + "qos-class")
    action_group = rules_elem.find(QOS_URN + "action-group")
    policer_pkts_excd = rules_elem.find(QOS_URN + "exceeded-packets")
    policer_byts_excd = rules_elem.find(QOS_URN + "exceeded-bytes")
    databytes = rules_elem.find(QOS_URN + "bytes")
    packets = rules_elem.find(QOS_URN + "packets")
    print(f"{spaces}rule: {name}, qos-class: {qos_class}, rule-number: "
          f"{rule_number} - packets: {packets}, bytes: {databytes}")
    print(f"action-group: {action_group}, policer_pkts_excd: "
          f"{policer_pkts_excd}, policer_byts_excd: {policer_byts_excd}")


def parse_groups(groups_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print(f"{spaces}--groups--")
#    print(objectify.dump(groups_elem))
    name = groups_elem.find(QOS_URN + "name")
    for child_elem in groups_elem.iterchildren():
        if child_elem.tag == QOS_URN + "rule":
            parse_rule(name, child_elem, indent+2, formatted)


def parse_rules(rules_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print(f"{spaces}--rules--")
#    print(objectify.dump(rules_elem))
    for child_elem in rules_elem.iterchildren():
        if child_elem.tag == QOS_URN + "groups":
            parse_groups(child_elem, indent+2, formatted)
        else:
            print(f"--unknown rules element: {child_elem.tag}")


def parse_traffic_class_list(traffic_class_list_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
#    print(f"{spaces}--traffic-class-list--")
#    print(objectify.dump(traffic_class_list_elem))
    tc = traffic_class_list_elem.find(QOS_URN + "traffic-class")
    data_bytes = traffic_class_list_elem.find(QOS_URN + "bytes")
    dropped = traffic_class_list_elem.find(QOS_URN + "dropped")
    packets = traffic_class_list_elem.find(QOS_URN + "packets")
    random_drops = traffic_class_list_elem.find(QOS_URN + "random-drop")

    print(f"{spaces}tc: {tc}, bytes: {data_bytes}, dropped: {dropped}, "
          f"packets: {packets}, random-drops: {random_drops}")


def parse_subport_list(subport_list_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    subport_number = subport_list_elem.find(QOS_URN + "subport")
    print(f"{spaces}--subport-list-- {subport_number}")
#    print(objectify.dump(subport_list_elem))

    for child_elem in subport_list_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def parse_vlan_list(vlan_list_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print(f"{spaces}--vlan-list--")
#    print(objectify.dump(vlan_list_elem))

    for child_elem in vlan_list_elem.iterchildren():
        if child_elem.tag == QOS_URN + "tag":
            vlan_tag = child_elem.text
        elif child_elem.tag == QOS_URN + "subport":
            subport_number = child_elem.text
        else:
            print(f"--unknown vlan-list element: {child_elem.tag}")

    print(f"{spaces}vlan-tag: {vlan_tag}, subport: {subport_number}")


def parse_shaper(ifname, shaper_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print(f"{spaces}--{ifname} shaper--")
#    print(objectify.dump(shaper_elem))

    for child_elem in shaper_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def parse_if_list(if_list_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print(f"{spaces}--if-list--")
#    print(objectify.dump(if_list_elem))
    ifname = if_list_elem.find(QOS_URN + "ifname")
    shaper = if_list_elem.find(QOS_URN + "shaper")
    if ifname is not None and shaper is not None:
        parse_shaper(ifname, shaper, indent+2, formatted)
    else:
        print(f"--Failed to parse if-list - ifname: {ifname}, shaper: {shaper}")


def parse_state(state_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print(f"{spaces}--state--")
#    print(objectify.dump(state_elem))
    for child_elem in state_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def parse_qos(qos_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print(f"{spaces}--qos--")
#    print(objectify.dump(qos_elem))
    for child_elem in qos_elem.iterchildren():
        parse_child_element(child_elem, indent+2, formatted)


def parse_policy(policy_elem, indent, formatted):
    """ """
    if not formatted:
        indent = 0
    spaces = "".ljust(indent)
    print(f"{spaces}--policy--")
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
#    print(child_elem.tag)

    tag = strip_name_space(child_elem.tag, QOS_URN)
    if tag is None:
        tag = strip_name_space(child_elem.tag, POLICY_URN)

    if tag not in functionDict.keys():
        print(f"--Failed to find parse function for {child_elem.tag}")
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
    "token-bucket-rate-64": parse_token_bucket_rate_64,
    "token-bucket-size": parse_token_bucket_size,
    "traffic-class-period": parse_traffic_class_period,
    "traffic-class-period-usec": parse_traffic_class_period_usec,
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
    print("Hello world\n")
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
        # The following sub_ele calls filter the amount of XML data returned
        # by the call to m.dispatch
        filter_elem = sub_ele(get_elem, 'filter', {"type": "subtree"})
        policy_elem = sub_ele(filter_elem, 'policy', {"xmlns": QOS_URN})
        qos_elem = sub_ele(policy_elem, 'qos', {"xmlns": QOS_URN})
        sub_ele(qos_elem, 'state', {"xmlns": QOS_URN})
        print(to_xml(get_elem, pretty_print=args.formatted))

        qos_stats_xml = m.dispatch(get_elem)

        after = time.time()

        if args.xml:
            print(qos_stats_xml)
        else:
            qos_stats_tree = objectify.fromstring(qos_stats_xml.data_xml)

            print(objectify.dump(qos_stats_tree))

            for child_elem in qos_stats_tree.iterchildren():
                parse_child_element(child_elem, 0, args.formatted)

    time_diff = after - before
    print(f"\nTime to dispatch 1 RPC request: {time_diff} seconds\n")


if __name__ == "__main__":
    main()
