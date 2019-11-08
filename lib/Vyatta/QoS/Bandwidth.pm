# Module Bandwidth.pm
#
# Copyright (c) 2019 AT&T Intellectual Property. All Rights Reserved.
# Copyright (c) 2013-2015, 2017 Brocade Communications Systems, Inc.
# All Rights Reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

package Vyatta::QoS::Bandwidth;
use strict;
use warnings;

use Carp;
use Vyatta::Rate qw(parse_rate);
use Vyatta::QoS::Debug;
use Readonly;

Readonly my $MAX_BANDWIDTH => 10_000_000_000 / 8; # 10Gbit in bytes per second
Readonly my $MIN_BANDWIDTH => 1000;               # 8Kbit or 1K bytes per second

# Default burst size = 4ms in bytes at rate
use constant DEFAULT_BURST_MS => 4;

# Create object based on input
sub new {
    my ( $class, $level, $parent, $oper_speed ) = @_;
    my $config = new Vyatta::Config($level);
    my $self   = {};
    my $percent;
    my $bandwidth;
    bless $self, $class;

    # If oper_speed is provided it takes precedence over bandwidth. The
    # oper_speed is only provided when a subport is created without the
    # bandwidth being specified as shown in the following sequence:
    #     _getVLans->_getSubport->new Subport->new Bandwidth

    if ( defined($oper_speed) ) {
        $bandwidth = $oper_speed;
    } else {
        $bandwidth = $config->returnValue('bandwidth');
        $bandwidth = '100%'
          unless defined($bandwidth);
    }

    my $bps;
    if ( $bandwidth =~ /^([0-9]*\.?[0-9]+)%$/ ) {
        invalid "Bandwidth percent but parent not defined"
          unless defined($parent);

        $percent = $1;
        $bps     = int( $parent->{bps} * $percent ) / 100.;
    } else {
        $bps = parse_rate($bandwidth) / 8;
    }

    invalid "Invalid bandwidth $bandwidth"
      unless defined($bps);

    if ( $bps > $MAX_BANDWIDTH ) {
        invalid 'Bandwidth cannot be higher than 10Gbit';
    }
    if ( $bps < $MIN_BANDWIDTH ) {
        invalid 'Bandwidth cannot be lower than 8Kbit';
    }

    my $burst = $config->returnValue('burst');
    $self->{default_burst} = "";
    if ( !defined($burst) ) {
        $burst = int( ( $bps * DEFAULT_BURST_MS ) / 1000 );
        $self->{default_burst} = 1;
    }

    $self->{bps}     = $bps;
    $self->{burst}   = $burst;
    $self->{percent} = $percent;
    return $self;
}

# Produce rate part of command
sub command {
    my ( $self, $prefix ) = @_;
    my $bps     = $self->{bps};
    my $burst   = $self->{burst};
    my $percent = $self->{percent};

    if ( $self->{default_burst} ) {
        $burst = 0;
    }

    if ( defined($percent) ) {
        $prefix .= " percent $percent size $burst";
    } else {
        $prefix .= " rate $bps size $burst";
    }
    return $prefix;
}

sub valid_binding {
    my ( $self, $min_pkt_len, $intf_name ) = @_;

    if ( not $self->{default_burst} and $min_pkt_len > $self->{burst} ) {
        warn
          "Increasing burst size for interface $intf_name from ",
          "$self->{burst} to smallest supported value of $min_pkt_len bytes\n";
    }
    return 1;
}

1;
