#!/usr/bin/env python3

# Copyright (c) 2021, Ciena Corporation, All Rights Reserved
#
# SPDX-License-Identifier: LGPL-2.1-only

from typing import Dict, List, Optional


class DropSummaryTableRow:
    """ Represents a single row of data in the output """

    def __init__(self, interface_name):
        self.interface_name: str = interface_name
        self.packet_data: Optional[Dict[int]] = {"queued_packets": 0,
                                                 "dropped_packets": 0,
                                                 "dropped_percentage": 0}

    def __iter__(self):
        """
        Class has to be iterable so the tabulate library can print the attributes.
        Each yield command returns a value to place in the row going from left to
        right.
        When no packet data is available return None for queued_packets, dropped_packets
        and dropped_percentage.
        """
        yield self.interface_name
        if self.packet_data:
            yield self.packet_data["queued_packets"]
            yield self.packet_data["dropped_packets"]
            yield self.packet_data["dropped_percentage"]
        else:
            yield None
            yield None
            yield None

    def __lt__(self, other):
        """
        Class has to be sortable so table rows can be ordered by dropped percentage.
        If interface does not have a qos policy then place it to the bottom (low)
        Treat interface 'Total' as an exception and always place it at the top (high)
        """
        if self.interface_name == "Total":
            return False
        elif other.interface_name == "Total":
            return True
        else:
            left = self.packet_data["dropped_percentage"] if self.packet_data else -1
            right = other.packet_data["dropped_percentage"] if other.packet_data else -1
            return left < right


def get_qos_data() -> Dict:
    """
    Get qos data from the dataplane(s).
    Combine the data into 1 dictionary and return it
    """

    from vplaned import Controller

    aggregated_qos_data = {}
    with Controller() as ctrl:
        for dataplane in ctrl.get_dataplanes():
            with dataplane:
                qos_data = dataplane.json_command("qos optimised-show")
                aggregated_qos_data.update(qos_data)
    return aggregated_qos_data


def extract_drop_summary_data(qos_data: Dict) -> List[DropSummaryTableRow]:
    """
    Given all the qos data, for each interface populate the table row information. Add a final row
    which totals the packet data from each interface.
    """

    class NoSubports(Exception):
        pass

    table_data: List[DropSummaryTableRow] = []
    total = DropSummaryTableRow("Total")
    assert total.packet_data

    for interface in qos_data:
        row = DropSummaryTableRow(interface)
        assert row.packet_data
        try:
            subports = qos_data[interface]['shaper']['subports']
            if subports:
                for subport in subports:
                    for tc in subport['tc']:
                        row.packet_data["queued_packets"] += tc['packets']
                        row.packet_data["dropped_packets"] += tc['dropped'] + \
                            tc['random_drop']
            else:
                raise NoSubports
        except (KeyError, NoSubports):
            # Interface does not have qos
            row.packet_data = None

        if row.packet_data and row.packet_data["queued_packets"] > 0:
            row.packet_data["dropped_percentage"] = ((row.packet_data["dropped_packets"]
                                                      / row.packet_data["queued_packets"])
                                                     * 100)

            total.packet_data["queued_packets"] += row.packet_data["queued_packets"]
            total.packet_data["dropped_packets"] += row.packet_data["dropped_packets"]
            total.packet_data["dropped_percentage"] += row.packet_data["dropped_percentage"]
        table_data.append(row)

    table_data.append(total)

    # Show interfaces with most drops at the top.
    table_data.sort(reverse=True)

    return table_data


def print_table(tabular_data: List[DropSummaryTableRow]):
    from tabulate import tabulate, TableFormat, Line, DataRow

    vyatta_fmt = TableFormat(
        lineabove=Line("", "-", "", ""),
        linebelowheader=Line("", "-", "", ""),
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("", "", ""),
        datarow=DataRow("", "", ""),
        padding=1,
        with_header_hide=("lineabove"))

    print(tabulate(tabular_data,
                   headers=["Interfaces", "Queued Packets",
                            "Dropped Packets", "Dropped Percentage"],
                   floatfmt=".3f",
                   missingval="-",
                   tablefmt=vyatta_fmt))


def get_difference(prev_table: List[DropSummaryTableRow], curr_table: List[DropSummaryTableRow]) -> List[DropSummaryTableRow]:
    """
    For each interface in the current table determine how many packets were queued/dropped
    since the previous time.
    """

    diff_table = []
    # Convert prev_table to a dictionary for fast lookup
    prev_table_dict = {row.interface_name: row for row in prev_table}

    for curr_row in curr_table:
        diff_row = DropSummaryTableRow(curr_row.interface_name)
        try:
            prev_row = prev_table_dict[curr_row.interface_name]

            assert diff_row.packet_data
            if curr_row.packet_data and prev_row.packet_data:
                diff_row.packet_data["queued_packets"] = (curr_row.packet_data["queued_packets"]
                                                          - prev_row.packet_data["queued_packets"])
                diff_row.packet_data["dropped_packets"] = (curr_row.packet_data["dropped_packets"]
                                                           - prev_row.packet_data["dropped_packets"])
                if diff_row.packet_data["queued_packets"] > 0:
                    diff_row.packet_data["dropped_percentage"] = ((diff_row.packet_data["dropped_packets"]
                                                                   / diff_row.packet_data["queued_packets"])
                                                                  * 100)
            else:
                diff_row.packet_data = None
        except KeyError:
            # A new interface has been added and there is no previous data to compare it against
            diff_row.packet_data = None

        diff_table.append(diff_row)

    diff_table.sort(reverse=True)
    return diff_table


def monitor_drop_summary():
    """
    handle op mode command: monitor policy qos summary
    Once per second it will retrieve the current qos drop summary data, calculate what has changed since the last retrieval
    and print that information.
    """

    import sys
    import time

    # Get initial data
    prev_table = extract_drop_summary_data(get_qos_data())
    time.sleep(1)

    try:
        while True:
            curr_table = extract_drop_summary_data(get_qos_data())
            diff_table = get_difference(prev_table, curr_table)
            prev_table = curr_table

            print_table(diff_table)
            time.sleep(1)

            # Move cursor up to start of table so the next print overwrites existing table
            # length = Number of rows + header + header seperator
            length = len(diff_table) + 2
            ansi_cmd_to_move_cursor_up_length_lines = f"\u001b[{length}A"
            print(ansi_cmd_to_move_cursor_up_length_lines, end="")

    except KeyboardInterrupt:
        # Since the command runs forever Ctrl-C is used to stop the command which raises a KeyboardInterrupt exception
        # Catch the exception to stop python printing the traceback and to move the cusor to bottom of buffer
        # so it doesn't overwrite the table.
        ansi_cmd_to_move_cursor_down_length_lines = f"\u001b[{length}B"
        print(ansi_cmd_to_move_cursor_down_length_lines, end="")
        sys.exit(1)


def show_drop_summary():
    """ handle op mode command: show policy qos summary """
    qos_data = get_qos_data()
    table_data = extract_drop_summary_data(qos_data)
    print_table(table_data)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="""Policy QoS VCI Service.
    If the command line switch doesn't exist please try using legacy script show-queueing.pl""")

    parser.add_argument('-ds', '--drop-summary', action='store_true',
                        help='Show aggregate summary from all vlans')
    parser.add_argument('-m', '--monitor', action='store_true',
                        help='Show live updates ')
    args = parser.parse_args()

    if (args.drop_summary and args.monitor):
        monitor_drop_summary()
    elif (args.drop_summary):
        show_drop_summary()
