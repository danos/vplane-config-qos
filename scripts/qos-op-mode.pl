#! /usr/bin/perl
#
# Copyright (c) 2017-2019, AT&T Intellectual Property. All rights reserved.
#
# This script issues a "qos optimised-show" command to the vyatta dataplane and
# in return receives the QoS operational state (including counters) encoded in
# JSON.  Unfortunately this JSON encoding is not compatible with Yang as it uses
# untagged array elements, where the array index is implicitly used as the tag.
# Yang lists (which is the nearest thing to a JSON untagged array) can't cope
# with this, so this script converts the received JSON (which is significantly
# more compact than Yang compatible JSON) into Yang compatible JSON.
#
# It does this by using decode_json on the incoming JSON to generate a perl
# tree-like data-structure.  It then generates a new perl tree-like
# data-structure by descending down the branches of the original tree
# converting non-Yang compatible JSON arrays into Yang compatible lists (the
# major part of the conversation), and then calls encode_json passing in the
# new tree to generate the required Yang compatible JSON.
#
# There is also a "disconnect" between the vyatta QoS configuration model
# (interface names, vlan names, QoS policies and profiles), and the underlying
# Intel DPDK QoS framework (ports, subport, pipes, traffic-classes, and queues).
# The JSON returned by the vyatta-dataplane is based upon the DPDK QoS
# framework, so this script maps some of the underlying DPDK entities onto the
# appropriate QoS configuration model entities that customers might have some
# chance of understanding.
#
# Copyright (c) 2016-2017, Brocade Communications Systems, Inc.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

use strict;
use warnings;

use Getopt::Long;
use Config::Tiny;
use Term::Cap;
use JSON qw( decode_json encode_json );

use lib "/opt/vyatta/share/perl5/";
use Vyatta::Dataplane;
use Vyatta::Interface;
use Vyatta::Config;
use Vyatta::Misc qw( get_sysfs_value );

use constant TC_SHIFT => 2;
use constant TC_MASK  => 0x3;
use constant WRR_MASK => 0x7;

# For a particular interface name (trunk or vif) interogate the current config
# and return the QoS policy name associated with the specified interface
sub get_if_subport_policy_name {
    my $if_name = shift;
    my $config  = new Vyatta::Config();
    my $policy_name;

    if ( $if_name =~ /(\w+) vif (\d+)/ ) {

        # Deal with the various VIF port attachment points
        my $trunk_name = $1;
        my $vif_id     = $2;
        my $intf       = new Vyatta::Interface($trunk_name);

        $config->setLevel( $intf->path
              . " switch-group port-parameters vlan-parameters qos-parameters vlan $vif_id policy qos"
        );
        $policy_name = $config->returnOrigValue();
        return $policy_name if defined($policy_name);

        $config->setLevel( $intf->path . " vif $vif_id policy qos" );
        $policy_name = $config->returnOrigValue();
    } else {

        # Deal with the various trunk port attachment points
        my $intf = new Vyatta::Interface($if_name);

        $config->setLevel(
            $intf->path . " switch-group port-parameters policy qos" );
        $policy_name = $config->returnOrigValue();
        return $policy_name if defined($policy_name);

        $config->setLevel( $intf->path . " policy qos" );
        $policy_name = $config->returnOrigValue();
    }
    return $policy_name;
}

sub get_traffic_class {
    my $qmap_value = shift;

    return ( $qmap_value & TC_MASK );
}

sub get_queue_number {
    my $qmap_value = shift;

    return ( ( $qmap_value >> TC_SHIFT ) & WRR_MASK );
}

sub convert_tc_rates {
    my ( $cmd, $tc_rates_in ) = @_;
    my @tc_rates_out;
    my $tc_id = 0;

    foreach my $tc ( @{$tc_rates_in} ) {
        my %tc_rate_out;

        $tc_rate_out{'traffic-class'} = $tc_id;
        $tc_rate_out{rate} = $tc;
        $tc_rate_out{'rate-64'} = "$tc";
        push @tc_rates_out, \%tc_rate_out;
        $tc_id += 1;
    }
    return \@tc_rates_out;
}

sub convert_wrr_weights {
    my ( $cmd, $wrr_weights_in ) = @_;
    my @wrr_weights_out;
    my $queue_id = 0;

    foreach my $wrr ( @{$wrr_weights_in} ) {
        my %wrr_weight_out;

        $wrr_weight_out{queue}  = $queue_id;
        $wrr_weight_out{weight} = $wrr;
        push @wrr_weights_out, \%wrr_weight_out;
        $queue_id += 1;
    }
    return \@wrr_weights_out;
}

