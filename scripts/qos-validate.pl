#!/usr/bin/perl

# Copyright (c) 2018-2019, AT&T Intellectual Property. All rights reserved.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

use strict;
use warnings;

use lib "/opt/vyatta/share/perl5";

use Getopt::Long;
use Vyatta::Config;
use Vyatta::Interface;
use Vyatta::QoS::Policy
  qw(make_policy validate_global_profiles list_profiles dscp_check get_byte_limits);

our $byte_limits;

our @ISA = qw(Exporter);

our @EXPORT = qw($byte_limits);

# check if policy is valid
sub validate_policy {

    $byte_limits = get_byte_limits();

    my $pol_config = new Vyatta::Config("policy qos name");
    foreach my $name ( $pol_config->listNodes() ) {
        if ( not $pol_config->isChanged("$name") ) {
            next;
        }
        my $policy = make_policy($name);
        if ( not defined($policy) ) {
            next;
        }
        exit 1 unless $policy->valid();
    }
}

# Validate binding a policy to an interface
sub validate_binding {
    my ( $ifname, $vif ) = @_;

    my $intf = new Vyatta::Interface($ifname);
    die "Interface $ifname does not exist"
      unless defined($intf);

    my $config = new Vyatta::Config( $intf->path() );

    my $name = $config->returnValue('policy qos');

    # This error now caught and reported by yang
    exit 0 unless defined($name);

    $byte_limits = get_byte_limits();

    my $policy = make_policy($name);

    # This error now caught and reported by yang
    exit 0 unless defined($policy);

    my $tag = 0;
    if ( $vif != 0 ) {
        $tag = $config->returnValue("vif $vif vlan");
        $tag = $vif unless defined($tag);
    }

    $policy->valid();

    my $router = 1;
    if ( $tag == 0 and $config->exists("switch-group") ) {
        $router = 0;
    }
    $policy->init( $ifname, $router );
    $policy->valid_binding( $intf, $vif, $tag );
    validate_global_profiles();

    exit 0;
}

sub usage {
    print <<EOF;
usage: qos-validate --validate policy-name
       qos-validate --validate-binding interface-name vif-number
       qos-validate --dscp dscp-value
       qos-validate --list-profiles policy-name
EOF
    exit 1;
}

my ( $validatePolicy, @validateBinding );
my ( $dscpCheck,      $listProfiles );

GetOptions(
    "validate"              => \$validatePolicy,
    "validate-binding=s{2}" => \@validateBinding,
    "dscp=s"                => \$dscpCheck,
    "list-profiles=s"       => \$listProfiles,
) or usage();

validate_policy()                  if $validatePolicy;
validate_binding(@validateBinding) if @validateBinding;
dscp_check($dscpCheck)             if $dscpCheck;
list_profiles($listProfiles)       if $listProfiles;
