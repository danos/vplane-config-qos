#! /usr/bin/perl

# Copyright (c) 2017-2019, AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2013-2017, Brocade Communications Systems, Inc.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

use strict;
use warnings;

use Getopt::Long;
use Config::Tiny;
use Term::Cap;
use JSON qw( decode_json );

use lib "/opt/vyatta/share/perl5/";
use Vyatta::Dataplane;
use Vyatta::Interface;
use Vyatta::Config;
use Vyatta::QoS::Profile;

use constant MAX_DSCP => Vyatta::QoS::Profile::MAX_DSCP;
use constant TC_SHIFT => 2;
use constant TC_MASK  => 0x3;

#
# The following global variable controls whether we're accessing and displaying
# 32-bit or 64-bit counters
#
my $bits64 = 0;

sub split_ifname {
    my $ifname = shift;    # dp0p2p1.N

    # QoS not directly allowed on VRRP interface
    die "QoS not available on VRRP pseudo interface\n"
      if ( $ifname =~ /v\d+$/ );

    # Split name and vif
    if ( $ifname =~ /^(.*)\.(\d+)$/ ) {
        return $1, $2;
    } else {
        return $ifname;
    }
}

# Fetch queuing information on a specific interface
# Parse resulting JSON output
#  only returns portion for this interface (or undef)
sub get_interface {
    my $ifname = shift;
    my $cmd    = shift;

    die "Interface $ifname does not exist\n"
      unless ( -d "/sys/class/net/$ifname" );

    my $intf = new Vyatta::Interface($ifname);
    die "$ifname is not a dataplane interface\n"
      unless ( $intf->type() eq 'dataplane'
        or $intf->type() eq 'uplink'
        or $intf->type() eq 'bonding'
        or $intf->type() eq 'vhost' );

    my $fabric = $intf->dpid();

    my ( $dpids, $dpsocks ) = Vyatta::Dataplane::setup_fabric_conns($fabric);
    die "Dataplane $fabric is not connected or does not exist\n"
      unless ( scalar(@$dpids) > 0 );

    my $sock = ${$dpsocks}[$fabric];
    die "Can not connect to dataplane $fabric\n"
      unless $sock;

    my $response = $sock->execute("$cmd $ifname");
    exit 1 unless defined($response);

    my $decoded = decode_json($response);
    return $decoded->{$ifname};
}

# For a particular interface name (trunk or subinterface) interogate the
# current config and return the QoS policy name associated with the interface
sub get_if_subport_policy_name {
    my $if_name = shift;
    my $trunk_name;
    my $vlan_id;

    if ( $if_name =~ /^(.*)\.(\d+)$/ ) {
        $trunk_name = $1;
        $if_name    = "$1 vif $2";
        $vlan_id    = $2;
    }

    my $config = new Vyatta::Config();
    my $intf   = new Vyatta::Interface($if_name);

    $config->setLevel( $intf->path . " policy qos" );
    my $policy_name = $config->returnOrigValue();
    return $policy_name if defined($policy_name);

    # SIAD has added new attach points for QoS policies
    if ( !defined($vlan_id) ) {

        # Non-vlan attach points
        $config->setLevel(
            $intf->path . " switch-group port-parameters policy qos" );
        $policy_name = $config->returnOrigValue();
        return $policy_name if defined($policy_name);

        $config->setLevel( $intf->path . " switch-group switch" );
        my $switch = $config->returnOrigValue();
        return undef if !defined($switch);

        $config->setLevel(
            "interface switch $switch default-port-parameters policy qos");
        $policy_name = $config->returnOrigValue();
        return $policy_name if defined($policy_name);
    } else {

        # Vlan attach-points
        my $intf = new Vyatta::Interface($trunk_name);

        $config->setLevel( $intf->path
              . " switch-group port-parameters vlan-parameters qos-parameters vlan $vlan_id policy qos"
        );
        $policy_name = $config->returnOrigValue();
        return $policy_name if defined($policy_name);

        $config->setLevel( $intf->path . " switch-group switch" );
        my $switch = $config->returnOrigValue();
        return undef if !defined($switch);

        $config->setLevel(
"interfaces switch $switch default-port-parameters vlan-parameters qos-parameters vlan $vlan_id policy qos"
        );
        $policy_name = $config->returnOrigValue();
        return $policy_name if defined($policy_name);
    }
    return undef;
}

# figure out which vlan tag is matchd with subport
sub find_vif {
    my ( $info, $vif ) = @_;

    for my $v ( @{ $info->{vlans} } ) {

        # $v = [ { 'tag' => 10, 'subport' => 1, } ]

        return $v->{subport}
          if ( $v->{tag} eq $vif );
    }
    return;    # undef
}

