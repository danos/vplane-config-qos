#!/usr/bin/env python3
#
# Copyright (c) 2020-2021, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
The Policy Filter VCI entrypoint module
"""

import argparse
import logging
import logging.handlers
import json
import sys
import vci

from traceback import format_tb
from systemd.journal import JournalHandler

from vyatta_policy_filter_vci.filter_config import FilterConfig
from vyatta_policy_filter_vci.filter_rpc import send_gpc

LOG = logging.getLogger('POLFIL VCI')

POLFIL_CONFIG_FILE = '/etc/vyatta/policy-filter.json'
PLATFORM_ID_FILE = '/var/lib/vyatta-platform/platform-id.conf'

POL_NAMESPACE = 'vyatta-policy-v1'
POLFIL_NAMESPACE = 'vyatta-policy-filter-classification-v1'
RES_NAMESPACE = 'vyatta-resources-v1'
GPC_NAMESPACE = 'vyatta-resources-packet-classifier-v1'


def get_config():
    """ Try to return JSON configuration file """
    filename = POLFIL_CONFIG_FILE
    config = {}
    try:
        with open(filename) as json_data:
            config = json.load(json_data)

    except OSError:
        LOG.info(f"Failed to open JSON config file {filename} "
                 f"{sys.exc_info()[0]}")

    except json.JSONDecodeError:
        LOG.error(f"Failed to decode JSON config file {filename}")

    return config


def save_config(config):
    """ Save the JSON configuration """
    filename = POLFIL_CONFIG_FILE
    with open(filename, "w") as write_file:
        write_file.write(json.dumps(config, indent=4, sort_keys=True))


def get_platform_id():
    """ Return the platform identifier. """
    filename = PLATFORM_ID_FILE
    default_platform_id = 'unknown'
    plat_config = {}
    try:
        with open(filename) as json_data:
            plat_config = json.load(json_data)

    except OSError:
        return default_platform_id

    except json.JSONDecodeError:
        return default_platform_id

    platform_id = plat_config.get('platform-id')
    if platform_id is None:
        return default_platform_id

    return platform_id


class Config(vci.Config):
    """
    The Configuration mode class for Policy Filter VCI
    """
    json_config = {}

    def set(self, new_json_config):
        """
        Do config stuff
        """
        LOG.debug(f"Config:set - {new_json_config}")

        try:
            filter_config = FilterConfig(new_json_config)
            save_config(new_json_config)
            filter_config.build_protobuf()

        except Exception:
            tb_type = sys.exc_info()[0]
            tb_value = sys.exc_info()[1]
            tb_info = format_tb(sys.exc_info()[2])
            tb_output = ""
            for line in tb_info:
                tb_output += line

            LOG.error(f"Unhandled exception: {tb_type}\n{tb_value}\n"
                      f"{tb_output}")

        self.json_config = new_json_config

    def get(self):
        """ Get current config """
        LOG.debug("Config:get")
        if not self.json_config:
            self.json_config = get_config()

        return self.json_config

    def check(self, proposed_config):
        """ Check anything not checked in yang """
        LOG.debug(f"Config:check - {proposed_config}")

        # When the 'resources packet-classifier' config is completely deleted,
        # proposed_config is an empty dictionary and nothing needs to be
        # checked
        if proposed_config:
            filter_config = FilterConfig(proposed_config)
            stat_count = 0

            res_dict = proposed_config[f'{RES_NAMESPACE}:resources']
            gpc_dict = res_dict[f'{GPC_NAMESPACE}:packet-classifier']
            gpc_group_list = gpc_dict['group']

            classifier_bindings = {}
            for fg in filter_config.groups.values():
                errmsg = fg.check(gpc_group_list, classifier_bindings)
                if errmsg is not None:
                    LOG.info(f"Config:check failed for filter-group: "
                             f"{fg.name} {errmsg}")
                    raise vci.Exception("vyatta-policy-qos-vci",
                                        f"Config:check failed for "
                                        f"filter-group {fg.name}: {errmsg}",
                                        "policy/filter-classification")

                stat_count += fg.stats_needed(gpc_group_list)

            platform_id = get_platform_id()
            LOG.debug(f"Platform id: {platform_id}")

            if platform_id == 'ufi.s9700-53dx':
                # The maximum number of statistics that can be allocated on
                # an ufi.s9700-53dx (J2) platform is 4096 due to the size of
                # the allocated statistics engine.
                stat_max = 4096

                if stat_count > stat_max:
                    errmsg = (f"The {stat_count} statistics required is more "
                              f"than maximum supported ({stat_max})")
                    LOG.info(f"Config:stat check failed: {errmsg}")
                    raise vci.Exception("vyatta-policy-qos-vci",
                                        f"Config:check failed: {errmsg}",
                                        "policy/filter-classification")


def rules_updated(data):
    gpc_groups = data.get('vyatta-resources-packet-classifier-v1:groups')

    if gpc_groups is not None:
        filter_config = FilterConfig(get_config())

        for fgroup in filter_config.groups.values():
            if fgroup.classifier in gpc_groups:
                filter_config.build_protobuf()
                return


if __name__ == "__main__":
    try:
        PARSER = argparse.ArgumentParser(
            description='Policy Filter VCI Service')
        PARSER.add_argument(
            '--debug', action='store_true', help='Enabled debugging')
        ARGS = PARSER.parse_args()

        logging.root.addHandler(
            JournalHandler(SYSLOG_IDENTIFIER='vyatta-policy-filter-vci'))

        if ARGS.debug:
            LOG.setLevel(logging.DEBUG)
            LOG.debug("Debug enabled")

        LOG.debug("About to register with VCI")

        (vci.Component("net.vyatta.vci.policy.filter")
         .model(vci.Model("net.vyatta.vci.policy.filter.v1")
                .config(Config())
                .rpc("vyatta-policy-filter-classification-v1",
                     "get-filter-classification-information", send_gpc))
         .subscribe("vyatta-resources-packet-classifier-v1", "rules-update",
                    rules_updated)
         .run()
         .wait())

    except Exception:
        LOG.error(f"Unexpected error: {sys.exc_info()[0]}")
        tb_type = sys.exc_info()[0]
        tb_value = sys.exc_info()[1]
        tb_info = format_tb(sys.exc_info()[2])
        tb_output = ""
        for line in tb_info:
            tb_output += line

        LOG.error(f"Unhandled exception: {tb_type}\n{tb_value}\n"
                  f"{tb_output}")
