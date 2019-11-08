# Module QoS::Debug.pm
#
# Copyright (c) 2019 AT&T Intellectual Property. All Rights Reserved.
# Copyright (c) 2015, Brocade Communications Systems, Inc.
# All Rights Reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

package Vyatta::QoS::Debug;

use strict;
use warnings;
use Carp;
use Exporter;

use vars qw( @ISA @EXPORT @EXPORT_OK $VERSION ) ;
@ISA = qw( Exporter ) ;

@EXPORT = qw(invalid);
@EXPORT_OK = qw(notify);
$VERSION = 1.00;

my $debug = $ENV{'QOS_DEBUG'};

sub invalid {
    my ($text) = @_;

    if ($debug) {
        confess($text);
    } else {
        die("$text\n");
    }
}

sub notify {
    my ($text) = @_;

    if ($debug) {
        carp($text);
    } else {
        warn("$text\n");
    }
}

1;
