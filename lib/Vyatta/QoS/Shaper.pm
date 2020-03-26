# Module QoS::Shaper.pm
#
# Copyright (c) 2017-2019, AT&T Intellectual Property.
# All Rights Reserved.
# Copyright (c) 2013-2017, Brocade Communications Systems, Inc.
# All Rights Reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#
package Vyatta::QoS::Shaper;

use strict;
use warnings;
use Carp;
use List::Util qw(first);

use Vyatta::Config;
use Vyatta::FWHelper qw(validate_npf_rule);
use Vyatta::Rate qw(parse_rate);
use Vyatta::QoS::Profile qw(valid_binding);
use Vyatta::QoS::Red qw(DEF_QSIZE_PACKETS DEF_QSIZE_BYTES);
use Vyatta::QoS::Class;
use Vyatta::QoS::Subport;
use Vyatta::QoS::Debug;
use Vyatta::DSCP qw(str2dscp);
use Data::Dumper;

our @ISA = qw(Exporter);

our @EXPORT = qw(_getSubport);

use constant { QUEUES_PER_TC => 8, };

# Create new policy
sub new {
    my ( $class, $level ) = @_;
    my $config = new Vyatta::Config($level);

    my $self = {};
    bless $self, $class;
    $self->{path}     = $level;
    $self->{mark_map} = $config->returnValue('mark-map');

    return $self;
}

# If random-detect is configured in the policy under traffic-class
# (ie per subport) we need to check the global-profiles incase one
# has per Q RED configured in which case it must be blocked.
sub validate_perQ_red {
    my ( $classes, $globals ) = @_;

    # The first class will be undef for the class default
    foreach my $class ( @{$classes} ) {
        if ( defined $class ) {
            my $profile = $class->{profile};
            foreach my $name ( keys %$globals ) {
                if ( $profile eq $globals->{$name}->{name} ) {
                    my $q_conf = $globals->{$name}->{queue};
                    foreach my $q ( @{$q_conf} ) {
                        invalid
"Subport level wred must not be configured with per queue wred\n"
                          if ( defined $q->{wred_map} );
                    }
                }
            }
        }
    }
}