# figure out vlan for a subport
sub subport_vlan {
    my ( $info, $id ) = @_;

    for my $v ( @{ $info->{vlans} } ) {

        # $v = [ { 'tag' => 10, 'subport' => 1, } ]

        return $v->{tag}
          if ( $v->{subport} eq $id );
    }
    return;    #undef
}

sub show {
    my $name = shift;
    my ( $port, $vif ) = split_ifname($name);
    my $data = get_interface( $port, "qos show " );

    # Skip interfaces with no QoS
    return unless defined($data);

    # Only know about shaper
    my $shaper = $data->{shaper};
    return unless defined($shaper);

    my $policy_name = get_if_subport_policy_name($name);
    return unless defined($policy_name);

    show_shaper( $shaper, $vif, $policy_name, 0 );
}

sub show_shaper {
    my ( $info, $vif, $policy_name, $brief ) = @_;
    my $subports = $info->{subports};

    if ( defined($vif) ) {
        my $id = find_vif( $info, $vif );

        if ( defined($id) ) {
            show_subport( $subports->[$id], $policy_name, $brief );
            return;
        }

        # If no QoS policy defined for vif then treated as untagged.
    }

    # first result is untagged subport
    show_subport( $subports->[0], $policy_name, $brief );
}

sub show_shaper_tc {
    my ( $fmt, $pfx, $subport, $old ) = @_;
    my $prev;
    $prev = $old->{tc} if defined($old);

    my $data = $subport->{tc};
    return unless defined($data);

    my @stat = @{$data};

    for my $tc ( 0 .. $#stat ) {
        my $packets = $stat[$tc]->{packets};
        my $bytes   = $stat[$tc]->{bytes};

        # the dropped counter counts total-drops, but we display it as
        # tail-drops, so some subtraction is required
        my $red  = $stat[$tc]->{random_drop};
        my $tail = $stat[$tc]->{dropped} - $red;

        # If there are loads of RED drops, a few may occur between
        # reading the total drop counter and the RED drop counter,
        # causing the tail drop to appear negative.
        if ( $tail < 0 ) {
            $tail = 0;
        }

        # used by monitor command where want to show incremental changes
        if ($prev) {
            my $tailorig = $tail;

            $packets -= $prev->[$tc]->{packets};
            $bytes   -= $prev->[$tc]->{bytes};

            # subtract red-drops from total-drops to get tail-drops
            $red  -= $prev->[$tc]->{random_drop};
            $tail -= ( $prev->[$tc]->{dropped} - $prev->[$tc]->{random_drop} );

            # when QoS config change, these counters get reset to zero, so
            # rather than display negative numbers, just use the most recent
            # values directly
            $packets = $stat[$tc]->{packets}     if ( $packets < 0 );
            $bytes   = $stat[$tc]->{bytes}       if ( $bytes < 0 );
            $red     = $stat[$tc]->{random_drop} if ( $red < 0 );
            $tail    = $tailorig                 if ( $tail < 0 );
        }

        if ($bits64) {
            printf $fmt, $pfx, $tc, $bytes, "Bytes";
            $pfx = '';
            $tc  = '';
            printf $fmt, $pfx, $tc, $packets, "Packets";
            printf $fmt, $pfx, $tc, $tail,    "Tail-drop";
            printf $fmt, $pfx, $tc, $red,     "RED-drop";
        } else {
            printf $fmt, $pfx, $tc, $packets, $bytes, $tail, $red;
            $pfx = '';
        }
    }
}

# Sum the results for all the WRR queues in the traffic class
sub sum_tc {
    my $stats = shift;
    my $out   = [];

    foreach my $i ( 0 .. $#$stats ) {
        my $tc  = $stats->[$i];
        my $sum = {};

        foreach my $j ( 0 .. $#$tc ) {
            my $q = $tc->[$j];

            next unless defined($q);

            while ( my ( $key, $value ) = each %{$q} ) {
                if ( defined( $sum->{$key} ) ) {
                    $sum->{$key} += $value;
                } else {
                    $sum->{$key} = $value;
                }

            }
        }
        $out->[$i] = $sum;
    }

    return $out;
}

