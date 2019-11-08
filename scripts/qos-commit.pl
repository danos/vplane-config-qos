#!/usr/bin/perl

# Copyright (c) 2017-2019, AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2013-2017, Brocade Communications Systems, Inc.
# All rights reserved.
#
# SPDX-License-Identifier: LGPL-2.1-only
#

use strict;
use warnings;

use lib "/opt/vyatta/share/perl5";

use Getopt::Long;
use Vyatta::Config;
use Vyatta::DSCP;
use Vyatta::VPlaned;
use Vyatta::Interface;
use Vyatta::SwitchConfig;
use Vyatta::FWHelper qw(action_group_features);
use Vyatta::QoS::Policy
  qw(make_policy get_ifindex vif_binding_changed config_same_as_before get_byte_limits);
use Vyatta::DSCP qw(str2dscp);
use Data::Dumper;

my $debug = $ENV{'QOS_DEBUG'};

my $ctrl;

our $byte_limits;

our @ISA = qw(Exporter);

our @EXPORT = qw($byte_limits);

sub open_ctrl {
    if ( !defined($ctrl) ) {
        $ctrl = new Vyatta::VPlaned;
        die "Can not connect to controller: $!\n"
          unless defined($ctrl);
    }
}

use constant {
    APPLY_POLICY            => 0,
    REMOVE_POLICY           => 1,
    REMOVE_AND_APPLY_POLICY => 2
};

# tell controller of policy change
sub update_policy_instance {
    my ( $ifname, $action, $name, $router ) = @_;
    my $ifindex = get_ifindex($ifname);

    # Hotplug interfaces won't be found
    if ( not defined $ifindex ) {
        return;
    }

    # pseudo-path for config store
    my $path = "qos $ifindex";

    open_ctrl();

    if ( $action eq REMOVE_POLICY || $action eq REMOVE_AND_APPLY_POLICY ) {

        # delete old config
        $ctrl->store( $path, "$path disable", $ifname, "DELETE" );

        if ( $action eq REMOVE_POLICY ) {
            return;
        }
    }

    my $policy = make_policy($name);

    # This error now caught and reported by yang
    exit 0 unless defined($policy);

    $policy->init( $ifname, $router );

    # get list of commands to create the new policy
    my @cmds = $policy->commands($ifindex);

    foreach my $cmd (@cmds) {
        print "send: $cmd\n" if $debug;

        $ctrl->store( "$path $cmd", $cmd, $ifname );
    }

    $ctrl->store( $path, "$path enable", $ifname );
}

sub update_installed_policies {
    my ( $policy, $ifname, $config, $update_action ) = @_;
    my $name         = $config->returnValue("$ifname policy qos");
    my $policy_found = 0;

    # Only examine the vifs if the port level policy hasn't changed
    if ( ( defined $name and $policy eq $name ) ) {
        $policy_found = 1;
    } else {
        foreach my $vif ( $config->listNodes("$ifname vif") ) {
            my $vif_name = $config->returnValue("$ifname vif $vif policy qos");
            if ( defined $vif_name and $vif_name eq $policy ) {
                $policy_found = 1;
                last;
            }
        }
    }

    if ($policy_found) {
        update_policy_instance( $ifname, $update_action, $name, 1 );
        return 0;
    }

    if ( $config->exists("$ifname switch-group") ) {
        if ( $config->exists("$ifname switch-group port-parameters") ) {
            my $name = $config->returnValue(
                "$ifname switch-group port-parameters policy qos");
            if ( defined $name and $name eq $policy ) {
                update_policy_instance( $ifname, $update_action, $name, 0 );
                return 0;
            }
            if (
                $config->exists(
                    "$ifname switch-group port-parameters mode access")
              )
            {
                my $vlan = $config->returnValue(
                    "$ifname switch-group port-parameters qos-parameters vlan");
                if ( defined $vlan ) {
                    my $name = $config->returnValue(
"$ifname switch-group port-parameters vlan-parameters qos-parameters vlan $vlan policy qos"
                    );
                    if ( defined $name and $name eq $policy ) {
                        update_policy_instance( $ifname, $update_action, $name,
                            0 );
                        return 0;
                    }
                }
                my $switch =
                  $config->returnValue("$ifname switch-group switch");
                $vlan = $config->returnValue(
"$ifname switch-group port-parameters vlan-parameters primary-vlan-id"
                );
                my $name = get_switch_policy( $switch, $vlan );
                if ( defined $name and $name eq $policy ) {
                    update_policy_instance( $ifname, $update_action, $name, 0 );
                    return 0;
                }
            }
        }
    }
}

