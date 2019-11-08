# Module QoS::Queue.pm
#
# Copyright (c) 2017-2019, AT&T Intellectual Property.
# All Rights Reserved.
# Copyright (c) 2013-2015, Brocade Communications Systems, Inc.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

package Vyatta::QoS::Queue;
use Vyatta::QoS::Red qw(Redparams);
use Vyatta::QoS::Debug qw(invalid);
use strict;
use warnings;

use constant TRAFFIC_CLASS_SHIFT => 2;

sub new {
    my ( $class, $level, $tc, $qind, $local, $w, $id, $subport_tc ) = @_;
    my $self   = {};
    my $config = new Vyatta::Config("$level queue $id");

    $self->{tc}      = $tc;
    $self->{index}   = $qind;
    $self->{local}   = $local;
    $self->{weight}  = defined($w) ? $w : 1;
    $self->{conf_id} = $id;

    if ( $config->exists("wred-map dscp-group") ) {
        $self->{wred_map} =
          _getWred( "$level queue $id wred-map dscp-group", $subport_tc );
        $self->{wred_weight} = $config->returnValue("wred-map filter-weight");

        invalid "$level filter-weight not set\n"
          unless defined( $self->{wred_weight} );
    } elsif ( $config->exists("wred-map-bytes dscp-group") ) {
        $self->{wred_map} =
          _getWred( "$level queue $id wred-map-bytes dscp-group", $subport_tc );
        $self->{wred_weight} =
          $config->returnValue("wred-map-bytes filter-weight");

        invalid "$level filter-weight not set\n"
          unless defined( $self->{wred_weight} );
    }

    bless $self, $class;
    return $self;
}

sub _add_to_reversed_ordered_list {
    my $old_list = shift;
    my $new_wred = shift;
    my @new_list;
    my $cur_wred;
    my $dp = 0;

    $cur_wred = shift @{$old_list};
    while ( defined($cur_wred) ) {
        if ( $cur_wred->{qmin} > $new_wred->{qmin} ) {

            # move old item into list
            push @new_list, $cur_wred;
            $dp += 1;
        } else {

            # insert new item into list
            $new_wred->{dp} = $dp;
            push @new_list, $new_wred;
            $dp += 1;
            while ( defined($cur_wred) ) {

                # append rest of old list
                $cur_wred->{dp} = $dp;
                push @new_list, $cur_wred;
                $dp += 1;
                $cur_wred = shift @{$old_list};
            }
            return @new_list;
        }
        $cur_wred = shift @{$old_list};
    }

    # add first item to list
    $new_wred->{dp} = $dp;
    push @new_list, $new_wred;
    return @new_list;
}

sub _getWred {
    my ( $level, $subport_tc ) = @_;
    my $config = new Vyatta::Config($level);
    my @wred_maps;
    my $map;

    foreach my $rsrc_grp ( $config->listNodes() ) {
        $map = Redparams( "$level $rsrc_grp", $rsrc_grp, $subport_tc );

        # The order of this list of wred-maps is important.  It is reverse
        # ordered by min-threshold (i.e. highest first, lowest last).
        # The first wred-map will be allocated a drop-precedence of zero, the
        # second wred-map will get a dp of one, and the third wred-map will get
        # a dp of two.
        @wred_maps = _add_to_reversed_ordered_list( \@wred_maps, $map );
    }
    return \@wred_maps;
}

# Look for a wred-map configuration with a matching dscp-group name, return
# its drop-precedence if it exists, or zero if it doesn't
sub getdp {
    my $self     = shift;
    my $grp_name = shift;
    my $dp       = 0;

    foreach my $map ( @{ $self->{wred_map} } ) {
        if ( $map->{rsrc_grp} eq $grp_name ) {
            return $dp;
        } else {
            $dp += 1;
        }
    }
    return $dp;
}

# Encoding (for dataplane) of DPDK traffic-class and queue
sub qmap {
    my $self = shift;

    return $self->{tc} | $self->{index} << TRAFFIC_CLASS_SHIFT;
}

# export wrr-weight to send to dataplane
sub wrr {
    my $self = shift;

    return $self->{weight};
}

# Is this queue marked as high priority local?
sub local {
    my $self = shift;

    return $self->{local};
}

sub conf_id {
    my $self = shift;

    return $self->{conf_id};
}

1;
