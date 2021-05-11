# <a name="Operation"></a> Operational commands

The QoS package supports displaying statistics and mapping of packets
to queues.

##  Statistics ##
The QoS scheduler keeps track of number of packets and bytes that pass through.
These statistics are displayed under:
> show queueing

These can be displayed for all devices:

    $ show queueing

Or on a per interface basis with more detail:

    $ show queueing dp0p2p1

To see per vlan information

    $ show queueing dp0p2p1.100

## Priority maps ##
The individual DSCP maps can be displayed:

    $ show queuing dp0p2p1 map dscp

And the 802.1p priority code point map:

    $ show queuing dp0p2p1 map pcp

## Operational command hierarchy ##