# update policy - reapply because policy values changed
sub update_policy {
    my @iftypes = ( 'dataplane', 'uplink', 'vhost', 'bonding' );

    $byte_limits = get_byte_limits();

    my $pol_config = new Vyatta::Config("policy qos name");
    foreach my $policy ( $pol_config->listNodes() ) {
	if ( not $pol_config->isChanged("$policy") ) {
	    next;
	}
        foreach my $iftype (@iftypes) {
            my $config = new Vyatta::Config("interfaces $iftype");
            foreach my $ifname ( $config->listNodes() ) {
                update_installed_policies( $policy, $ifname, $config,
                    REMOVE_POLICY );
            }
            foreach my $ifname ( $config->listNodes() ) {
                update_installed_policies( $policy, $ifname, $config,
                    APPLY_POLICY );
            }
        }
    }

    return 0;
}

# We only need to worry about global profile changes
sub update_profile {
    my $global_profile_name = shift;
    my @policy_list         = ();

    # We need to find any policies that references this global profile
    my $policy_config = new Vyatta::Config('policy qos');
    return 1 unless defined($policy_config);

    return 1 if ( not $policy_config->exists("profile $global_profile_name") );

    $byte_limits = get_byte_limits();

    foreach my $policy_name ( $policy_config->listNodes('name') ) {
        my $shaper_config =
          new Vyatta::Config("policy qos name $policy_name shaper");
        if ( $shaper_config->returnValue('default') eq $global_profile_name ) {
            push @policy_list, $policy_name;
        } else {
            my @class_list = $shaper_config->listNodes('class');
            foreach my $class (@class_list) {
                my $class_profile =
                  $shaper_config->returnValue("class $class profile");
                if ( $class_profile eq $global_profile_name ) {
                    push @policy_list, $policy_name;
                    last;
                }
            }
        }
    }

    # Update any policies that use this global profile
    foreach my $policy (@policy_list) {
        update_policy($policy);
    }

    return 1;
}

sub get_switch_policy {
    my ( $switch, $vlan ) = @_;

    my $config = new Vyatta::Config("interfaces switch $switch");
    return $config->returnValue(
"default-port-parameters vlan-parameters qos-parameters vlan $vlan policy qos"
    );
}

# Using the switch root CLI apply a policy to an interface
sub apply_switch_policy {
    my ( $intf, $config ) = @_;

    if ( index( $intf->{name}, "sw" ) == 0 ) {
        switch_inherit( $intf, $config );
        return 0;
    }

    # First we check if a policy is applied directly to the dataplane
    # interface under the switch-group CLI.  This overrides any configuration
    # which may be setup under the "interf switch sw0 default-..." CLI.
    my $oldname =
      $config->returnOrigValue('switch-group port-parameters policy qos');
    my $name = $config->returnValue('switch-group port-parameters policy qos');

    if ( defined $name ) {
        if ( ( not defined $oldname or ( not $oldname eq $name ) )
            or switch_vlan_changed($intf) )
        {
            update_policy_instance( $intf->{name}, REMOVE_AND_APPLY_POLICY,
                $name, 0 );
            return 0;
        }
    } else {
        if ( defined $oldname ) {
            update_policy_instance( $intf->{name}, REMOVE_POLICY );
        }
    }

    # Now we check the default-port-params under the "inter switch" CLI,
    # an access interface can inherit a policy from the default-port-params
    # section of it.
    my $switch;
    if ( $config->exists("switch-group port-parameters mode access") ) {
        $switch = $config->returnValue("switch-group switch");
        my $vlan = $config->returnValue(
            "switch-group port-parameters vlan-parameters primary-vlan-id");
        my $policy = get_switch_policy( $switch, $vlan );
        if ( defined $policy ) {
            update_policy_instance( $intf->{name}, REMOVE_AND_APPLY_POLICY,
                $policy, 0 );
        }
    }
    return 0;
}