sub convert_dscp_map {
    my ( $cmd, $dscp_map_in ) = @_;
    my @dscp_map_out;
    my @tc_queue_to_dscp_map = ();
    my $dscp_id              = 0;

    foreach my $dscp_map_value ( @{$dscp_map_in} ) {
        my %dscp_out;
        my @dscp_values;
        my $tc = get_traffic_class($dscp_map_value);
        my $q  = get_queue_number($dscp_map_value);

        $dscp_out{'dscp'}          = $dscp_id;
        $dscp_out{'traffic-class'} = $tc;
        $dscp_out{'queue'}         = $q;
        push @dscp_map_out, \%dscp_out;

        if ( defined( $tc_queue_to_dscp_map[$tc][$q] ) ) {
            @dscp_values = @{ $tc_queue_to_dscp_map[$tc][$q] };
        } else {
            @dscp_values = ();
        }
        push @dscp_values, $dscp_id;
        $tc_queue_to_dscp_map[$tc][$q] = \@dscp_values;

        $dscp_id += 1;
    }
    return ( \@dscp_map_out, \@tc_queue_to_dscp_map );
}

sub convert_pcp_or_des_map {
    my ( $cmd, $map_in, $map_type ) = @_;
    my @map_out;
    my @tc_queue_to_map             = ();
    my $map_id                      = 0;

    foreach my $qmap_value ( @{$map_in} ) {
        my %map_out;
        my @map_values;
        my $tc = get_traffic_class($qmap_value);
        my $q  = get_queue_number($qmap_value);

        $map_out{$map_type}       = $map_id;
        $map_out{'traffic-class'} = $tc;
        $map_out{'queue'}         = $q;
        push @map_out, \%map_out;

        if ( defined( $tc_queue_to_map[$tc][$q] ) ) {
            @map_values = @{ $tc_queue_to_map[$tc][$q] };
        } else {
            @map_values = ();
        }
        push @map_values, $map_id;
        $tc_queue_to_map[$tc][$q] = \@map_values;

        $map_id += 1;
    }
    return ( \@map_out, \@tc_queue_to_map );
}

sub convert_map_list {
    my ( $cmd, $map_list, $map_type ) = @_;
    my @map_list_out;

    foreach my $value ( @{$map_list} ) {
        my %value_out;

        $value_out{"$map_type"} = $value;
        push @map_list_out, \%value_out;
    }
    return \@map_list_out;
}

sub convert_wred_map_list {
    my ($map_ar) = @_;
    my @map_list;

    foreach my $map ( @{$map_ar} ) {
        my %map_ent;

        $map_ent{'res-grp'}          = $map->{res_grp};
        $map_ent{'random-dscp-drop'} = $map->{random_dscp_drop} & 0xffffffff;
        push @map_list, \%map_ent;
    }
    return \@map_list;
}

sub convert_wred_map_list_64 {
    my ($map_ar) = @_;
    my @map_list;

    foreach my $map ( @{$map_ar} ) {
        my %map_ent;

        $map_ent{'res-grp-64'}          = "$map->{res_grp}";
        $map_ent{'random-dscp-drop-64'} = "$map->{random_dscp_drop}";
        push @map_list, \%map_ent;
    }
    return \@map_list;
}

sub convert_tc_queues {
    my ( $cmd, $tc_queues_in, $tc_id, $reverse_map, $map_type_values ) = @_;
    my @tc_queues_out;
    my $queue_id = 0;

    foreach my $queue ( @{$tc_queues_in} ) {
        my %queue_out;
        my $map_type;

        $queue_out{queue} = $queue_id;

        # Truncate the value for the old 32-bit counters
        $queue_out{packets} = $queue->{packets} & 0xffffffff;
        $queue_out{bytes}   = $queue->{bytes} & 0xffffffff;

        # the dropped counter is total drops, we just want tail-drops
        $queue_out{dropped} =
          ( $queue->{dropped} - $queue->{random_drop} ) & 0xffffffff;
        $queue_out{'random-drop'} = $queue->{random_drop} & 0xffffffff;
        if ( defined( $queue->{wred_map} ) ) {
            $queue_out{'wred-map'} =
              convert_wred_map_list( $queue->{wred_map} );
        }

        # Don't truncate the new 64-bit counters
        $queue_out{'packets-64'} = "$queue->{packets}";
        $queue_out{'bytes-64'}   = "$queue->{bytes}";

        # the dropped counter is total drops, we just want tail-drops
        my $dropped_64 = $queue->{dropped} - $queue->{random_drop};

        $queue_out{'dropped-64'}     = "$dropped_64";
        $queue_out{'random-drop-64'} = "$queue->{random_drop}";
        if ( defined( $queue->{wred_map} ) ) {
            $queue_out{'wred-map-64'} =
              convert_wred_map_list_64( $queue->{wred_map} );
        }
        if ( defined( $queue->{qlen} ) ) {
            $queue_out{qlen} = $queue->{qlen} & 0xffffffff;
            $queue_out{'qlen-packets'} = $queue->{qlen};
        } else {
            $queue_out{'qlen-bytes'} = $queue->{'qlen-bytes'};
        }
        $queue_out{'priority-local'} = $queue->{prio_local};
        $map_type_values =~ /(dscp|pcp|designation)-values/;
        $map_type = $1;
        $queue_out{"$map_type_values"} =
          convert_map_list( $cmd, $reverse_map->[$tc_id][$queue_id],
            $map_type );
        push @tc_queues_out, \%queue_out;
        $queue_id += 1;
    }
    return \@tc_queues_out;
}

