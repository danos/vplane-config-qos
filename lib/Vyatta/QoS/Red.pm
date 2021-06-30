# Module QoS::Red.pm
#
# Copyright (c) 2018-2021, AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2013-2015, Brocade Communications Systems, Inc. All rights reserved.
# SPDX-License-Identifier: LGPL-2.1-only


package Vyatta::QoS::Red;
require Exporter;

our @ISA = qw(Exporter);

our @EXPORT = qw(Redparams DEF_QSIZE_BYTES DEF_QSIZE_PACKETS);

use strict;
use warnings;
use Carp;

use Vyatta::QoS::Debug;

use constant DEF_QSIZE_PACKETS => "64";
use constant DEF_QSIZE_BYTES   => "65536";

# Packet Color Set
my %meter_colors = (
    'GREEN'  => 0,
    'YELLOW' => 1,
    'RED'    => 2,
);

# Read RED parameters
sub new {
    my ( $class, $level, $qlimit, $trunk_tc_ref, $id ) = @_;
    my $config = new Vyatta::Config($level);

    # If we don't have a specific RED configuration for this subport check to
    # see if we have a trunk red configuration to inherit from
    if ( not $config->exists() ) {
        if ( defined $trunk_tc_ref ) {
            my $tc_red = ${$trunk_tc_ref}[$id]->{red};

            return $tc_red if defined($tc_red);
        }
        return;
    }

    my $self = {};
    bless $self, $class;

    my $params = getparams( $config, $qlimit );
    $self->{qmax} = $params->{qmax};
    $self->{qmin} = $params->{qmin};
    $self->{prob} = $params->{prob};

    $self->{weight} = $config->returnValue('filter-weight');

    return $self;
}

sub Redparams {
    my ( $level, $rsrc_grp, $subport_tc ) = @_;
    my $config = new Vyatta::Config($level);
    my $params;
    my $qlimit;

    if ( $main::byte_limits ) {
        $qlimit = DEF_QSIZE_BYTES;
    } else {
        $qlimit = DEF_QSIZE_PACKETS;
    }

    if ( defined($subport_tc) && defined( $subport_tc->{limit} ) ) {
        $qlimit = $subport_tc->{limit};
    }

    $params = getparams( $config, $qlimit );

    # If the profile is part of the policy then check the max-threshold
    # If it's a global profile we need to wait till we have the subport
    # and profile information before we can make the test
    if ( index( $level, "policy qos profile" ) == -1 ) {
        invalid
"$level max-threshold $params->{qmax} must be less than qlimit $qlimit\n"
          if defined $params->{qmax} && $params->{qmax} >= $qlimit;
    }

    invalid
"$level min-threshold $params->{qmin} must be less than max-threshold $params->{qmax}\n"
      if defined $params->{qmin}
      && defined $params->{qmax}
      && $params->{qmin} >= $params->{qmax};

    invalid "$level mark-probability not set\n"
      unless defined( $params->{prob} );

    $params->{rsrc_grp} = $rsrc_grp;

    return $params;
}

sub getparams {
    my ( $config, $qlimit ) = @_;
    my $params;

    my $qmax = $config->returnValue('max-threshold');
    $qmax = $qlimit / 2 unless defined($qmax);
    $params->{qmax} = $qmax;

    my $qmin = $config->returnValue('min-threshold');
    $qmin = $qmax / 3 unless defined($qmin);
    $params->{qmin} = $qmin;

    $params->{prob} = $config->returnValue('mark-probability');

    return $params;
}

sub command {
    my ($self) = @_;
    my $color = $meter_colors{GREEN};

    return sprintf ' red %u %u %u %u %u', $color,
      $self->{qmin}, $self->{qmax}, $self->{prob}, $self->{weight};
}

1;
