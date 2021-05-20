#!/usr/bin/env python3
#
# Copyright (c) 2019, AT&T Intellectual Property.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
"""
A module to define a class of Pipe Queue objects
"""

from vyatta_policy_qos_vci.queue import Queue

PERIOD_DEFAULT_MS = 10

class PipeQueues:
    """
    Define the PipeQueues class.  A PipeQueue object describes a group of queue
    objects, which are identified by their pipe-queue-id (0 to 31).
    """
    def __init__(self, pipe_queue_list, tc_block, shaper_tc_block):
        """ Create a PipeQueue object """
        self._pipe_queue = {}
        self._wred_group = {}
        if pipe_queue_list is None:
            return

        for pipe_queue in pipe_queue_list:
            pipe_queue_id = pipe_queue.get('id')
            tc_id = pipe_queue.get('traffic-class')
            wrr_weight = pipe_queue.get('weight')
            priority_local = pipe_queue.get('priority-local')
            wrr_id = tc_block.add_pipe_queue(tc_id, pipe_queue_id,
                                             priority_local)
            is_time = 1
            wred_map_dict = pipe_queue.get('wred-map-time')

            if wred_map_dict is None:
                is_time = 0
                wred_map_dict = pipe_queue.get('wred-map-bytes')

            if wred_map_dict is None:
                is_time = 0
                wred_map_dict = pipe_queue.get('wred-map')

            self._pipe_queue[pipe_queue_id] = Queue(tc_id, wrr_id, wrr_weight,
                                                    priority_local,
                                                    wred_map_dict, is_time, shaper_tc_block)

    def pipe_queue(self, pipe_queue_id):
        """ Return the specified pipe_queue tuple """
        return self._pipe_queue[pipe_queue_id]

    def check(self, path_prefix):
        """ Check if configuration is valid """
        for pipe_queue_id, queue in self._pipe_queue.items():
            result, error, path = queue.check(f"{path_prefix}/queue/{pipe_queue_id}")
            if not result:
                return result, error, path

        return True, None, None

    def commands(self, cmd_prefix):
        """ Generate the necessary commands for this PipeQueue object """
        cmd_list = []
        for pipe_queue_id, queue in self._pipe_queue.items():
            cmd_list.extend(queue.commands(cmd_prefix, pipe_queue_id))

        return cmd_list