sub convert_tc_queues_list {
    my ( $cmd, $tc_queues_list_in, $reverse_map, $map_type_values ) = @_;
    my @tc_queues_list_out;
    my $tc_id = 0;

    foreach my $tc_queues_in ( @{$tc_queues_list_in} ) {
        my %tc_queues_out;

        $tc_queues_out{'traffic-class'} = $tc_id;
        $tc_queues_out{'queue-statistics'} =
          convert_tc_queues( $cmd, $tc_queues_in, $tc_id, $reverse_map,
            $map_type_values );
        push @tc_queues_list_out, \%tc_queues_out;
        $tc_id += 1;
    }
    return \@tc_queues_list_out;
}

sub convert_pipe {
    my ( $cmd, $pipe_in, $pipe_id, $profile_name ) = @_;
    my %pipe_out;
    my $queue_list;
    my $reverse_dscp_map;
    my $reverse_pcp_map;
    my $reverse_des_map;

    $pipe_out{pipe}          = $pipe_id;
    $pipe_out{'qos-class'}   = $pipe_id;
    $pipe_out{'qos-profile'} = $profile_name;
    if ( $cmd eq 'all' ) {
        $pipe_out{'token-bucket-rate'}    = $pipe_in->{params}->{tb_rate};
        $pipe_out{'token-bucket-rate-64'} = "$pipe_in->{params}->{tb_rate}";
        $pipe_out{'token-bucket-size'}    = $pipe_in->{params}->{tb_size};
        $pipe_out{'traffic-class-period'} = $pipe_in->{params}->{tc_period};
        $pipe_out{'traffic-class-rates'} =
          convert_tc_rates( $cmd, $pipe_in->{params}->{tc_rates} );
        $pipe_out{'weighted-round-robin-weights'} =
          convert_wrr_weights( $cmd, $pipe_in->{params}->{wrr_weights} );
    }

    ( $pipe_out{'dscp-to-queue-map'}, $reverse_dscp_map ) =
      convert_dscp_map( $cmd, $pipe_in->{dscp2q} );
    ( $pipe_out{'pcp-to-queue-map'}, $reverse_pcp_map ) =
      convert_pcp_or_des_map( $cmd, $pipe_in->{pcp2q}, 'pcp' );
    ( $pipe_out{'designation-to-queue-map'}, $reverse_des_map ) =
      convert_pcp_or_des_map( $cmd, $pipe_in->{designation}, 'designation' );

    if ( defined( $pipe_out{'dscp-to-queue-map'} ) ) {
        $queue_list =
          convert_tc_queues_list( $cmd, $pipe_in->{tc}, $reverse_dscp_map,
            "dscp-values" );
    }

    if ( defined( $pipe_out{'pcp-to-queue-map'} ) ) {
        $queue_list =
          convert_tc_queues_list( $cmd, $pipe_in->{tc}, $reverse_pcp_map,
            "pcp-values" );
    }

    if ( defined( $pipe_out{'designation-to-queue-map'} ) ) {
        $queue_list =
          convert_tc_queues_list( $cmd, $pipe_in->{tc}, $reverse_des_map,
            "designation-values" );
    }

    $pipe_out{'traffic-class-queues-list'} = $queue_list;

    if ( $cmd eq 'stats' ) {

        # Throw away the map data if we are processing a 'stats' request
        delete $pipe_out{'dscp-to-queue-map'};
        delete $pipe_out{'pcp-to-queue-map'};
        delete $pipe_out{'designation-to-queue-map'};
    }
    return \%pipe_out;
}