sub show_subport {
    my ( $subport, $policy_name, $brief ) = @_;
    my $pipes = $subport->{pipes};
    return unless defined($pipes);

    my $fmt;
    my $l;

    if ($bits64) {
        $fmt = "%-5s %2s %3s %8s %8s %-7s %3s %20s %-9s\n";
        $l = sprintf $fmt, 'Class', 'TC', 'WRR', 'Pipe-QID', 'Qlength', '',
          'PLQ',
          'Counters', '';
    } else {
        $fmt = "%-8s %4s %4s %7s %10s %16s %9s %9s %3s\n";
        $l = sprintf $fmt, 'Class', 'Prio', 'WRR', 'Qlength',
          'Packets', 'Bytes', 'Tail-drop', 'RED-drop', 'PLQ';
    }
    print $l, '-' x length($l), "\n";

    for my $class ( 0 .. $#$pipes ) {
        my $policy_config = new Vyatta::Config("policy qos name $policy_name");
        my $profile_name;

        if ( $class == 0 ) {
            $profile_name = $policy_config->returnOrigValue("shaper default");
        } else {
            $profile_name =
              $policy_config->returnOrigValue("shaper class $class profile");
        }
        next if ( !defined($profile_name) );

        my $info = $pipes->[$class]->{tc};

        for my $tc ( 0 .. $#$info ) {
            my $tinfo = $info->[$tc];
            my $tpfx  = $tc;

            for my $q ( 0 .. $#$tinfo ) {
                my $stat = $tinfo->[$q];

                # the dropped counter counts total-drops, we display it as
                # tail-drops, so some subtraction is required
                my $tail = $stat->{dropped} - $stat->{random_drop};

                if ( $tail < 0 ) {
                    $tail = 0;
                }

                if ($bits64) {
                    #
                    # How do we determine of the length of the queue is
                    # measured in packets (dpdk) or bytes (qumran)?
                    # The dataplane knows and either returns "qlen" or
                    # "qlen-bytes"
                    #
                    my $qlen_units;
                    my $qlen_value;

                    if ( defined $stat->{qlen} ) {
                        $qlen_value = $stat->{qlen};
                        $qlen_units = "packets";
                    } else {
                        $qlen_value = $stat->{'qlen-bytes'};
                        $qlen_units = "bytes";
                    }

                    my $cfgid;
                    if ( !defined( $stat->{cfgid} ) ) {
                        $cfgid = '';
                    } else {
                        $cfgid = sprintf "%s", $stat->{cfgid};
                    }

                    printf $fmt,
                      ( $tc == 0 && $q == 0 ) ? $class : '',
                      ( $q == 0 ) ? $tc : '', $q, $cfgid, $qlen_value,
                      $qlen_units, ( $stat->{prio_local} == 1 ) ? '*' : '',
                      $stat->{bytes}, 'bytes';
                    printf $fmt, '', '', '', '', '', '', '', $stat->{packets},
                      'packets';
                    printf $fmt, '', '', '', '', '', '', '', $tail, 'Tail-drop';
                    printf $fmt, '', '', '', '', '', '', '',
                      $stat->{random_drop},
                      'RED-drop';
                    if ( $brief == 1 && defined( $stat->{wred_map} ) ) {
                        my $lay = "%8s %10s %-20s %20s RED-drop\n";
                        for my $i ( 0 .. 3 ) {
                            my $maps;

                            if ( defined( $stat->{wred_map}[$i] ) ) {
                                if ( $i == 0 ) {
                                    $maps = "Wred Maps:";
                                } else {
                                    $maps = '';
                                }
                                printf $lay, " ", $maps,
                                  $stat->{wred_map}[$i]->{res_grp},
                                  $stat->{wred_map}[$i]->{random_dscp_drop};
                            }
                        }
                        next;
                    }
                } else {
                    if ( not defined( $stat->{qlen} ) ) {
                        $stat->{qlen} = $stat->{'qlen-bytes'};
                    }
                    printf $fmt,
                      ( $tc == 0 && $q == 0 ) ? $class : '',
                      ( $q == 0 ) ? $tc : '', $q,
                      $stat->{qlen}, $stat->{packets}, $stat->{bytes}, $tail,
                      $stat->{random_drop},
                      ( $stat->{prio_local} == 1 ) ? '*' : '';
                    if ( $brief == 1 && defined( $stat->{wred_map} ) ) {
                        printf "%35.s %s\n", " ", "Wred Maps :";
                        my $lay = "%38.s group %-10s    drops %9s\n";
                        for my $i ( 0 .. 3 ) {
                            if ( defined( $stat->{wred_map}[$i] ) ) {
                                printf $lay, " ",
                                  $stat->{wred_map}[$i]->{res_grp},
                                  $stat->{wred_map}[$i]->{random_dscp_drop};
                            }
                        }
                        next;
                    }
                }
            }
        }
    }
}

