# <a name="Configuration"></a>Configuration syntax

This section describes user visible configuration QoS commands.
By convention user defined values are in *UPPERCASE*.

Policies
-------

QoS has two configuration sub trees.

 * Policy definitions which are defined under
> set policy qos POLICYNAME shaper ...

 * Assignment of policy to interface which is done as
> set interface dataplane IFNAME qos-policy POLICYNAME

If no qos-policy is set on an interface, traffic skips the QoS processing completely and goes direct to hardware.

Bandwidth
---------
The implementation of QoS supports bandwidth restriction at multiple level of
the hierarchy: port, vlan, profile and traffic-class. The bandwidth maybe
specified as:

  * Numeric value which is interpreted as Kbits/sec
  * Number followed by suffix, for example 1.2Mbit
  * Percentage of parent hierarchy

The percentage feature works by setting the bandwidth to a percent of the
parent node. For VLAN and profile, the parent is the value configured
for the overall shaper. For a traffic-class, the parent is the profile
or vlan containing the traffic-class definition. Percent is *not*
allowed on the configuration of the base shaper class.

Queue
-----
The queue is the user abstraction of the underlying scheduling
algorithm. Queue's are identified by an integer between 0 and 7.
The Queue as exposed in the CLI do not really exist anymore in the dataplane!
Inside the dataplane there is only 4 Strict priority classes, and 4
Weighted Round Robin slots. What we expose in the CLI as queue is an
intermediate step in the mapping between packets and the SP class/WRR slot.