sub update_binding {
    my ($ifname) = @_;

    # Ignore vif interfaces.
    if ( $ifname =~ /[.]/msx ) {
        return 0;
    }

    $byte_limits = get_byte_limits();

    my $intf    = new Vyatta::Interface($ifname);
    my $config  = new Vyatta::Config( $intf->path() );
    my $oldname = $config->returnOrigValue('policy qos');
    my $name    = $config->returnValue('policy qos');

    # If we're applying an L3 policy to an interface the yang has ensured
    # there's no switch-group config.   As part of the policy install a
    # disable is passed first which will remove any existing config
    # including previously installed switch policies.
    if ( defined $name ) {
        if ( ( not defined $oldname or ( not $oldname eq $name ) )
            or vif_binding_changed($ifname) )
        {
            update_policy_instance( $ifname, REMOVE_AND_APPLY_POLICY, $name,
                1 );
            return 0;
        }
    } else {
        if ( defined $oldname ) {
            update_policy_instance( $ifname, REMOVE_POLICY );
        }
    }

    if (   $config->exists("switch-group")
        or $config->exists("default-port-parameters") )
    {
        apply_switch_policy( $intf, $config );
        return 0;
    }

    if ( $config->existsOrig("switch-group port-parameters policy qos") ) {
        update_policy_instance( $ifname, REMOVE_POLICY );
        return 0;
    }

    if ( $config->existsOrig("switch-group") ) {
        my $vlan = $config->returnOrigValue(
            "switch-group port-parameters vlan-parameters primary-vlan-id");
        if ( not defined($vlan) ) {
            return 0;
        }
        my $switch = $config->returnOrigValue("switch-group switch");
        my $swconf = new Vyatta::Config(
            "interfaces switch $switch default-port-parameters");
        if ( not defined($swconf) ) {
            return 0;
        }
        $name = $swconf->returnOrigValue(
            "vlan-parameters qos-parameters vlan $vlan policy qos");
        if ( ( defined $name ) ) {
            update_policy_instance( $ifname, REMOVE_POLICY );
        }
        return 0;
    }

    return 0;
}

sub action_group_delete {
    my ( $name, $config ) = @_;

    if ( defined($config) ) {
        $ctrl->store(
            "policy action name $name", "npf-cfg delete action-group:$name",
            "ALL",                      "DELETE"
        );
    }
}

# Each policy is passed in one after another.
# Check each match within each class to see any any have the action-group.
# Once we've found one the policy is done since it'll be re-installed.
sub act_grp_inst_pol {
    my ( $config, $policy, $name ) = @_;

    foreach my $class ( $config->listNodes("$policy shaper class") ) {
        my $parsed_cli = "$policy shaper class $class match";
        foreach my $match ( $config->listNodes("$parsed_cli") ) {
            if (    $config->exists("$parsed_cli $match action-group")
                and $config->returnValue("$parsed_cli $match action-group") eq
                $name )
            {
                update_policy($policy);
                return;
            }
        }
    }
}