sub show_summary_header {
    my ($fmt) = @_;

    my $l = sprintf $fmt, 'Interface', 'Prio', 'Packets', 'Bytes',
      'Tail-drop', 'RED-drop';
    print $l, '-' x length($l), "\n";
}

sub show_summary_header64 {
    my ($fmt) = @_;

    my $l = sprintf $fmt, 'Interface', 'TC', 'Counters', '        ';
    print $l, '-' x length($l), "\n";
}

# Walk through each interface
sub walk_interfaces {
    my $func       = shift;
    my $interfaces = shift;

    # Sort the interfaces alphabetically by name
    foreach my $ifname ( sort( keys %{$interfaces} ) ) {
        my $data = %{$interfaces}{$ifname};

        # For now only have 'shaper' => ...
        while ( my ( $policy, $value ) = each %{$data} ) {
            if ( $policy ne 'shaper' ) {
                warn "$ifname: unknown policy $policy\n";
                next;
            }
            $func->( @_, $ifname, $value );
        }
    }
}

# Walk through all fabrics
sub walk_fabrics {
    my $show_cmd = shift;
    my $func     = shift;

    my ( $dpids, $dpsocks ) = Vyatta::Dataplane::setup_fabric_conns();

    for my $fid ( @{$dpids} ) {
        my $sock = ${$dpsocks}[$fid];
        unless ($sock) {
            warn "Can not connect to dataplane $fid\n";
            next;
        }

        my $response = $sock->execute("$show_cmd");
        next unless defined($response);

        my $decoded = decode_json($response);
        $func->( $decoded, @_ );
    }
}

# Walk through subports
sub walk_subports {
    my ( $func, $fmt, $ifname, $info, $old ) = @_;
    my @subports = @{ $info->{subports} };

    foreach my $i ( 0 .. $#subports ) {
        my $qname = $ifname;
        if ( $i > 0 ) {
            my $vif = subport_vlan( $info, $i );
            next unless $vif;

            $qname = $ifname . '.' . $vif;
        }
        $func->( $fmt, $qname, $subports[$i], $old->{subports}->[$i] );
    }
}

sub show_bcm_subport {
    my ( $fmt, $pfx, $subport ) = @_;
    my $bcm_info = $subport->{'fal-bcm-qossub'};
    return unless defined($bcm_info);

    printf $fmt, $pfx, $bcm_info->{'voq-id'}, $bcm_info->{'voq-conn-id'};
}

sub show_bcm_port {
    walk_subports( \&show_bcm_subport, @_ );
}

sub show_bcm_summary {
    my ( $decoded, $fmt ) = @_;
    my $intf = each %{$decoded};
    return unless defined($intf);

    my $data     = %{$decoded}{$intf};
    my $shaper   = $data->{shaper};
    my $subport  = $shaper->{subports}->[0];
    my $bcm_info = $subport->{'fal-bcm-qossub'};

    if ( defined($bcm_info) ) {
        print "\nTC/WRR -> BCM TC\n";
        for my $tc ( 0 .. 7 ) {
            if ( defined( $bcm_info->{'q2tc'}->[$tc] ) ) {
                my $q2tc = $bcm_info->{'q2tc'}->[$tc];

                if ( $q2tc->{'priority-local'} ) {
                    printf " PLQ   -> %6d\n", $q2tc->{'bcm-tc'};
                } else {
                    printf "%2d/%d   -> %6d\n",
                      $q2tc->{'pipe-q-tc'},
                      $q2tc->{'pipe-q-wrr'},
                      $q2tc->{'bcm-tc'};
                }
            }
        }

        print "\nPort[.Vlan]  VOQ/QID  VOQ Conn/FlowID\n";
        walk_interfaces( \&show_bcm_port, $decoded, $fmt );
    }
}

sub show_bcm_buffer_errors {
    my ( $decoded, $fmt ) = @_;
    my $buf_num;
    my $buf_errs;
    my $buf_del;
    return unless defined($decoded);
    my $memerrs = %{$decoded}{'fal-bcm-memerr'};
    return unless defined( $memerrs->{buf} );

    foreach ( @{ $memerrs->{buf} } ) {
        $buf_num  = $_->{'buf-num'};
        $buf_errs = $_->{'buf-errs'};
        if ( $_->{'buf-del'} ) {
            $buf_del = "yes";
        } else {
            $buf_del = "no";
        }
        printf $fmt, $buf_num, $buf_errs, $buf_del;
    }
}

sub show_platform_info {
    my $fmt = "%-11s %8d %16d\n";

    walk_fabrics( "qos show platform", \&show_bcm_summary, $fmt );
}