Each queue has the following configurable parameters:

    set policy qos NAME shaper {
	    profile NAME {
	        queue ID {
			    traffic-class TC
				weight WEIGHT
		    }
		}

  * *traffic-class* is the Strict Priority assignment.
     *  Priorities are ordered from 0 (highest priority) to 3 (lowest
        priority).
	 * Up to 4 queues can have same priority, and they will be
       serviced in round-robin fashion.
	 * The traffic-class must be set for each queue.
  * *weight* is the Weighted Round Robin value.
  This determines the proportion of bandwidth a queue will receive
  when multiple queues share same priority. It can be
  any number between 1 and 100, there is no requirement that it be percent.
  The default weight is 1.

### Restrictions ###
There can be up to 4 queue's all sharing the same traffic-class. This
is checked by the CLI during validation stage.

Internally, the configuration scripts assign a WRR slot for each
queue. Since there can be up to 4 WRR slots in the DPDK, this means
only 4 queues can share the same traffic class.

It is allowed to have an unused traffic-class (i.e. no queues
assigned). And it is OK for only one WRR slot being used.

### Default ###
If no queues are defined, the system is initialize with four
strict-priority queues.
This is for compatibility with earlier release.

 - Queue 0 -> traffic-class 3
 - Queue 1 -> traffic-class 2
 - Queue 2 -> traffic-class 1
 - Queue 3 -> traffic-class 0

Traffic-class
-------------
Traffic class nodes describe the strict priority queue.
Traffic class parameters exist at two places in the hierarchy: global
per VLAN, and per profile.

    set policy qos ...
        traffic-class TC {
		    bandwidth BW
			burst BYTES
			queue-limit PACKETS
		}


 * *bandwidth* expressed in one of the following:
     * Number and suffix
	 Some examples:
	   * 10Mbit which correspond to 10 Megabit/sec,
	   * 1 Mbps which is 8 Mbit/sec
	 * Number with no suffix is interpreted as Kbits/sec
	 * Percent of line rate
	 * *unlimited* is a special keyword meaning line rate.
 * *burst* size is the number of consecutive bytes that will be sent before
 re-evaluating the bandwidth.
 * *queue-limit* is the number of packets queued before dropping.
 Limit must be greater than 0 and a power of 2 less than 32K

The scheduler needs to take into account additional byte times added
by underlying link layer protocols. For most cases the default
Ethernet frame overhead of 22 is correct, but the value can be
configured at the top-level with:

    set policy qos NAME shaper {
	    frame-overhead 32
		...

RED
---
At the highest level traffic-class definition the optional Random
Early Detection (RED) feature can be enabled. Unless RED is enabled, all
traffic-classes are pure drop tail.

    set policy qos ...
	    traffic-class TC* {
		    random-detect {
			    filter-weight FW
				mark-probability MP
				max-threshold THRESH
				min-threshold THRESH
			}
		}

The parameters are:
 * *filter-weight* queue weight
 * *mark-probability* marking probability
 * *max-threshold*  maximum threshold for the queue (in packets)
 * *min-threshold*  minimum threshold for the queue (in packets)


Profile
-------
The profile is the description of a per customer policy. This is used
to describe different throughput groups. For example, Premium, Normal,
Guest.

     set policy qos ...
	     profile NAME {
		     bandwidth BW
			 burst SIZE
			 period INTERVAL
			 map ...
			 queue ID ...
			 traffic-class TC ...
	     }

   * *period* is the enforcement interval measured in milliseconds.

The bandwidth is required, the burst defaults to 100K bytes, and period defaults to 10ms.

Map
---

Packets are mapped to queues based on either 802.1p priority (if present)
or DSCP (for IPv4/IPv6). For each profile there is a table mapping all
possible PCP and DSCP to queue. For PCP the default mapping is such
that highest priority 802.1p value corresponds to highest priority
traffic class. The default DSCP to queue mapping is based on the
highest order bits (2 bits) since by default there are four priority
queues.

When DSCP is specified in CLI, it can be either numeric, symbolic or a range.
The numeric form is standard POSIX input method: a decimal number, hex
number preceded by 0x. The symbolic names are matched (case
independent) with those values in the system file
_/etc/iproute/rt_dsfield_. Lists can be comma separated items or a
range with minus sign.

    set policy qos ...
	    profile NAME {
                map {
                        dscp 5-8 {
                                to 3
                        }
                        dscp 10,11-13 {
                                to 1
                        }
                        dscp af21 {
                                to 2
                        }
                }
        }




Priority code point mapping takes precedence over DSCP. In other
words, DSCP is only evaluated for untagged or PCP=0. Non IP traffic is
treated as best effort (DSCP 0).

    set policy qos ...
	    profile NAME {
		    map dscp DSCP to QUEUE
			map pcp PCP to QUEUE
			...

ACL
---

The QoS classification uses a subset of the *NPF* base classification
that is also used in *PBR* and firewall. The classification allows
matching based on source and destination values for IP and MAC
addresses as well as *DSCP* and *PCP* values. The result of the
classification process assigns an class to the packet.

Classes are identified by one or match rules based on subset of firewall
syntax. For example

    set policy qos ...
         class 1 {
             match HTTP-IN {
                 protocol tcp
                 source {
                     port http
                 }
             }
             match HTTP-OUT {
                 destination {
                     port http
                 }
                 protocol tcp
             }
             profile PROFILE1
         }
         class 2 {
             drop
             match 1 {
                 fragment
             }
         }

Classes are evaluated in numerical order. The first class that matches
is used (i.e. they are final). The class numbers do not have to be
sequential (it is okay to have gaps) but the largest class number
determines the size of internal data structures, therefore using large
numbers is discouraged.
Even though classes look like firewall rules, they are not stateful.
Each class is either associated with an action which can either be a
QoS scheduling profile or drop.

### Remarking ###
The ACL may also include rules to remark a packet by changing the DSCP
or PCP values. Any changes that are made during the classification
process occur before the packet is evaluated for scheduling. For
example, if the QoS scheduler has a rule to set all packets DSCP to 0,
then all packets will go the the lowest priority queue (7).

Policing
--------
In a class there may also be policing restrictions. These restrictions
are used to drop or remark packets that go over a preset bandwidth
value.

In this example, traffic that matches DSCP 40 (decimal) and exceeds
1 Megabits/sec will be remarked to DSCP 0

    set policy qos ...
         class 1 {
             match REALTIME {
                 dscp 40
				 police {
				     bandwidth 1Mbit
					 then {
					     mark {
						     dscp 0
						 }
					 }
				}
			...

Policing happens as the first post processing step of the ACL
matching. Therefore if you have normal remarking and over-bandwidth
remarking it will work as expected; normal traffic will get remarked
to the normal remark value and over bandwidth traffic will get
remarked to that value.

ACL rule processing, policing and remarking take place before the
QoS classification that happens where DSCP (and PCP) are used to
assign a packet to a queue and then to a traffic-class.


VLAN
----

The QoS scheduler also can have per VLAN semantics. If a VLAN
subsection is defined in the CLI, then all packets matching that VLAN
tag are evaluated according to that set of classification and
scheduling policies. Untagged packets and packets that do not have a
VLAN tag are evaluated according to default outer rules

    set policy qos NAME shaper {
       vlan TAG {
	       class N {
		      destination address ADDR
			  profile VLAN1
		   }
		}
    ...

Profiles are only defined in the outer (non VLAN) portion but
can be referenced from either subsection.

Example
-------
These are a customer based examples.
First for configuring four traffic classes:

    policy {
         qos ATT1 {
             shaper {
                 default CE_QUEUE
                 description "AT&T VCE example"
                 profile CE_QUEUE {
                     bandwidth 1Gbit
                     map {
                         dscp 24-24 {
                             to 1
                         }
                         dscp 40,46 {
                             to 0
                         }
                     }
                     queue 0 {
                         description COS1
                         traffic-class 0
                     }
                     queue 1 {
                         description COS2
                         traffic-class 3
                         weight 60
                     }
                     queue 2 {
                         description COS3
                         traffic-class 3
                         weight 30
                     }
                     queue 3 {
                         description COS4
                         traffic-class 3
                         weight 10
                     }
                 }
                 traffic-class 0 {
                     bandwidth 593971
                     description "Highest priority"
                 }
                 traffic-class 3 {
                     description "Best effort"
                     bandwidth 395981
                 }
             }
         }
    }

More complex one with multiple matches and classes see [Appendix](#Appendix)

## Configuration hierarchy ##

