#! /usr/bin/perl
#
# Copyright (c) 2019, AT&T Intellectual Property. All rights reserved.
#

use strict;
use warnings;

use lib '/opt/vyatta/share/perl5';

use Vyatta::Config;
use Vyatta::Configd;
use Vyatta::FWHelper qw(build_rule);

# $policy_name as in 'set policy qos name $policy_name shaper'
# $class_id = 1..255

sub call_npf_build_rule {
    my ( $policy_name, $class_id, $rule_id ) = @_;

    my $level  = "policy qos name $policy_name shaper class $class_id";
    my $config = new Vyatta::Config($level);
    my $rule   = "";

    $rule = build_rule( "$level match $rule_id", $class_id )
      if ( !$config->exists("match $rule_id disable") );

    return $rule;
}

my ( $policy_name, $class_id, $rule_id ) = @ARGV;

if ( defined $policy_name and defined $class_id and defined $rule_id ) {
    my $client = Vyatta::Configd::Client->new();

    $client->session_setup("$$");
    $ENV{'VYATTA_CONFIG_SID'} = "$$";
    print call_npf_build_rule( $policy_name, $class_id, $rule_id );
    $client->session_teardown();
    exit 0;
} else {
    print "rule.pm missing arguments\n";
    exit 1;
}
