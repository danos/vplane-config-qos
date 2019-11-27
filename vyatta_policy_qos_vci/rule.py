#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
This module calls the Perl FWHelper.pm module, that is found in
/opt/vyatta/share/perl5/Vyatta/FWHelper.pm, to interrogate configd for QoS
class match rules used by a QoS policy, and to turn them into NPF firewall
rules.   It does so by spawning a sub-process that runs a perl script that
established a configd session and then calls the build_rule function of
FWHelper.pm.
"""
import logging
import os
import subprocess

LOG = logging.getLogger('Policy QoS VCI')

def RunGetOutput(cmd, chk_err=True):
    """
    Wrapper for subprocess.run.
    Execute 'cmd'.  Returns return code and STDOUT, trapping expected exceptions.
    Reports exceptions to Error if chk_err parameter is True
    """
    try:
        process = subprocess.run(cmd, check=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        if chk_err:
            LOG.error(f'CalledProcessError.  Error Code is {str(exc.returncode)}')
            LOG.error(f'CalledProcessError.  Command string was {exc.cmd}')
            LOG.error(f'CalledProcessError.  Command result was {exc.stdout[:-1]}')
        return exc.returncode, exc.stdout

    return process.returncode, process.stdout

class Rule:
    """
    Define the Rule class.  A Rule object holds all the information necessary
    to describe a single NPF rule.
    """
    def __init__(self, policy_name, class_id, rule):
        """ Create a Rule object """
        rule_id = rule['id']
        cmd = ['/opt/vyatta/share/perl5/Vyatta/QoS/rule.pm',
               f"{policy_name}", f"{class_id}", f"{rule_id}"]
        _, output = RunGetOutput(cmd)
        self._commands = output

    def commands(self):
        """ Generate the rule command """
        return self._commands