sub convert_pipes {
    my ( $cmd, $pipes_in, $subport_name ) = @_;
    my @pipe_list_out;
    my $pipe_id     = 0;
    my $policy_name = get_if_subport_policy_name($subport_name);

    if ( !defined($policy_name) ) {
        print "policy_name not defined for $subport_name\n";
        return;
    }
    my $policy_config = new Vyatta::Config("policy qos name $policy_name");

    foreach my $pipe_in ( @{$pipes_in} ) {
        my $pipe_out;
        my $profile_name;

        if ( $pipe_id == 0 ) {
            $profile_name = $policy_config->returnOrigValue("shaper default");
        } else {
            $profile_name =
              $policy_config->returnOrigValue("shaper class $pipe_id profile");
        }

        # Only return op-mode data for this pipe/qos-class if a qos-profile
        # has been configured for it.
        if ( defined($profile_name) ) {
            $pipe_out = convert_pipe( $cmd, $pipe_in, $pipe_id, $profile_name );
            push @pipe_list_out, $pipe_out;
        }
        $pipe_id += 1;
    }
    return \@pipe_list_out;
}

sub convert_tcs {
    my ( $cmd, $tcs_in ) = @_;
    my @tc_list_out;
    my $tc_id = 0;

    foreach my $tc_in ( @{$tcs_in} ) {
        my %tc_out;

        $tc_out{'traffic-class'} = $tc_id;

        # Truncate these values for the old 32-bit counters
        $tc_out{packets} = $tc_in->{packets} & 0xffffffff;
        $tc_out{bytes}   = $tc_in->{bytes} & 0xffffffff;

        # the dropped counter is total drops, we just want tail-drops
        $tc_out{dropped} =
          ( $tc_in->{dropped} - $tc_in->{random_drop} ) & 0xffffffff;
        $tc_out{'random-drop'} = $tc_in->{random_drop} & 0xffffffff;

        # 64-bit counters don't get truncated
        $tc_out{'packets-64'} = "$tc_in->{packets}";
        $tc_out{'bytes-64'}   = "$tc_in->{bytes}";

        # the dropped counter is total drops, we just want tail-drops
        my $dropped_64 = $tc_in->{dropped} - $tc_in->{random_drop};

        $tc_out{'dropped-64'}     = "$dropped_64";
        $tc_out{'random-drop-64'} = "$tc_in->{random_drop}";

        push @tc_list_out, \%tc_out;
        $tc_id += 1;
    }
    return \@tc_list_out;
}

sub convert_npf_rule {
    my ( $cmd, $rules_in ) = @_;
    my @rules_out;

    foreach my $rule_id ( keys %{$rules_in} ) {
        my $rule_in        = $rules_in->{$rule_id};
        my $rule_operation = $rule_in->{operation};
        my %rule_out;

        $rule_out{'rule-number'} = "$rule_id";
        if ( $rule_operation =~ /tag\((\d+)\)/ ) {
            $rule_out{'qos-class'} = $1;
        }

        if ( index( $rule_operation, "action-group" ) != -1 ) {
            $rule_out{'action-group'} = $rule_in->{'rprocs'}->{'action-group'};
            my $policer = $rule_in->{'rprocs'}->{'action-group'}->{'policer'};
            if ( defined($policer) ) {
                $rule_out{'exceeded-packets'} = $policer->{'exceed-packets'};
                $rule_out{'exceeded-bytes'}   = $policer->{'exceed-bytes'};
            }
        }
        if ( index( $rule_operation, "policer" ) != -1 ) {
            my $policer = $rule_in->{'rprocs'}->{'policer'};
            $rule_out{'exceeded-packets'} = $policer->{'exceed-packets'};
            $rule_out{'exceeded-bytes'}   = $policer->{'exceed-bytes'};
        }

        $rule_out{packets} = "$rule_in->{packets}";
        $rule_out{bytes}   = "$rule_in->{bytes}";

        push @rules_out, \%rule_out;
    }
    return \@rules_out;
}

sub convert_groups {
    my ( $cmd, $subport_ifname, $group_list_in ) = @_;
    my @group_list_out;

    my $ifindex = get_sysfs_value( $subport_ifname, 'ifindex' );

    foreach my $group_in ( @{$group_list_in} ) {
        my %group_out;

        $group_out{name}      = $group_in->{name};
        $group_out{class}     = $group_in->{class};
        $group_out{ifindex}   = $ifindex;
        $group_out{direction} = $group_in->{direction};
        $group_out{rule}      = convert_npf_rule( $cmd, $group_in->{rules} );

        push @group_list_out, \%group_out;
    }
    return \@group_list_out;
}