sub show_buffer_errors {
    my $fmt = "%-12s %6s %16s\n";
    my $hdr = sprintf $fmt, 'Buffer #', 'Errors', 'Quarantined';
    print $hdr, '-' x length($hdr), "\n";

    walk_fabrics( "qos show buffer-errors", \&show_bcm_buffer_errors, $fmt );
}

# Show shapers on all interfaces
sub show_interface_queues {
    walk_interfaces( \&show_shaper_queues, @_ );
}

# show summary of interfaces
sub show_summary {
    my $fmt;

    if ($bits64) {
        $fmt = "%-16s %4s %20s %-9s\n";
        show_summary_header64($fmt);
    } else {
        $fmt = "%-16s %4s %10s %16s %10s %10s\n";
        show_summary_header($fmt);
    }
    walk_fabrics( "qos show", \&show_interface_queues, $fmt );

    exit 0;
}

# from Perl Cookbook
sub get_cls {
    my $OSPEED = 9600;
    eval {
        require POSIX;
        my $termios = POSIX::Termios->new();
        $termios->getattr;
        $OSPEED = $termios->getospeed;
    };
    my $terminal = Term::Cap->Tgetent( { OSPEED => $OSPEED } );

    return $terminal->Tputs('cl');
}

# monitor mode, like brief but repeat output
sub show_monitor {
    my $fmt;

    if ($bits64) {
        $fmt = "%-16s %4s %20s %-9s\n";
    } else {
        $fmt = "%-16s %6s %10s %16s %10s %10s\n";
    }

    # make socket to each dataplane
    my ( $dpids, $dpsocks ) = Vyatta::Dataplane::setup_fabric_conns();

    my %prev;
    my $clear = get_cls();
    while (1) {
        print $clear;
        if ($bits64) {
            show_summary_header64($fmt);
        } else {
            show_summary_header($fmt);
        }

        for my $fid ( @{$dpids} ) {
            my $sock = ${$dpsocks}[$fid];
            unless ($sock) {
                warn "Can not connect to dataplane $fid\n";
                next;
            }

            my $response = $sock->execute("qos show");
            next unless defined($response);

            my $decoded = decode_json($response);
            foreach my $ifname ( sort( keys %{$decoded} ) ) {
                my $data = %{$decoded}{$ifname};

                # For now only have 'shaper' => ...
                my $stats = $data->{shaper};
                next unless $stats;

                show_shaper_queues( $fmt, $ifname, $stats, $prev{$ifname} );
                $prev{$ifname} = $stats;
            }
        }

        STDOUT->flush();
        sleep(1);
    }
}

sub show_bcm_platform_map {
    my $subport     = shift;
    my $pipe        = $subport->{pipes}->[0];
    my $platdscpmap = $pipe->{'fal-bcm-qos-dscpmap'};
    my $platpcpmap  = $pipe->{'fal-bcm-qos-pcpmap'};

    if ( defined($platdscpmap) ) {
        print "\nDSCP->PipeQ->TC/DP    DSCP->PipeQ->TC/DP";
        print "    DSCP->PipeQ->TC/DP\n";

        # Print output in columns for readability
        for my $i ( 0 .. MAX_DSCP ) {
            my $dscp;
            my $dscp_map_entry;

            if ( $i eq MAX_DSCP ) {
                $dscp = $i;
            } else {
                $dscp = ( $i % 3 ) * 21 + ( $i / 3 );
            }

            if ( $dscp eq MAX_DSCP ) {
                print "                                            ";
            }

            $dscp_map_entry = $platdscpmap->[$dscp];

            printf " %2d -> %d/%d -> %d/%d",
              $dscp,
              $dscp_map_entry->{'pipe-q-tc'},
              $dscp_map_entry->{'pipe-q-wrr'},
              $dscp_map_entry->{'bcm-tc'},
              $dscp_map_entry->{'dp'};

            if ( ( $i + 1 ) % 3 ) {
                print "     ";
            } else {
                print "\n";
            }
        }
    }

    if ( defined($platpcpmap) ) {
        if ( defined($platdscpmap) ) {
            print "\n";
        }
        print "\nDSCP->PCP  DSCP->PCP  DSCP->PCP  DSCP->PCP";
        print "  DSCP->PCP  DSCP->PCP  DSCP->PCP\n";
        for my $i ( 0 .. MAX_DSCP ) {
            my $dscp;
            my $pcp_map_entry;

            if ( $i eq MAX_DSCP ) {
                $dscp = $i;
                printf( "%66s", " " );
            } else {
                $dscp = ( $i % 7 ) * 9 + ( $i / 7 );
            }
            $pcp_map_entry = $platpcpmap->[$dscp];
            printf " %2d -> %d", $dscp, $pcp_map_entry->{'pcp'};
            if ( ( $i % 7 ) == 6 ) {
                print "\n";
            } else {
                print "   ";
            }
        }
    }
}

