# Module QoS::Profile.pm
#
# Copyright (c) 2017-2019, AT&T Intellectual Property.
# All Rights Reserved.
# Copyright (c) 2013-2017, Brocade Communications Systems, Inc.
# All Rights Reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

package Vyatta::QoS::Profile;
use strict;
use warnings;

use Carp;
use Vyatta::Config;

use Vyatta::DSCP qw(dscp_range str2dscp);
use Vyatta::QoS::Bandwidth;
use Vyatta::QoS::TrafficClass;
use Vyatta::QoS::Queue;
use Vyatta::QoS::Debug qw(invalid notify);

use constant {
    MAX_QUEUE     => 31,
    MAX_DSCP      => 63,
    MAX_PCP       => 7,
    MAX_WRR_QUEUE => 7,
    TC_WRR_BITS   => 5,
};

our $PERIOD_DEFAULT = 10;

# Create new class based on Vyatta Config
# pass $level to indicate where to find values
sub new {
    my ( $class, $level, $bw, $subport_tc ) = @_;
    my $config = new Vyatta::Config($level);
    my $self   = {};
    bless $self, $class;

    $self->{name} = $1 if ( $level =~ m/([-\w]+)$/ );

    if ( $config->exists('period') ) {
        $self->{period}            = $config->returnValue('period');
        $self->{period_is_default} = $config->isDefault('period');
    } else {
        $self->{period}            = $PERIOD_DEFAULT;
        $self->{period_is_default} = 1;
    }

    $self->{bandwidth} = new Vyatta::QoS::Bandwidth( $level, $bw );
    $self->{tc} = new Vyatta::QoS::TrafficClass( "$level traffic-class",
        $self->{bandwidth} );

    $self->{map_in_use} = whichMapInUse($level);
    $self->{queue}      = getQueues( $level, $subport_tc );
    $self->{dscp_group} = getDscpGroupMap( $level, $self->{queue} );
    $self->{dscp}       = getDscpMap( $level, $self->{queue} );
    $self->{pcp}        = getPcpMap( $level, $self->{queue} );

    return $self;
}

sub whichMapInUse {
    my $level        = shift;
    my $config       = new Vyatta::Config($level);
    my $dscpgroupmap = $config->listNodes('map dscp-group');
    my $dscpmap      = $config->listNodes('map dscp');
    my $pcpmap       = $config->listNodes('map pcp');

    if ( $dscpmap and $pcpmap ) {
        notify 'Cannot configure PCP and DSCP maps together, ignoring PCP map';
        $pcpmap = undef;
    }

    return 'dscp-group' if $dscpgroupmap;
    return 'dscp'       if $dscpmap;
    return 'pcp'        if $pcpmap;
    return;
}

# make ref to array of DSCP to queue mappings
sub getDscpGroupMap {
    my ( $level, $queues ) = @_;
    $level .= ' map dscp-group';
    my $config = new Vyatta::Config($level);
    my @dscp2q;
    my $index = 0;

    # process overrides
    foreach my $name ( $config->listNodes() ) {
        my $qid = $config->returnValue("$name to");
        invalid "Queue id missing at $level $name"
          unless defined($qid);

        # The dataplane sets up a default map so we only need
        # send those which are configured to non default queues
        if ( defined $queues->[$qid] ) {
            my $q  = $queues->[$qid];
            my $dp = $q->getdp($name);
            $dscp2q[$index] = " $name ";
            $dscp2q[$index++] .= $q->qmap() | ( $dp << TC_WRR_BITS );
        }
    }

    return \@dscp2q;
}

