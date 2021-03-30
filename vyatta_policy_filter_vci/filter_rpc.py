#!/usr/bin/python3
#
# Copyright (c) 2021 AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: GPL-2.0-only
#

""" This is run to get the Qos GPC information from the dataplane
using the RPC API. """


import vplaned


DATAPLANE_CMD = 'gpc show'
GPC_PREFIX_FEAT = 'vyatta-policy-filter-classification-v1:feature'
GPC_PREFIX_INTF = 'vyatta-policy-filter-classification-v1:interface'


def get_gpc_qos_info(feature, intf):
    """ Get the json state for a feature and interface from the dataplane """

    args = DATAPLANE_CMD

    # Add the feature to the command
    try:
        feature
    except Exception:
        pass
    else:
        args += f" {feature}"
    # Add the interface to the command
    try:
        intf
    except Exception:
        pass
    else:
        args += f" {intf}"

    with vplaned.Controller() as controller:
        for dataplane in controller.get_dataplanes():
            with dataplane:

                dp_dict = dataplane.json_command(args)
                if not dp_dict:
                    break

    if dp_dict is not None:
        return dp_dict, 0

    return None, 0


def send_gpc(in_dict) -> None:
    """ Get the state json from the dataplane and return for netconf """
    if in_dict:
        feature = in_dict.get(GPC_PREFIX_FEAT)
        interface = in_dict.get(GPC_PREFIX_INTF)
    info, ret = get_gpc_qos_info(feature, interface)
    return info