sub action_group_update {
    my ( $name, $config ) = @_;

    if ( defined($config) and $config->exists("name $name") ) {

        my $act_grp = new Vyatta::Config("policy action name $name");

        # nothing to apply and it'll have been deleted if it existed
        if ( !defined($act_grp) ) {
            print "action_group_update no act_grp name $name\n";
            return;
        }

        my @rprocs = action_group_features($act_grp);
        if ( scalar @rprocs > 0 ) {
            my $rule = "rproc=" . join( ';', @rprocs ) . " ";

            $ctrl->store(
                "policy action name $name",
                "npf-cfg add action-group:$name 0 $rule",
                "ALL", "SET"
            );
        }

        # Scan all the policies to see if any have the action-group set
        my $policy_list = new Vyatta::Config("policy qos name");
        if ( !defined($policy_list) ) {
            return;
        }
        foreach my $policy ( $policy_list->listNodes() ) {
            act_grp_inst_pol( $policy_list, $policy, $name );
        }
    }
}

sub action_group {
    my ( $name, $cmd ) = @_;

    my $config = new Vyatta::Config("policy action");

    $byte_limits = get_byte_limits();

    open_ctrl();

    # Whether it's an update or a delete do a delete first
    action_group_delete( $name, $config );

    if ( $cmd eq "update" ) {
        action_group_update( $name, $config );
    }
}

sub switch_vlan_changed {
    my ($intf) = @_;
    my $level =
"$intf->{path} switch-group port-parameters vlan-parameters qos-parameters";
    my $config   = new Vyatta::Config($level);
    my @vlans    = $config->listNodes("vlan");
    my @oldvlans = $config->listOrigNodes("vlan");

    # Check for new bindings, or changes in VLAN tag
    foreach my $vlan (@vlans) {
        if ( config_same_as_before("$level vlan $vlan policy qos") ) {
            if ( defined $config->returnValue("$level vlan $vlan policy qos")
                and not config_same_as_before("$level vlan $vlan policy qos") )
            {
                return 1;
            }
        } else {
            return 1;
        }
    }

    # Check for deleted vifs which had bindings
    foreach my $oldvlan (@oldvlans) {
        return 1
          if not config_same_as_before("$level vlan $oldvlan policy qos");
    }

    return 0;
}

sub switch_inherit {
    my ( $intf, $config ) = @_;

    my $id;
    my $newconf = new Vyatta::Config();
    my $access  = $config->exists("default-port-parameters mode access");

    my @intfs = ( Vyatta::Interface::get_interfaces() );
    my %vlan_policies;
    my %vlan_policies_rm;

    # First build a list of the vlans which have changed
    foreach my $vlans (
        $config->listNodes(
            "default-port-parameters vlan-parameters qos-parameters vlan")
      )
    {
        my $oldname = $config->returnOrigValue(
"default-port-parameters vlan-parameters qos-parameters vlan $vlans policy qos"
        );
        my $name = $config->returnValue(
"default-port-parameters vlan-parameters qos-parameters vlan $vlans policy qos"
        );
        if ( defined $oldname and defined $name and $oldname eq $name ) {
            next;
        }
        if ( defined($name) ) {
            $vlan_policies{$vlans} = $name;
        } else {
            if ( defined($oldname) ) {
                $vlan_policies_rm{$vlans} = $oldname;
            }
        }
    }

    # check to make sure none have been removed
    foreach my $oldvlans (
        $config->listOrigNodes(
            "default-port-parameters vlan-parameters qos-parameters vlan")
      )
    {
        my $oldname = $config->returnOrigValue(
"default-port-parameters vlan-parameters qos-parameters vlan $oldvlans policy qos"
        );
        $vlan_policies_rm{$oldvlans} = $oldname;
    }

    # Do we have any changes ?
    if ( keys %vlan_policies == 0 and keys %vlan_policies_rm == 0 ) {
        return 0;
    }

    #
    # We only allow inheritance for the following conditions:
    #  It's a dataplane interface (name dpX)
    #  It's an access port
    #  There's no local qos policies (override)
    #  Vlan ID matches if configured
    foreach my $interface (@intfs) {
        if ( index( $interface->{name}, "dp" ) == -1 ) {
            next;
        }
        if (
            not(
                $newconf->exists(
                    "$interface->{path} switch-group switch $intf->{name}")
            )
          )
        {
            next;
        }
        if ( $newconf->exists("$interface->path() mode trunk") ) {
            next;
        }
        if (
            $newconf->exists(
                "$interface->{path} switch-group port-parameters policy qos")
          )
        {
            next;
        }
        if (
            $newconf->exists(
"$interface->{path} switch-group port-parameters vlan-parameters qos-parameters"
            )
          )
        {
            next;
        }
        $id = $newconf->returnValue(
"$interface->{path} switch-group port-parameters vlan-parameters primary-vlan-id"
        );
        if ( defined($id) ) {
            if ( defined( $vlan_policies{$id} ) ) {
                update_policy_instance( $interface->{name},
                    REMOVE_AND_APPLY_POLICY, $vlan_policies{$id}, 0 );
            } else {
                if ( defined( $vlan_policies_rm{$id} ) ) {
                    update_policy_instance( $interface->{name}, REMOVE_POLICY );
                }
            }
        }
    }

    return 0;
}

