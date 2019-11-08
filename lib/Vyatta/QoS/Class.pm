# Module QoS::Class.pm
#
# Copyright (c) 2019 AT&T Intellectual Property. All Rights Reserved.
# Copyright (c) 2013-2015, Brocade Communications Systems, Inc.
# All Rights Reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

package Vyatta::QoS::Class;
use strict;
use warnings;

use Carp;
use Vyatta::Config;
use Vyatta::FWHelper qw(build_rule);

# Create new class based on Vyatta Config
# pass $level to indicate where to find values
sub new {
    my ( $class, $level, $id ) = @_;
    $level .= " class $id";
    my $config = new Vyatta::Config($level);
    my $self   = {};

    $self->{profile} = $config->returnValue('profile');

    my @rules;
    foreach my $match ( $config->listNodes('match') ) {
        push @rules, build_rule( "$level match $match", $id )
          if ( !$config->exists("match $match disable") );
    }
    $self->{rules} = \@rules;
    bless $self, $class;

    return $self;
}

# return profile name for this class
sub profile {
    my $self = shift;

    return $self->{profile};
}

# return command suffix list
sub rules {
    my $self = shift;

    return @{ $self->{rules} };
}

1;