# make ref to array of DSCP to queue mappings
sub getDscpMap {
    my ( $level, $queues ) = @_;
    $level .= ' map dscp';
    my $config = new Vyatta::Config($level);
    my @dscp2q;

    # process overrides
    foreach my $str ( $config->listNodes() ) {
        my $qid = $config->returnValue("$str to");
        invalid "Queue id missing at $level $str"
          unless defined($qid);

        my @ret = dscp_range($str);
        invalid "Invalid DSCP '$str'"
          unless ( $#ret >= 0 );

        # The dataplane sets up a default map so we only
        # need send those values assigned to different queues
        foreach my $dscp (@ret) {
            next unless defined $queues->[$qid];
            my $q = $queues->[$qid];
            $dscp2q[$dscp] = $q->qmap();
        }
    }

    return \@dscp2q;
}

# make ref to array of PCP to queue mappings
sub getPcpMap {
    my ( $level, $queues ) = @_;
    $level .= ' map pcp';
    my $config = new Vyatta::Config($level);
    my @pcp2q;

    # default PCP to queue mapping
    # 0 == best effort => traffic-class 3
    # 7 == high priority =>             0
    # Need indexes into the queue array, not TC/Q combo
    for my $pcp ( 0 .. MAX_PCP ) {
        my $tc = ( ~$pcp >> 1 ) & 3;
        $pcp2q[$pcp] = $tc;
    }

    foreach my $pcp ( $config->listNodes() ) {
        invalid "Invalid pcp value $pcp"
          unless ( $pcp >= 0 && $pcp <= 7 );

        my $qid = $config->returnValue("$pcp to");
        invalid "Queue id missing at $level $pcp"
          unless defined($qid);

        if ( defined( $queues->[$qid] ) ) {
            my $q = $queues->[$qid];
            $pcp2q[$pcp] = $q->qmap();
        }
    }

    return \@pcp2q;
}

sub createQueue {
    my ( $level, $config, $id, $qpertc, $queues, $subport_tc, $is_local ) = @_;
    my $tc;
    my $qindex;
    my $w;

    $tc = $config->returnValue("queue $id traffic-class");

    invalid "traffic-class (priority) not set for queue $id"
      unless ( defined($tc) );

    $w = $config->returnValue("queue $id weight");

    # Assign WRR queue per priority level
    $qindex = $$qpertc[$tc]++;
    invalid "too many queues using traffic-class (priority) $tc\n"
      if ( $qindex > MAX_WRR_QUEUE );

    # Don't use qindex 0 for the local queue so it is always
    # separate from default.
    if ( $is_local && $qindex eq 0 ) {
        $qindex++;
    }

    $$queues[$id] =
      new Vyatta::QoS::Queue( $level, $tc, $qindex, $is_local, $w, $id,
        $subport_tc->[$tc] );
}

# make ref to array of queues
sub getQueues {
    my $level      = shift;
    my $subport_tc = shift;
    my $config     = new Vyatta::Config($level);
    my @queues;
    my @qpertc = (0) x 4;
    my $local_q;

    for my $id ( 0 .. MAX_QUEUE ) {
        if ( $config->exists("queue $id") ) {

            # If the local priority queue exists, assign it last
            # so it can be kept away from default config.
            if ( $config->exists("queue $id priority-local") ) {
                $local_q = $id;
                next;
            }
            createQueue( $level, $config, $id, \@qpertc, \@queues,
                $subport_tc, 0 );
        }
    }

    if ( defined($local_q) ) {
        createQueue( $level, $config, $local_q, \@qpertc, \@queues,
            $subport_tc, 1 );
    }

    return \@queues;
}

sub _map_commands {
    my ( $self, $name, $mapref, $prefix ) = @_;
    my @map = @{$mapref};
    my @cmds;

    for my $value ( 0 .. $#map ) {
        my $q = $map[$value];
        next unless defined($q);

        my $cmd = sprintf ' %s %u 0x%x', $name, $value, $q;
        push @cmds, $prefix . $cmd;
    }

    return @cmds;
}

sub _grp_map_commands {
    my ( $self, $name, $mapref, $prefix ) = @_;
    my @map = @{$mapref};
    my @cmds;

    for my $value ( 0 .. $#map ) {
        my $q = $map[$value];
        next unless defined($q);

        my $cmd = sprintf ' %s %s', $name, $q;
        push @cmds, $prefix . $cmd;
    }

    return @cmds;
}

# generate parameters for profile
sub commands {
    my ( $self, $prefix ) = @_;
    my @cmds;

    # command for setting bandwidth of this profile
    my $bw  = $self->{bandwidth};
    my $cmd = $bw->command($prefix);

    my $period = $self->{period};
    $cmd .= " period $period" if defined($period);
    push @cmds, $cmd;

    # Traffic class rates
    my $tc = $self->{tc};
    push @cmds, $tc->commands($prefix);

    my $queues = $self->{queue};

    if ( defined $self->{map_in_use} ) {
        if ( $self->{map_in_use} eq 'pcp' ) {
            push @cmds, $self->_map_commands( 'pcp', $self->{pcp}, $prefix );
        }

        if ( $self->{map_in_use} eq 'dscp' ) {
            push @cmds, $self->_map_commands( 'dscp', $self->{dscp}, $prefix );
        }

        if ( $self->{map_in_use} eq 'dscp-group' ) {
            push @cmds,
              $self->_grp_map_commands( 'dscp-group', $self->{dscp_group},
                $prefix );
        }
    }

    # WRR weights and local priority queue
    for my $id ( 0 .. $#$queues ) {
        my $suffix = "";
        my $q      = $queues->[$id];
        next unless keys %{$q};

        # Is there a priority queue for local traffic?
        if ( $q->local() eq 1 ) {
            $suffix = " prio-loc";
        }
        $cmd = sprintf ' queue %#x wrr-weight %u %u', $q->qmap(), $q->wrr(),
          $q->conf_id();
        push @cmds, $prefix . $cmd . $suffix;

        if ( !defined( $q->{wred_map} ) or !defined( $q->{wred_weight} ) ) {
            next;
        }
        my $units;
        if ($main::byte_limits) {
            $units = "bytes";
        } else {
            $units = "packets";
        }
        foreach my $map ( @{ $q->{wred_map} } ) {
            $cmd = sprintf ' queue %#x dscp-group %s %s %u %u %u',
              $q->qmap(), $map->{rsrc_grp}, $units,
              $map->{qmax}, $map->{qmin}, $map->{prob};
            push @cmds, $prefix . $cmd;
        }
        if ( defined( $q->{wred_weight} ) ) {
            $cmd = sprintf ' queue %#x wred-weight %u',
              $q->qmap(), $q->{wred_weight};
            push @cmds, $prefix . $cmd;
        }
    }

    return @cmds;
}

sub valid_binding {
    my ( $self, $intf, $overhead ) = @_;
    my $min_pkt_len = $intf->mtu() + $overhead;

    $self->{bandwidth}->valid_binding( $min_pkt_len, $intf->name() );

    $self->{tc}->valid_binding(
        $min_pkt_len, $self->{period},
        $self->{period_is_default},
        "profile $self->{name}"
    );

    return 1;
}

1;
