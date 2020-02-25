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
    my ( $class, $level, $parent ) = @_;
    my $config = new Vyatta::Config($level);
    my $self   = {};
    my $percent;
    my $burst_time;
    bless $self, $class;

    my $bandwidth = $config->returnValue('bandwidth');
    $bandwidth = '100%'
      unless defined($bandwidth);

    my $bps = $MAX_BANDWIDTH;
    if ( $bandwidth =~ /^([0-9]*\.?[0-9]+)%$/ ) {
        $percent = $1;
        $bps = int( ( $parent->{bps} * $percent ) / 100. )
          unless !defined($parent);
    } else {
        $bps = int( parse_rate($bandwidth) / 8 );
    }

    if ( $bps > $MAX_BANDWIDTH ) {
        invalid 'Bandwidth cannot be higher than 10Gbit';
    }
    if ( $bps < $MIN_BANDWIDTH ) {
        invalid 'Bandwidth cannot be lower than 8Kbit';
    }

    my $burst = $config->returnValue('burst');
    $self->{default_burst} = "";
    if ( !defined($burst) ) {
        $burst_time = DEFAULT_BURST_MS;
        $self->{default_burst} = 1;
    } elsif ( $burst =~ /^([1-9][0-9]*)ms(ec)?$/ ) {
        $burst_time = $1;
    }

    if ( defined($burst_time) ) {
        $burst = int( ( $bps * $burst_time ) / 1000 );
    }

    $self->{bps}        = $bps;
    $self->{burst}      = $burst;
    $self->{percent}    = $percent;
    $self->{burst_time} = $burst_time;
    return $self;
}

# Produce rate part of command
sub command {
    my ( $self, $prefix ) = @_;
    my $bps        = $self->{bps};
    my $burst      = $self->{burst};
    my $burst_time = $self->{burst_time};
    my $percent    = $self->{percent};

    if ( defined($percent) ) {
        $prefix .= " percent $percent";
    } else {
        $prefix .= " rate $bps";
    }

    if ( defined($burst_time) ) {
        $prefix .= " msec $burst_time";
    } else {
        $prefix .= " size $burst";
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