sub show_platform_map {
    my $ifname = shift;
    my ( $port, $vif ) = split_ifname($ifname);
    my $data = get_interface( $port, "qos show platform" );

    # Skip interfaces with no QoS
    return unless defined($data);

    my $shaper = $data->{shaper};
    return unless defined($shaper);

    show_bcm_platform_map( $shaper->{subports}->[0] );
}

# show DSCP map for interface
sub show_dscp {
    my $ifname = shift;
    my ( $port, $vif ) = split_ifname($ifname);
    my $data = get_interface( $port, "qos show " );

    # Skip interfaces with no QoS
    return unless defined($data);

    my $shaper = $data->{shaper};
    return unless defined($shaper);

    if ( defined($vif) ) {
        my $id = find_vif( $shaper, $vif );

        if ( defined($id) ) {
            show_shaper_dscp( $shaper->{subports}->[$id] );
            return;
        }

        # If no QoS policy defined for vif then treated as untagged.
    }
    show_shaper_dscp( $shaper->{subports}->[0] );
}

# show queueing brief for an interface
sub show_brief {
    my $ifname = shift;
    my ( $port, $vif ) = split_ifname($ifname);
    my $data = get_interface( $port, "qos optimised-show " );

    # Skip interfaces with no QoS
    return unless defined($data);

    # Only know about shaper
    my $shaper = $data->{shaper};
    return unless defined($shaper);

    my $policy_name = get_if_subport_policy_name($ifname);
    return unless defined($policy_name);

    show_shaper( $shaper, $vif, $policy_name, 1 );
}

sub show_shaper_dscp {
    my $subport = shift;
    my @pipes   = @{ $subport->{pipes} };

    for my $cid ( 0 .. $#pipes ) {
        my $pipe   = $pipes[$cid];
        my $dscp2q = $pipe->{dscp2q};

        my $cname = ( $cid == 0 ) ? "default" : "class $cid";
        print "DSCP->TC:WRR map for $cname: (dscp=d1d2)\n\n";
        print "     d2 |    0    1    2    3    4    5    6    7    8    9\n";
        print "  d1    |\n";
        print "  ------+---------------------------------------------------\n";

        for my $d2 ( 0 .. 6 ) {
            printf "     %u  |", $d2;
            for my $d1 ( 0 .. 9 ) {
                my $dscp = $d2 * 10 + $d1;
                last if $dscp >= 64;

                my $qm = $dscp2q->[$dscp];
                printf "  %u:%u", $qm & TC_MASK, $qm >> TC_SHIFT;
            }
            print "\n";
        }
    }
}

# Show DSCP-to-PCP mark map
sub show_mark {
    my $ifname = shift;
    my ( $port, $vif ) = split_ifname($ifname);
    my $data = get_interface( $port, "qos show" );

    # Skip interfaces with no QoS
    return unless defined($data);

    my $shaper = $data->{shaper};
    return unless defined($shaper);

    if ( defined($vif) ) {
        my $id = find_vif( $shaper, $vif );

        if ( defined($id) ) {
            show_subport_mark_map( $ifname,
                $shaper->{subports}->[$id]->{mark_map} );
            return;
        }
    }
    show_subport_mark_map( $ifname, $shaper->{subports}->[0]->{mark_map} );
}

sub show_subport_mark_map {
    my ( $ifname, $map_name ) = @_;
    my ( $dpids,  $dpsocks )  = Vyatta::Dataplane::setup_fabric_conns();

    return unless defined($map_name);

    for my $fid ( @{$dpids} ) {
        my $sock = ${$dpsocks}[$fid];
        unless ($sock) {
            warn "Can not connect to dataplane $fid\n";
            next;
        }

        my $response = $sock->execute("qos show mark-maps");
        next unless defined($response);

        my $decoded = decode_json($response);
        show_mark_map( $ifname, $map_name, $decoded );
    }
}

