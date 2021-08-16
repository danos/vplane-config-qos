#! /usr/bin/perl

# Copyright (c) 2019, AT&T Intellectual Property. All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

use strict;
use warnings;

use Getopt::Long;
use JSON qw( decode_json );

use lib "/opt/vyatta/share/perl5/";
use Vyatta::Dataplane;

sub show_buf_threshold {
    my ( $dpids, $dpsocks ) = Vyatta::Dataplane::setup_fabric_conns();

    for my $fid ( @{$dpids} ) {
        my $sock = ${$dpsocks}[$fid];
        unless ($sock) {
            warn "Can not connect to dataplane $fid\n";
            next;
        }

        my $response = $sock->execute("qos show platform buf-threshold");
        next unless defined($response);

        my $decoded = decode_json($response);
        my $threshold_obj = $decoded->{"buf-threshold"};
        my $threshold = $threshold_obj->{'threshold'};
        print "Buffer Congestion Threshold:  $threshold\n\n";
    }
}

# Displays current buffer utiliaztion
sub show_buf_utilization {
    my ( $dpids, $dpsocks ) = Vyatta::Dataplane::setup_fabric_conns();

    for my $fid ( @{$dpids} ) {
        my $sock = ${$dpsocks}[$fid];
        unless ($sock) {
            warn "Can not connect to dataplane $fid\n";
            next;
        }

        my $response = $sock->execute("qos show platform buf-utilization");
        next unless defined($response);

        my $decoded = decode_json($response);
        my $buf_stats = $decoded->{"ext-buf-stats"};
        my $total_buf_units = $buf_stats->{'total-buf-units'};
        my $total_rejected = $buf_stats->{'total-rejected-packets'};
        my $notification_mode = $buf_stats->{'mode'};
        print "Total Buffer Units: $total_buf_units\n";
        print "Total Dropped Packets due to buffer failures: $total_rejected\n";
        print "Current SNMP notification mode: $notification_mode\n\n";

        my @samples = @{ $buf_stats->{'latest-samples'} };
        print  "Sample |  Free |  Used | Utilization | Dropped Pkts\n";
        foreach my $idx ( 0 .. $#samples ) {
            my $buf_free = $samples[$idx]->{'free'};
            my $buf_used = $samples[$idx]->{'used'};
            my $buf_uti_rate = $samples[$idx]->{'uti-rate'};
            my $pkt_dropped = $samples[$idx]->{'rejected'};
            printf "%6d | %5d | %5d | %10d%% | %12d\n",
                $idx + 1, $buf_free, $buf_used, $buf_uti_rate, $pkt_dropped;
        }
        print  "\n";
    }
}

sub usage {
    print "Usage: $0 --threshold\n";
    print "       $0 --utilization\n";
    exit 1;
}

my ($buf_threshold, $buf_statsation);

GetOptions(
    'threshold'   => \$buf_threshold,
    'utilization' => \$buf_statsation,
) or usage();

show_buf_threshold()     if $buf_threshold;
show_buf_utilization()   if $buf_statsation;
