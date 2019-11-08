# Module QoS::TrafficClass.pm
#
# Copyright (c) 2018-2019 AT&T Intellectual Property.
# All Rights Reserved.
# Copyright (c) 2013-2017, Brocade Communications Systems, Inc.
# All Rights Reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

package Vyatta::QoS::TrafficClass;
use strict;
use warnings;

use Carp;
use Vyatta::Config;
use Vyatta::QoS::Bandwidth;
use Vyatta::QoS::Red;
use Vyatta::QoS::Debug;
use Vyatta::QoS::Red qw(DEF_QSIZE_BYTES);

use constant MAX_TRAFFIC_CLASS => 3;

# Read all the traffic class queue definitions
sub new {
    my ( $class, $level, $parent_bw, $trunk_tc_ref ) = @_;
    my $config = new Vyatta::Config($level);
    my @prio;

    invalid("TC parent bandwidth not defined") unless defined($parent_bw);

    for my $id ( 0 .. MAX_TRAFFIC_CLASS ) {
        my $tc;
        my $limit;

        $tc->{rate} = new Vyatta::QoS::Bandwidth( "$level $id", $parent_bw );

        if ( $level =~ /profile/ ) {
            $prio[$id] = $tc;
            next;
        }

        if ( $main::byte_limits ) {
            $limit = $config->returnValue("$id queue-limit-bytes");
        } else {
            $limit = $config->returnValue("$id queue-limit");
        }
        if ( not defined $limit ) {
            # If no subport queue-limit, try to inherit from trunk
            if ( defined $trunk_tc_ref ) {
                $limit = ${$trunk_tc_ref}[$id]->{limit};
            }
        }
        if ( defined $limit ) {

            # If a value has been set, use it.
            $tc->{limit} = $limit;
        }

	if ( $main::byte_limits ) {
	    $tc->{red} = new Vyatta::QoS::Red( "$level $id random-detect-bytes",
					       $limit, $trunk_tc_ref, $id );
	} else {
	    $tc->{red} = new Vyatta::QoS::Red( "$level $id random-detect",
					       $limit, $trunk_tc_ref, $id );
	}

        $prio[$id] = $tc;
    }

    my $self = \@prio;
    bless $self, $class;
    return $self;
}

# generate array of commands for each traffic class
sub commands {
    my ( $self, $sub_prefix, $port_prefix ) = @_;
    my @cmds;

    for my $id ( 0 .. MAX_TRAFFIC_CLASS ) {
        my $tc   = $self->[$id];
        my $rate = $tc->{rate};

        # rates per subport(vlan) per traffic class
        push @cmds, $rate->command("$sub_prefix queue $id");

        # queue size only valid at top (port level)
        next unless defined($port_prefix);

        my $qlen = $tc->{limit};
        my $red  = $tc->{red};

        if ( $main::byte_limits and not defined($qlen) ) {
            $qlen = DEF_QSIZE_BYTES;
        }

        # cmd is qos IFINDEX param TC ...
        my $cmd = "$port_prefix $id";
        if ( $main::byte_limits ) {
            $cmd .= " limit bytes $qlen" if defined($qlen);
        } else {
            $cmd .= " limit packets $qlen" if defined($qlen);
        }

        if ( defined($red) ) {
            $cmd .= $red->command();
        }

        push @cmds, $cmd;
    }

    return @cmds;
}

# Validate that these Traffic Classes can be bound
sub valid_binding {
    my ( $self, $min_pkt_len, $period, $period_is_default, $location ) = @_;

    for my $id ( 0 .. MAX_TRAFFIC_CLASS ) {
        my $tc = $self->[$id];

        my $min_period = ( $min_pkt_len * 1000 ) / ( $tc->{rate}->{bps} );
        $min_period = int($min_period) + 1;
        invalid "Minimum necessary period for $location is $min_period."
          if ( $min_period > $period && not $period_is_default );

        if ( defined $tc->{red} ) {
            $tc->{red}->valid_binding( $id, $tc->{limit} );
        }
    }

    return 1;
}

1;