# Check the max-threshold configured in a global profile isn't
# greater than the qlimit configured in the policy.
sub validate_perQ_Qlim {
    my ( $classes, $globals, $qlims ) = @_;

    # The first class will be undef for the class default
    foreach my $class ( @{$classes} ) {
        if ( defined $class ) {
            my $profile = $class->{profile};
            foreach my $name ( keys %$globals ) {
                if ( $profile eq $globals->{$name}->{name} ) {
                    my $q_conf = $globals->{$name}->{queue};
                    foreach my $q ( @{$q_conf} ) {
                        if ( defined $q->{wred_map} ) {
                            foreach my $map ( @{ $q->{wred_map} } ) {
                                if ( $map->{qmax} >= @$qlims[ $q->{tc} ] ) {
                                    invalid
"Global profile $profile RED qmax $map->{qmax} >= queue limit @$qlims[$q->{tc}]\n";
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

# Initialize based on configuration
sub init {
    my ( $self, $intf, $router ) = @_;
    my $level  = $self->{path};
    my $config = new Vyatta::Config($level);

    $self->{default}  = $config->returnValue('default');
    $self->{overhead} = $config->returnValue('frame-overhead');

    my $globals = _getGlobalProfiles();
    $self->{global} = $globals;
    my $vlans = _getVLans( $level, $intf, $router );
    $self->{vlan} = $vlans;

    # This will check per Q RED configurations to ensure they're
    # ok if configured in a global profile
    foreach my $vlan (%$vlans) {
        my $subport = ${ $self->{vlan} }{$vlan};
        my @qlims   = ();
        if ( defined $subport->{tc} ) {
            my @tcs = @{ $subport->{tc} };
            foreach my $tc (@tcs) {
                if ( defined $tc->{red} ) {
                    validate_perQ_red( \@{ $subport->{class} }, $globals );
                }
                if ( defined $tc->{limit} ) {
                    push @qlims, $tc->{limit};
                } else {
                    if ($main::byte_limits) {
                        push @qlims, DEF_QSIZE_BYTES;
                    } else {
                        push @qlims, DEF_QSIZE_PACKETS;
                    }
                }
            }
            validate_perQ_Qlim( \@{ $subport->{class} }, $globals, \@qlims );
        }
    }
}

sub _getSubport {
    my ( $level, $vif, $tag, $parent_bw, $trunk_tc_ref ) = @_;
    my $config = new Vyatta::Config($level);

    my $default = $config->returnValue("default");

    my $subport =
      new Vyatta::QoS::Subport( $level, $vif, $tag, $parent_bw, $default,
        $trunk_tc_ref );

    return $subport;
}

# Using the switch root CLI apply a policy to an interface
sub switch_get_vlans {
    my ( $intf, $port_bw, $trunk_tc, %vlans ) = @_;

    my $config = new Vyatta::Config(
"$intf->{path} switch-group port-parameters vlan-parameters qos-parameters"
    );
    foreach my $vlan ( $config->listNodes("vlan") ) {
        my $vpol = $config->returnValue("vlan $vlan policy qos");
        if ( defined $vpol ) {
            $vlans{$vlan} = _getSubport( "policy qos name $vpol shaper",
                $vlan, $vlan, $port_bw, $trunk_tc );
        }
    }

    return \%vlans;
}

# Read vlan params from the config
# vlan 0 is for untagged traffic
sub _getVLans {
    my ( $level, $ifname, $router ) = @_;    # qos-policy $name
    my %vlans;

    my $intf = new Vyatta::Interface($ifname);
    invalid "Interface $ifname does not exist"
      unless defined($intf);

    my $untag = _getSubport( $level, 0, 0 );
    $vlans{0} = $untag;
    my $port_bw  = $untag->bandwidth();
    my $trunk_tc = $untag->tc();

    # $router = 1 is a VR, $router = 0 is a switch
    if ( $router eq 0 ) {
        return switch_get_vlans( $intf, $port_bw, $trunk_tc, %vlans );
    }

    my $config = new Vyatta::Config();

    foreach my $vif (
        Vyatta::Interface::get_vif_interfaces(
            $config,                 'listNodes',
            $intf->physicalDevice(), $intf->type(),
            $intf->path()
        )
      )
    {
        my $vifid;
        if ( $vif->{path} =~ /.*vif\s(\d+)/msx ) {
            $vifid = $1;
        } else {
            invalid "Cannot find VIF ID in [$vif->{path}]";
        }

        my $tag = $config->returnValue("$vif->{path} vlan");
        if ( not defined $tag ) {
            $tag = $vifid;
        }

        my $vpol = $config->returnValue("$vif->{path} policy qos");
        if ( defined $vpol ) {
            $vlans{$tag} = _getSubport( "policy qos name $vpol shaper",
                $vifid, $tag, $port_bw, $trunk_tc );
        }
    }

    return \%vlans;
}

sub _getGlobalProfiles {
    my $config = new Vyatta::Config('policy qos');
    my %globals;

    foreach my $name ( $config->listNodes('profile') ) {
        $globals{$name} = new Vyatta::QoS::Profile("policy qos profile $name");
    }
    return \%globals;
}

# what is the most number of classes used
# Note: has to add 1 to account for default class
sub _max_pipes {
    my $self  = shift;
    my %vlans = %{ $self->{vlan} };
    my $max   = 0;

    foreach my $tag ( keys %vlans ) {
        my $vlan  = $vlans{$tag};
        my $count = scalar( @{ $vlan->{class} } );

        $max = $count if ( $count > $max );
    }

    return $max;
}

sub build_profile_index {
    my ( $global_profiles_ref, $vlans_ref ) = @_;
    my %pindex;
    my $i = 0;
    foreach my $name ( keys %$global_profiles_ref ) {
        $pindex{"global $name"} = $i;
        $i += 1;
    }
    foreach my $tag ( keys %$vlans_ref ) {
        my $profiles_base = keys %pindex;
        my @profiles = $vlans_ref->{$tag}->profile_list($global_profiles_ref);
        for my $i ( 0 .. $#profiles ) {
            my ( $name, $profile ) = @{ $profiles[$i] };
            my $pid = $profiles_base + $i;

            # if the profile name is global, override the calculated id
            if ( defined $pindex{"global $name"} ) {
                $pid = $pindex{"global $name"};
            }
            $pindex{"$tag $name"} = $pid;
        }
    }
    return %pindex;
}

# Generate list of commands to dataplane to setup this policy
# This is where conversion from global profile to per interface
# policy happens
sub commands {
    my ( $self, $ifindex ) = @_;
    my @cmds;
    my %vlans    = %{ $self->{vlan} };
    my %pindex   = build_profile_index( $self->{global}, $self->{vlan} );
    my $subports = scalar keys %vlans;
    my $pipes    = $self->_max_pipes();
    my $profiles = ( scalar keys %pindex );

    # tell dataplane size of parameters
    my $cmd = sprintf( "qos %u port subports %u pipes %u profiles %u",
        $ifindex, $subports, $pipes, $profiles );

    my $overhead = $self->{overhead};
    $cmd .= sprintf( " overhead %d", $overhead )
      if defined($overhead);
    push @cmds, $cmd;

    # enumerate all the profiles to dataplane and
    # record name to index assignment
    # foreach subport
    my @tags = sort keys %vlans;
    for my $sid ( 0 .. $#tags ) {
        my $tag     = $tags[$sid];
        my $subport = $vlans{$tag};

        # subport bandwidth and traffic classes
        push @cmds, $subport->commands( $ifindex, $sid );

        # vlan to subport mapping
        push @cmds, "qos $ifindex vlan $tag $sid";

        # add vlan profiles
        while ( my ( $pname, $profile ) = each %{ $subport->{profile} } ) {
            my $pid = $pindex{"$tag $pname"};
            push @cmds, $profile->commands("qos $ifindex profile $pid");
        }

        # add global profiles
        while ( my ( $pname, $profile ) = each %{ $self->{global} } ) {
            my $pid = $pindex{"global $pname"};
            push @cmds, $profile->commands("qos $ifindex profile $pid");
        }

        # mapping default profile
        my $did = $pindex{"$tag $subport->{default}"};
        push @cmds, "qos $ifindex pipe $sid 0 $did";

        # foreach class
        my @classes = @{ $subport->{class} };
        for my $cid ( 1 .. $#classes ) {
            my $class = $classes[$cid];
            next unless defined($class);

            my $pname = $class->profile();
            my $pid   = $pindex{"$tag $pname"};

            # check against the global profiles is not local
            $pid = $pindex{"global $pname"} unless defined($pid);

            # send class/pipe to profile mapping
            push @cmds, "qos $ifindex pipe $sid $cid $pid";

            foreach my $rule ( $class->rules() ) {
                push @cmds, "qos $ifindex match $sid $cid $rule";
            }
        }
    }

    return @cmds;
}

# global flag that error has been called.
my $errors;

# standard format for error location
sub error {
    my $path = shift;

    if ( ++$errors < 10 ) {
        warn "@_\n";
        warn " at node: $path\n\n";
    }
}

# Validate policy
# This is a consolidation of all the individual commit checks that used to
# be in individual nodes
sub valid {
    my $self       = shift;
    my $level      = $self->{path};
    my $config     = new Vyatta::Config($level);
    my $qos_config = new Vyatta::Config('policy qos');

    $errors = 0;

    my @global_profiles = $qos_config->listNodes('profile');
    foreach my $id (@global_profiles) {
        valid_profile("policy qos profile $id");
    }

    my @local_profiles = $config->listNodes('profile');
    foreach my $id (@local_profiles) {
        valid_profile("$level profile $id");
    }

    my @all_profiles = @local_profiles;

    push @all_profiles, @global_profiles;

    foreach my $class ( $config->listNodes('class') ) {
        valid_class( "$level class $class", @all_profiles );
    }

    my %global_pdict = map { $_ => 0 } @global_profiles;
    my %local_pdict  = map { $_ => 0 } @local_profiles;
    valid_subport( $level, \%global_pdict, \%local_pdict );

    # we are unable to check that all global profiles are being referenced here
    while ( my ( $profile, $used ) = each %local_pdict ) {
        warn "warning: local profile $profile defined but has no references\n"
          if ( $used == 0 );
    }

    return ( $errors == 0 );
}

# Validate subport
# used for top-level as well as per-vlan
sub valid_subport {
    my ( $level, $global_pdict, $local_pdict ) = @_;
    my $config = new Vyatta::Config($level);

    my $profile = $config->returnValue('default');
    if ( defined($profile) ) {
        if ( exists $global_pdict->{$profile} ) {
            $global_pdict->{$profile} += 1;
        } elsif ( exists $local_pdict->{$profile} ) {
            $local_pdict->{$profile} += 1;
        }
    }

    my @classes = $config->listNodes('class');
    foreach my $class (@classes) {
        my $path    = "class $class profile";
        my $profile = $config->returnValue($path);
        if ( defined($profile) ) {
            if ( exists $global_pdict->{$profile} ) {
                $global_pdict->{$profile} += 1;
            } elsif ( exists $local_pdict->{$profile} ) {
                $local_pdict->{$profile} += 1;
            }
        }
    }
}

# error function for validate_npf_rule
sub npf_error {
    my $path = shift->setLevel(".");
    error( $path, @_ );
}

# Validates a match
sub valid_match {
    my $level        = shift;
    my $config       = new Vyatta::Config($level);
    my $group_config = new Vyatta::Config("resources group");

    validate_npf_rule( $config, $group_config, \&npf_error );
}

# Validates a class
sub valid_class {
    my ( $level, @profiles ) = @_;
    my $config = new Vyatta::Config($level);

    foreach my $match ( $config->listNodes('match') ) {
        valid_match("$level match $match");
    }
}

sub valid_profile_dscpgroupmap {
    my $level       = shift . ' map dscp-group';
    my $config      = new Vyatta::Config($level);
    my $dscp_bitmap = 0;
    my $error       = 0;

    foreach my $name ( $config->listNodes() ) {
        my $group_config =
          new Vyatta::Config("resources group dscp-group $name dscp");

        foreach my $dscp ( $group_config->returnValues() ) {

            # We might have diff-serv dscp-name e.g. af12, cs6, ef
            $dscp = str2dscp($dscp);
            if ( ( ( 1 << $dscp ) & $dscp_bitmap ) != 0 ) {
                warn "Multiple use of dscp-value $dscp in profile map\n";
                $error = 1;
            }
            $dscp_bitmap |= ( 1 << $dscp );
        }
    }
    invalid "" if ( $error == 1 );
}

# Check if profile is valid
sub valid_profile {
    my $level  = shift;
    my $config = new Vyatta::Config($level);

    # get list of queues, if not defined then have default queues
    my @queues = $config->listNodes('queue');
    if (@queues) {
        my @qpertc = (0) x QUEUES_PER_TC;

        foreach my $id (@queues) {
            my $path = "queue $id traffic-class";
            my $prio = $config->returnValue($path);
            if ( defined($prio) ) {
                ++$qpertc[$prio];
                error $level,
                  "Too many queues assigned to traffic-class $prio\n"
                  if ( $qpertc[$prio] > QUEUES_PER_TC );
            } else {
                error "$level $path",
                  "Traffic-class not defined for queue $id\n";
            }
        }
    } else {
        @queues = qw(0 1 2 3 4 5 6 7);
    }
    valid_profile_dscpgroupmap($level);
}

sub valid_vif_binding {
    my ( $self, $intf, $vif ) = @_;
    my $intfconfig = new Vyatta::Config( $intf->{path} );
    my $pname      = $intfconfig->returnValue("vif $vif policy qos");
    my $qos_config = new Vyatta::Config("policy qos name");

    return 1 unless $qos_config->exists($pname);

    my $config = new Vyatta::Config("policy qos name $pname shaper");

    if ( not $config->isDefault('frame-overhead') ) {
        invalid "frame-overhead cannot be defined in policy bound to a VIF\n";
    }

    return 1;
}

# Validate that this policy can be bound to a given interface
sub valid_binding {
    my ( $self, $intf, $vif, $tag ) = @_;
    my $ifname        = $intf->name();
    my %pindex        = build_profile_index( $self->{global}, $self->{vlan} );
    my $port_profiles = ( scalar keys %pindex );

    warn
"warning: unsupported configuration, > 256 QoS profiles configured on $ifname\n"
      unless $port_profiles <= 256;

    if ( $vif != 0 ) {
        $self->valid_vif_binding( $intf, $vif );
    }

    my $subport = ${ $self->{vlan} }{$tag};
    if ( defined $subport ) {

        # We only need to validate the subport that is being changed
        return 0
          unless $subport->valid_binding( $intf, $self->{overhead},
            $self->{global} );
    }

    return 1;
}

sub bump_global_profile_counts {
    my ( $self, $globals ) = @_;
    my %vlans = %{ $self->{vlan} };

    foreach my $tag ( keys %vlans ) {
        my $subport = $vlans{$tag};
        my $dname   = $subport->{default};

        # bump the default profile name if global
        if ( exists $globals->{$dname} ) {
            $globals->{$dname} += 1;
        }

        # bump each class profile name if global
        my @classes = @{ $subport->{class} };
        for my $cid ( 1 .. $#classes ) {
            my $class = $classes[$cid];
            next unless defined($class);

            my $pname = $class->profile();

            if ( exists $globals->{$pname} ) {
                $globals->{$pname} += 1;
            }
        }
    }
}

1;