sub show_mark_map {
    my ( $ifname, $map_name, $mark_map_json ) = @_;
    my @mark_maps = @{ $mark_map_json->{'mark-maps'} };

    foreach my $map ( 0 .. $#mark_maps ) {
        if ( $mark_maps[$map]->{'map-name'} eq $map_name ) {
            my @pcp_values = @{ $mark_maps[$map]->{'pcp-values'} };

            print "DSCP->PCP mark map for $ifname: (dscp=d1d2)\n\n";
            print
              "     d2 |    0    1    2    3    4    5    6    7    8    9\n";
            print "  d1    |\n";
            print
              "  ------+---------------------------------------------------\n";

            for my $d2 ( 0 .. 6 ) {
                printf "     %u  |", $d2;
                for my $d1 ( 0 .. 9 ) {
                    my $dscp = $d2 * 10 + $d1;
                    last if $dscp >= 64;

                    printf "    %u", $pcp_values[$dscp];
                }
                print "\n";
            }
        }
    }
}

# Show 802.1p class of service map
sub show_pcp {
    my $ifname = shift;
    my ( $port, $vif ) = split_ifname($ifname);
    my $data = get_interface( $port, "qos show " );

    # Skip interfaces with no QoS
    return unless defined($data);

    my $shaper = $data->{shaper};
    return unless defined($shaper);

    if ( defined($vif) ) {
        my $id = find_vif( $shaper, $vif );

        if ( defined($id) ) {
            show_shaper_pcp( $shaper->{subports}->[$id] );
            return;
        }

        # If no QoS policy defined for vif then treated as untagged.
    }
    show_shaper_pcp( $shaper->{subports}->[0] );
}

sub show_shaper_pcp {
    my $subport = shift;
    my @pipes   = @{ $subport->{pipes} };

    for my $cid ( 0 .. $#pipes ) {
        my $pipe  = $pipes[$cid];
        my $pcp2q = $pipe->{pcp2q};

        my $cname = ( $cid == 0 ) ? "default" : "class $cid";
        print "Class Of Service->TC:WRR map for $cname\n\n";
        print "  PCP |    0    1    2    3    4    5    6    7\n";
        print "  ----+-----------------------------------------\n";
        print "      |";
        for my $pcp ( 0 .. 7 ) {
            my $qm = $pcp2q->[$pcp];
            printf "  %u:%u", $qm & TC_MASK, $qm >> TC_SHIFT;
        }
        print "\n";
    }
}

# Summary of all activity
sub show_shaper_queues {
    walk_subports( \&show_shaper_tc, @_ );
}

# Display rules associated with a given interface
sub show_rules {
    my ( $fmt, $ifname, $subport ) = @_;
    my $rules = $subport->{rules};
    return unless ( defined($rules) && defined( $rules->{groups} ) );
    my @groups = @{ $rules->{groups} };

    foreach my $j ( 0 .. $#groups ) {
        my $gname     = $groups[$j]->{name};
        my $grules    = $groups[$j]->{rules};
        my @prio_list = sort keys %{$grules};

        foreach my $prio (@prio_list) {
            my $matches = %{$grules}{$prio};
            my $bytes   = $matches->{bytes};
            my $packets = $matches->{packets};
            my $match   = $matches->{match};
            my $oper    = $matches->{operation};
            my $pcptag  = $matches->{markpcp};
            my $rprocs  = $matches->{rprocs};
            my $policer;
            my $act_grp;
            my $rule_rproc;
            my $exceed_pkts;
            my $exceed_bytes;

            if ( !defined($pcptag) ) {
                $pcptag = "";
            }

            # The "operation" field value can have an action-group or a policer
            # but not both - it may have neither.
            if ( index( $oper, "action-group" ) != -1 ) {
                my $act_grp_name;
                my $act_grp_rules;

                $act_grp      = $rprocs->{'action-group'};
                $act_grp_name = $act_grp->{name};

                # Check that the action-group names in the operation and this
                # rproc match
                if ( index( $oper, $act_grp_name ) == -1 ) {
                    printf("action-group names do not match");
                    return;
                }
                $act_grp_rules = $act_grp->{rules};
                my @rules_list = sort keys %{$act_grp_rules};

                foreach my $ruleno (@rules_list) {
                    my $rule = %{$act_grp_rules}{$ruleno};

                    $rule_rproc = $rule->{rule};

                    # Remove the "rproc=" prefix
                    $rule_rproc = substr( $rule_rproc, 6 );

                    if ( index( $rule_rproc, "policer" ) != -1 ) {
                        $policer      = $act_grp->{policer};
                        $exceed_pkts  = $policer->{'exceed-packets'};
                        $exceed_bytes = $policer->{'exceed-bytes'};
                    }
                }
            }
            if ( index( $oper, "policer" ) != -1 ) {
                $policer      = $rprocs->{policer};
                $exceed_pkts  = $policer->{'exceed-packets'};
                $exceed_bytes = $policer->{'exceed-bytes'};
            }
            if ($bits64) {
                printf $fmt, $ifname, $prio, $packets, $bytes, '';
                $ifname = '';
                printf( "%16s %6s %s %s %s\n",
                    '', 'Match:', $match, $oper, $pcptag )
                  if ( defined $oper && $oper ne '' );

                if ( defined $rule_rproc ) {
                    printf( "%23s %s %s\n", ' ', $rule_rproc, $pcptag );
                }
                if ( defined $policer ) {
                    printf( "%22s %20s %20s  exceeded\n",
                        ' ', $exceed_pkts, $exceed_bytes );
                }
            } else {
                printf $fmt, $ifname, $prio, $packets, $bytes, $match, "";
                printf $fmt, '', '', '', '', $oper, $pcptag
                  if ( defined $oper && $oper ne '' );
                $ifname = '';
                if ( defined $rule_rproc ) {
                    printf( "%50s %s %s\n", ' ', $rule_rproc, $pcptag );
                }
                if ( defined $policer ) {
                    printf( "%21s %10s %16s  exceeded\n",
                        ' ', $exceed_pkts, $exceed_bytes );
                }
            }
        }
    }
}

