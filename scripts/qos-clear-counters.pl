#! /usr/bin/perl
#
# Copyright (c) 2017-2021, AT&T Intellectual Property. All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

use strict;
use warnings;

use Getopt::Long;
use Config::Tiny;

use lib "/opt/vyatta/share/perl5/";
use Vyatta::Dataplane;
use Vyatta::Interface;
use Vyatta::Config;
use Vyatta::Bonding;
use Vyatta::Configd qw($AUTO $RUNNING);
use Vyatta::Misc qw(getInterfaces);
use Vyatta::QoS::Policy qw(split_ifname);

# Walk through all fabrics issuing "qos clear" requests
sub clear_counters {
    my $if_name = shift;
    my @members =();
    my ( $dpids, $dpsocks ) = Vyatta::Dataplane::setup_fabric_conns();

    for my $fid ( @{$dpids} ) {
        my $sock = ${$dpsocks}[$fid];
        unless ($sock) {
            warn "Can not connect to dataplane $fid\n";
            next;
        }

        if ( !defined($if_name) ) {
            $sock->execute("qos clear");
            $sock->execute("gpc clear qos");
        } else {
            if ($if_name =~ "bond") {
                my ( $if_bond, $vif ) = split_ifname($if_name);
                @members = get_members($if_bond);
                foreach my $port (@members) {
                    # Concatenate port and vif
                    $port = "$port.$vif" if ($vif);

                    $sock->execute("qos clear $port");
                }
            } else {
                $sock->execute("qos clear $if_name");
                $sock->execute("gpc clear qos $if_name");
            }
        }
    }

    # Close down ZMQ sockets. This is needed or sometimes a hang
    # can occur due to timing issues with libzmq - see VRVDR-17233 .
    Vyatta::Dataplane::close_fabric_conns( $dpids, $dpsocks );
    return;
}

sub get_qos_if_list {

    # Generate an ordered list of interfaces that QoS is configured on
    my @iftypes = ( 'dataplane', 'uplink', 'vhost', 'bonding' );
    my @if_list = ();

    my $client = new Vyatta::Configd::Client();
    my $db     = $Vyatta::Configd::Client::AUTO;

    my @interfaces = getInterfaces();
    foreach my $if_name (@interfaces) {
        my $intf      = new Vyatta::Interface($if_name);
        my $intf_type = $intf->type();
        my $match     = 0;

        for (@iftypes) {
            if ( $intf_type eq $_ ) {
                $match = 1;
                last;
            }
        }

        if ( $match == 1 ) {
            my $intf_path = $intf->path();
            my $path      = "$intf_path policy qos";
            if ( $client->node_exists( $db, $path ) ) {
                push @if_list, $if_name;
            }
        }
    }
    print join( ' ', sort(@if_list) ), "\n";

    $client->DESTROY();
}

sub usage {
    print "Usage: $0  \n";
    print "       $0 --clear-all\n";
    print "       $0 --clear-if\n";
    print "       $0 --if-list\n";
    exit 1;
}

my ( $clear_all, $clear_if, $if_list );
GetOptions(
    'clear-all'  => \$clear_all,
    'clear-if=s' => \$clear_if,
    'if-list'    => \$if_list,
) or usage();

clear_counters()            if $clear_all;
clear_counters("$clear_if") if $clear_if;
get_qos_if_list()           if $if_list;