sub convert_rules {
    my ( $cmd, $subport_ifname, $rules_in ) = @_;
    my %rules_out;

    $rules_out{groups} =
      convert_groups( $cmd, $subport_ifname, $rules_in->{groups} );
    return \%rules_out;
}

sub convert_subports {
    my ( $cmd, $subports_in, $ifname, $vlan_list_ref ) = @_;
    my @subport_list_out;
    my $subport_id = 0;
    my @vlan_list  = @{$vlan_list_ref};

    foreach my $subport_in ( @{$subports_in} ) {
        my %subport_out;
        my $subport_name   = $ifname;
        my $subport_ifname = $ifname;

        if ( $subport_id != 0 ) {
            foreach my $vlan (@vlan_list) {
                if ( $vlan->{subport} == $subport_id ) {
                    my $vif = $vlan->{tag};
                    #
                    # ++AGD++ do we want to return "<if-name> vif <vif>" or
                    # "<if-name>.<vif>" here??
                    #
                    $subport_name   .= " vif $vif";
                    $subport_ifname .= ".$vif";
                    last;
                }
            }
        }
        $subport_out{subport} = $subport_id;
        $subport_out{'subport-name'} = $subport_name;
        $subport_out{'traffic-class-list'} =
          convert_tcs( $cmd, $subport_in->{tc} );
        $subport_out{'pipe-list'} = convert_pipes( $cmd, $subport_in->{pipes},
            $subport_out{'subport-name'} );
        $subport_out{rules} =
          convert_rules( $cmd, $subport_ifname, $subport_in->{rules} );

        push @subport_list_out, \%subport_out;
        $subport_id += 1;
    }
    return \@subport_list_out;
}

sub convert_vlans {
    my ( $cmd, $vlans_in, $iname ) = @_;
    my @vlan_list_out;

    foreach my $vlan ( @{$vlans_in} ) {
        my $subport = $vlan->{subport};
        my $tag     = $vlan->{tag};
        my %vlan_out;

        $vlan_out{tag}     = $tag;
        $vlan_out{subport} = $subport;

        push @vlan_list_out, \%vlan_out;
    }
    return \@vlan_list_out;
}

sub convert_shaper {
    my ( $cmd, $shaper_in, $ifname ) = @_;
    my %shaper_out;

    $shaper_out{'vlan-list'} =
      convert_vlans( $cmd, $shaper_in->{vlans}, $ifname );
    $shaper_out{'subport-list'} =
      convert_subports( $cmd, $shaper_in->{subports},
        $ifname, $shaper_out{'vlan-list'} );
    if ( $cmd eq 'stats' ) {
        delete $shaper_out{'vlan-list'};
    }
    return \%shaper_out;
}

# Convert the list of interfaces
sub convert_if_list {
    my ( $cmd, $op_mode_state ) = @_;
    my @if_list_out = ();

    foreach my $ifname ( keys %{$op_mode_state} ) {
        my $shaper_in = $op_mode_state->{$ifname}->{shaper};
        my %if_shaper_out;

        $if_shaper_out{"ifname"} = "$ifname";
        $if_shaper_out{"shaper"} = convert_shaper( $cmd, $shaper_in, $ifname );
        push @if_list_out, \%if_shaper_out;
    }

    return \@if_list_out;
}

# Walk through all fabrics issuing "qos optimised-show" requests
sub get_op_mode {
    my $cmd = shift;
    my ( $dpids, $dpsocks ) = Vyatta::Dataplane::setup_fabric_conns();

    for my $fid ( @{$dpids} ) {
        my %yang_state;
        my $sock = ${$dpsocks}[$fid];
        unless ($sock) {
            warn "Can not connect to dataplane $fid\n";
            next;
        }

        my $response = $sock->execute("qos optimised-show");
        next unless defined($response);

        my $op_mode_state = decode_json($response);

        $yang_state{"if-list"} = convert_if_list( $cmd, $op_mode_state );
        print encode_json( \%yang_state );
    }

    # Close down ZMQ sockets. This is needed or sometimes a hang
    # can occur due to timing issues with libzmq - see VRVDR-17233 .
    Vyatta::Dataplane::close_fabric_conns( $dpids, $dpsocks );
    return;
}

sub usage {
    print "Usage: $0  \n";
    print "       $0 --all\n";
    print "       $0 --statistics\n";
    exit 1;
}

my ( $all, $statistics );
GetOptions(
    'all'        => \$all,
    'statistics' => \$statistics,
) or usage();

get_op_mode('all')   if $all;
get_op_mode('stats') if $statistics;