sub show_shaper_rules {
    walk_subports( \&show_rules, @_ );
}

sub show_interface_rules {
    walk_interfaces( \&show_shaper_rules, @_ );
}

# Displays class match stats on all interfaces
sub show_class_all {
    my $fmt = shift;

    walk_fabrics( "qos show", \&show_interface_rules, $fmt );

    exit 0;
}

# Displays class match stats
sub show_class {
    my $interfaces = shift;
    my $fmt;
    my $hdr;

    if ($bits64) {
        $fmt = "%-16s %5s %20s %20s %8s\n";
        $hdr = sprintf $fmt, 'Interface', 'Class', 'Packets', 'Bytes', '';
    } else {
        $fmt = "%-16s %4s %10s %16s  %-28s %s\n";
        $hdr = sprintf $fmt, 'Interface', 'Prio', 'Packets', 'Bytes', 'Match',
          '';
    }

    print $hdr, '-' x length($hdr), "\n";

    if ( '' eq $interfaces ) {
        show_class_all($fmt);
        return;
    }

    foreach my $name ( split( ' ', $interfaces ) ) {
        my ( $port, $vif ) = split_ifname($name);
        my $data = get_interface( $port, "qos show " );

        # Skip interfaces with no QoS
        return unless defined($data);

        # Only know about shaper
        my $shaper = $data->{shaper};
        return unless defined($shaper);

        my $subports = $shaper->{subports};

        if ( defined($vif) ) {
            my $id = find_vif( $shaper, $vif );

            if ( defined($id) ) {
                show_rules( $fmt, $name, $subports->[$id] );
                return;
            }

            # If no QoS policy defined for vif then treated as untagged.
        }

        # first result is untagged subport
        show_rules( $fmt, $name, $subports->[0] );
    }
}

sub usage {
    print "Usage: $0 [--64] --brief INTERFACE\n";
    print "       $0 [--64] --monitor\n";
    print "       $0 [--64] --class \n";
    print "       $0 --dscp INTERFACE\n";
    print "       $0 --mark INTERFACE\n";
    print "       $0 --cos INTERFACE\n";
    print "       $0 --platmap INTERFACE\n";
    print "       $0 --platinfo\n";
    print "       $0 [--64] --summary\n";
    print "       $0 [--64] INTERFACE...\n";
    exit 1;
}

my (
    $brief, $dscp,    $mark,    $pcp,      $monitor,
    $class, $summary, $platmap, $platinfo, $buf_errs
);

GetOptions(
    '64'            => \$bits64,
    'brief=s'       => \$brief,
    'monitor'       => \$monitor,
    'dscp=s'        => \$dscp,
    'platmap=s'     => \$platmap,
    'platinfo'      => \$platinfo,
    'buffer-errors' => \$buf_errs,
    'mark=s'        => \$mark,
    'cos=s'         => \$pcp,
    'class:s'       => \$class,
    'summary'       => \$summary,
) or usage();

show_brief($brief)          if $brief;
show_monitor()              if $monitor;
show_dscp($dscp)            if $dscp;
show_platform_map($platmap) if $platmap;
show_mark($mark)            if $mark;
show_pcp($pcp)              if $pcp;
show_class($class)          if defined($class);
show_summary()              if $summary;
show_platform_info()        if $platinfo;
show_buffer_errors()        if $buf_errs;

foreach my $ifname (@ARGV) {
    show($ifname);
}