sub mark_map {
    my $map_name = shift;
    my $path     = "qos mark-map $map_name";
    my $config   = new Vyatta::Config("policy $path");

    # To QoS an if-index of zero means that this is a global object
    my $cmd = "qos 0 mark-map $map_name delete";

    open_ctrl();

    # Delete any existing entries for this remark-map
    $ctrl->store( $path, "$cmd", "ALL", "DELETE" );

    if ( defined($config) ) {
        my $dscp_bitmap = 0;
        foreach my $grp_name ( $config->listNodes('dscp-group') ) {
            my $block_hw = 0;
            my $group_config =
              new Vyatta::Config("resources group dscp-group $grp_name dscp");
            foreach my $dscp ( $group_config->returnValues() ) {

                # We might have diff-serv dscp-name e.g. af12, cs6, ef
                $dscp = str2dscp($dscp);
                if ( ( ( 1 << $dscp ) & $dscp_bitmap ) != 0 ) {
                    warn
"Multiple use of dscp-value $dscp in mark-map $map_name\n";
                    $block_hw = 1;
                } else {
                    $dscp_bitmap |= ( 1 << $dscp );
                }
            }
            if ($block_hw) {
                warn "dscp-group $grp_name not applied to hardware\n";
            } else {
                my $pcp = $config->returnValue("dscp-group $grp_name pcp-mark");
                my $cmd =
                  "qos 0 mark-map $map_name dscp-group $grp_name pcp $pcp";
                $ctrl->store( "$path dscp-group $grp_name", $cmd, "ALL",
                    "SET" );
            }
        }
    }
    return 0;
}

sub usage {
    print <<EOF;
usage:
       qos-commit --update policy-name
       qos-commit --update-binding interface
       qos-commit --update-profile profile-name
       qos-commit --action={cmd} --name={name}
       qos-commit --mark-map map-name
EOF
    exit 1;
}

my ( $updateBinding, $actioncmd, $agname, $updatePolicy, $updateProfile );
my ($markMap);

GetOptions(
    "debug"            => \$debug,
    "update-binding=s" => \$updateBinding,
    "name=s"           => \$agname,
    "action=s"         => \$actioncmd,
    "update"           => \$updatePolicy,
    "update-profile=s" => \$updateProfile,
    "mark-map=s"       => \$markMap,
) or usage();

update_binding($updateBinding) if $updateBinding;
action_group( $agname, $actioncmd ) if $actioncmd;
update_policy()                if $updatePolicy;
update_profile($updateProfile) if $updateProfile;
mark_map($markMap)             if $markMap;

undef $ctrl;
