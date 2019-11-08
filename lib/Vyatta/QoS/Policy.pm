# Module QoS::Policy.pm
#
# Copyright (c) 2018-2019, AT&T Intellectual Property. All rights reserved.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

package Vyatta::QoS::Policy;

use Vyatta::Config;
use Vyatta::Interface;
use Vyatta::SwitchConfig;
use Vyatta::DSCP;
use Getopt::Long;
use Vyatta::QoS::Shaper;

require Exporter;
use strict;
use warnings;
use Carp;

our @ISA = qw(Exporter);

our @EXPORT =
  qw(make_policy get_ifindex vif_binding_changed validate_global_profiles list_profiles dscp_check config_same_as_before get_byte_limits);

sub get_byte_limits {
    my $feature_marker =
"/run/vyatta-platform/features/vyatta-policy-qos-groupings-v1/byte-limits";

    return -e $feature_marker;
}

# keys for object factory
my %policies = ( 'shaper' => 'Shaper', );

# Policy factory
# given a name (from CLI) find the name of the perl object
sub make_policy {
    my $name = shift;
    my $top  = 'policy qos name';

    # lookup which policy type
    my $config = new Vyatta::Config("$top $name");
    my @types  = $config->listNodes();

    # undefined if no type given for tag
    return if ( scalar @types == 0 );

    # only one choice allowed after name
    die "multiple policy types listed under $name"
      unless ( scalar @types == 1 );

    my $module = $types[0];              # "shaper"
    my $path   = "$top $name $module";

    # Remove the dynamic import of the qos type since we only
    # support shaper for now.  If we add another it'll probably
    # be more efficient to invoke as we do with the shaper
    # explicitly below.  Done this way it makes the commit
    # time much quicker.
    my $obj = new Vyatta::QoS::Shaper($path);
    die "QoS policy $name not configured"
      unless defined($obj);

    return $obj;
}

# Create a hash keyed by global profile names, each entry value starts at zero
sub init_global_profile_counts {
    my $config = new Vyatta::Config('policy qos');
    my %globals;

    foreach my $name ( $config->listNodes('profile') ) {
        $globals{$name} = 0;
    }
    return \%globals;
}

# Check that all global profiles are referenced by policy attached to an
# interface
sub bump_global_profile_counts {
    my ( $level, $ifname, $globals ) = @_;
    my $config      = new Vyatta::Config("$level $ifname");
    my $policy_name = $config->returnValue("policy qos");

    return unless defined $policy_name;

    my $policy = make_policy($policy_name);

    return unless defined $policy;

    my $router;
    if ( $config->exists("$level $ifname switch-group") ) {
        $router = 0;
    } else {
        $router = 1;
    }
    $policy->init( $ifname, $router );
    $policy->bump_global_profile_counts($globals);
}

sub check_global_profile_counts {
    my $globals = shift;

    while ( my ( $profile, $used ) = each %{$globals} ) {
        warn "warning: global profile $profile defined but has no references\n"
          if ( $used == 0 );
    }
}

sub validate_global_profiles {

    # Create a hash of global profile names, with each count value set to zero
    my $globals = init_global_profile_counts();
    my @iftypes = ( 'dataplane', 'uplink', 'vhost', 'bonding' );

    my $glob_profs = ( scalar keys %$globals );
    return if ( $glob_profs == 0 );

    foreach my $iftype (@iftypes) {

        # Allow the various interface types to increment the global profile
        # counts if their QoS policies references any global profiles
        my $config = new Vyatta::Config("interfaces $iftype");
        foreach my $ifname ( $config->listNodes() ) {
            bump_global_profile_counts( "interfaces $iftype",
                $ifname, $globals );
        }
    }

    # Issue a warning for any global profiles with a zero reference count
    check_global_profile_counts($globals);
}

# could be part of Interface.pm and use ioctl
sub get_ifindex {
    my $ifname = shift;
    open my $sysf, '<', "/sys/class/net/$ifname/ifindex"
      or return;    # undefined
    my $ifindex = <$sysf>;
    close $sysf;
    chomp $ifindex if defined($ifindex);
    return $ifindex;
}

sub dscp_check {
    my $str = shift;
    my @ret = dscp_range($str);

    die "Invalid DSCP $str\n"
      unless ( $#ret >= 0 );
}

# update policy - reapply because policy values changed
sub update_policy {
    my $policy = shift;
    my @iftypes = ( 'dataplane', 'uplink', 'vhost', 'bonding' );

    foreach my $iftype (@iftypes) {

        my $config = new Vyatta::Config("interfaces $iftype");
        foreach my $ifname ( $config->listNodes() ) {
            update_installed_policies( $policy, $ifname, $config );
        }

    }

    return 0;
}

sub config_same_as_before {
    my ($path) = @_;
    my $config = new Vyatta::Config();
    my $now    = $config->returnValue($path);
    my $before = $config->returnOrigValue($path);

    return 1 if not defined $now and not defined $before;

    return 0 if not defined $now xor not defined $before;

    return 1 if $now eq $before;

    return 0;
}

sub vif_binding_changed {
    my ($ifname) = @_;
    my $config   = new Vyatta::Config();
    my $intf     = new Vyatta::Interface($ifname);
    my @vifs     = $config->listNodes("$intf->{path} vif");
    my @oldvifs  = $config->listOrigNodes("$intf->{path} vif");

    # Check for new bindings, or changes in VLAN tag
    foreach my $vif (@vifs) {
        if ( config_same_as_before("$intf->{path} vif $vif policy qos") ) {
            if (
                defined $config->returnValue(
                    "$intf->{path} vif $vif policy qos")
                and not config_same_as_before("$intf->{path} vif $vif vlan") )
            {
                return 1;
            }
        } else {
            return 1;
        }
    }

    # Check for deleted vifs which had bindings
    foreach my $oldvif (@oldvifs) {
        return 1
          if not config_same_as_before("$intf->{path} vif $oldvif policy qos");
    }

    return 0;
}

sub list_profiles {
    my $name            = shift;
    my $global_config   = new Vyatta::Config('policy qos');
    my @global_profiles = $global_config->listNodes('profile');
    my $shaper_config   = new Vyatta::Config("policy qos name $name shaper");
    my @local_profiles  = $shaper_config->listNodes('profile');

    push @global_profiles, @local_profiles;
    print join( ' ', @global_profiles ), "\n";
}

1;
