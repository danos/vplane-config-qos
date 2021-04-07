#!/usr/bin/python3
#
# Copyright (c) 2021 AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: GPL-2.0-only
#

""" This is run to get the Qos GPC information from the dataplane via a
RPC and print the information for op-mode support. """


import sys


def print_gpc_actions(rule):
    """ Print the actions configured for this rule """
    for key in rule:
        if key in ("designation", "colour"):
            txt = "action: ".rjust(37)
            print(f"{txt}{key} {rule[key]}")
        if key == "police":
            txt = "action: policer".rjust(44)
            pol_params = rule[key]
            txt2 = str(pol_params['drops']).rjust(24)
            print(f"{txt}{txt2} Drops")


def print_gpc_tables(tbl_dict):
    """ Print the tables configured for this feature """
    # Print the banner
    gpc = tbl_dict['gpc']
    txt = "Group".ljust(17)
    txt2 = "Interface".ljust(12)
    txt3 = "Result[rule]".ljust(35)
    print(f"{txt}{txt2}{txt3}Counters")
    print('-'.ljust(80, '-'))

    features = gpc['features']
    for feature in features:
        if feature['type'] == 'qos':
            tables = feature['tables']
            # Now go through the tables
            for table in tables:
                txt = table['table-names'][0]['name'].ljust(17)
                table_id = table['table-id'].split('/')
                txt2 = table_id[0].ljust(12)
                print(f"{txt}{txt2}", end='')

                # Print the rules for each table
                for rule in table['rules']:
                    txt = f"{rule['result']}[{rule['rule-number']}]".ljust(22)
                    counter = rule['counter']
                    txt2 = str(counter['packets']).rjust(17)
                    print(f"{txt}{txt2} Packets")
                    print_gpc_actions(rule)
                    print("".rjust(29), end='')
                print("")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Invalid input arguments : prog ifname")
        exit(1)
    ifname = ""
    if len(sys.argv) == 2:
        ifname += f"{sys.argv[1]}"

    from vyatta import configd
    client: configd.Client = configd.Client()

    Dict = client.call_rpc_dict("vyatta-policy-filter-classification-v1",
                                "get-filter-classification-information",
                                {"feature": "qos", "interface": f"{ifname}"})
    if Dict is not None:
        print_gpc_tables(Dict)
    exit(0)
