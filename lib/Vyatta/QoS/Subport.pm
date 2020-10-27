# Module QoS::Subport.pm
#
# Copyright (c) 2018-2020 AT&T Intellectual Property.
# All Rights Reserved.
# Copyright (c) 2013-2015, 2017 Brocade Communications Systems, Inc.
# All Rights Reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

package Vyatta::QoS::Subport;
use strict;
use warnings;
use Carp;

use Vyatta::Config;
use Vyatta::QoS::Bandwidth;
use Vyatta::QoS::TrafficClass;
use Vyatta::QoS::Queue;

our $PERIOD_DEFAULT = 40;

sub new {
    my ( $class, $level, $vif, $tag, $parent_bw, $default, $trunk_tc_ref ) = @_;
    my $config = new Vyatta::Config($level);
    my $self   = {};
    bless $self, $class;

    my $bw = new Vyatta::QoS::Bandwidth( $level, $parent_bw );
    my $tclass = new Vyatta::QoS::TrafficClass( "$level traffic-class", $bw,
        $trunk_tc_ref );

    $self->{bandwidth} = $bw;
    $self->{tc}        = $tclass;
    $self->{vif}       = $vif;
    $self->{tag}       = $tag;
    $self->{mark_map}  = $config->returnValue('mark-map');

    if ( $config->exists('period') ) {

        # period can be configured on CLI in integer or decimal format
        # milliseconds - convert to microseconds
        $self->{period} = int( $config->returnValue('period') * 1000 );
        $self->{period_is_default} = 0;
    } else {
        $self->{period}            = $PERIOD_DEFAULT * 1000;
        $self->{period_is_default} = 1;
    }

    $self->{default} = $default;
    $self->{class}   = _getClasses($level);
    $self->{profile} = _getProfiles( $level, $bw, $tclass );

    return $self;
}

# Read all the profiles from the config
# return reference to hash name => profile
sub _getProfiles {
    my ( $level, $bw, $subport_tc ) = @_;
    my $config = new Vyatta::Config($level);
    my %profiles;

    foreach my $name ( $config->listNodes('profile') ) {
        $profiles{$name} =
          new Vyatta::QoS::Profile( "$level profile $name", $bw, $subport_tc );
    }

    return \%profiles;
}

# Read all classes from the config
sub _getClasses {
    my $level  = shift;
    my $config = new Vyatta::Config($level);
    my @classes;

    $classes[0] = undef;    # default class

    foreach my $id ( $config->listNodes('class') ) {
        $classes[$id] = new Vyatta::QoS::Class( $level, $id );
    }
    return \@classes;
}

sub bandwidth {
    my $self = shift;

    return $self->{bandwidth};
}

sub tc {
    my $self = shift;

    return $self->{tc};
}

# Generate ordered list of profiles
# reserve 0th for the default
# returns array of name and profile
sub profile_list {
    my ( $self, $global_profiles_ref ) = @_;
    my $profiles = $self->{profile};
    my @list;

    return @list unless defined( $self->{default} );

    my $def_prof_name = $self->{default};
    my $default       = $profiles->{$def_prof_name};

    # check against the global profiles if not local profile
    $default = $global_profiles_ref->{$def_prof_name} unless defined($default);

    push @list, [ $self->{default}, $default ];

    foreach my $name ( sort keys %{$profiles} ) {
        my $profile = $profiles->{$name};
        next if ( $profile eq $default );

        push @list, [ $name, $profile ];
    }

    return @list;
}

# generate parameters for subport
sub commands {
    my ( $self, $ifindex, $sid ) = @_;
    my $prefix = "qos $ifindex subport $sid";
    my @cmds;

    # command for setting bandwidth of this subport
    my $bw  = $self->{bandwidth};
    my $cmd = $bw->command($prefix);

    my $period = $self->{period};
    $cmd .= " period $period" if defined($period);
    push @cmds, $cmd;

    # Traffic class rates, qlen, red, etc
    my $tc = $self->{tc};

    push @cmds, $tc->commands( $prefix, "qos $ifindex param subport $sid" );

    if ( defined( $self->{mark_map} ) ) {
        push @cmds, "$prefix mark-map $self->{mark_map}";
    }
    return @cmds;
}

# Validate that this subport can be bound to an interface
sub valid_binding {
    my ( $self, $intf, $overhead, $global_profiles_ref ) = @_;

    my $config        = new Vyatta::Config( $intf->path() );
    my $vlan_mtu_path = "vif $self->{vif} mtu";
    my $intf_name     = $intf->name();
    if ( $self->{tag} != 0 ) {
        $intf_name .= " vif $self->{vif}";
    }
    my $mtu;
    if ( $intf->type() eq "vhost" ) {
        $mtu = 1522;
    } else {
        if ( $config->exists($vlan_mtu_path) ) {
            $mtu = $config->returnValue($vlan_mtu_path);
        } else {
            $mtu = $intf->mtu();
        }
    }
    my $min_pkt_len = $mtu + $overhead;

    $self->{bandwidth}->valid_binding( $min_pkt_len, $intf_name );

    my $tc = $self->{tc};
    $tc->valid_binding(
        $min_pkt_len, $self->{period},
        $self->{period_is_default},
        "subport $self->{tag}"
    );

    my @profiles = $self->profile_list($global_profiles_ref);
    for my $i ( 0 .. $#profiles ) {
        my ( $name, $profile ) = @{ $profiles[$i] };

        # We may have a profile name without a profile definition, perhaps due
        # to the profile definition commands failing, so just return 1 here
        # as a must statement in the Yang file will catch this, unfortunately
        # the must statement is run after this validation script
        return 1 unless defined($profile);
        return 0 unless $profile->valid_binding( $intf, $overhead );
    }

    return 1;
}

1;
