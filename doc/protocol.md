QoS Protocol
============

This section describes the interface from the QoS perl script to the
dataplane (via vplane controller). It is not a stable API, it maybe
changed at anytime as long as both CLI and dataplane are updated.
The script interacts with controller by sending commands over the ZMQ
Request channel.

Config
------

### qos IFINDEX port ###

### qos IFINDEX queue ###

### qos IFINDEX subport ###

### qos IFINDEX pipe ###

### qos IFINDEX profile ###

### qos IFINDEX match SUBPORT CLASS RULE ###
Create a new class on subport using NPF rule string.
Adds new rule to the configuration.

### qos IFINDEX disable ###
Turn off QoS on an interface, goes back to pass through mode.

### qos IFINDEX enable ###
Turn on QoS on interface. Last command after all configuration is done

Operational
-----------
These are done directly from script to dataplane.

### qos show ###
Produce statistics (in JSON) for all interfaces.

### qos show INTERFACE ###
Produce statistics (in JSON) for a given interface
