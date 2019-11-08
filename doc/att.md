# <a name="Appendix"></a>Large sample configuration

This is a much more complex example, with: RED,
per class limits; multiple matches per class;
remarking of DSCP values; and dropping of fragments. It mostly matches
example from AT&T but is missing policing.

    policy qos ATT2 {
        shaper {
            class 1 {
                description "Discard all fragments"
                drop
                match 1 {
                    fragment
                }
            }
            class 2 {
                description CLASS_DSCP48
                match 1 {
                    destination {
                        port bgp
                    }
                    mark {
                        dscp 48
                    }
                    protocol tcp
                }
                match 2 {
                    mark {
                        dscp 48
                    }
                    protocol tcp
                    source {
                        port bgp
                    }
                }
                profile NMC
            }
            class 3 {
                description CLASS_DSCP49
                match 1 {
                    destination {
                        port ntp
                    }
                    mark {
                        dscp 49
                    }
                    protocol udp
                }
                match 2 {
                    mark {
                        dscp 49
                    }
                    protocol udp
                    source {
                        port ntp
                    }
                }
                profile NMC
            }
            class 4 {
                description TACACS
                match 1 {
                    mark {
                        dscp 50
                    }
                    protocol udp
                    source {
                        port tacacs
                    }
                }
                match 2 {
                    destination {
                        port tacacs
                    }
                    mark {
                        dscp 50
                    }
                    protocol udp
                }
                match 3 {
                    mark {
                        dscp 50
                    }
                    protocol tcp
                    source {
                        port tacacs
                    }
                }
                match 4 {
                    destination {
                        port tacacs
                    }
                    mark {
                        dscp 50
                    }
                    protocol tcp
                }
                profile NMC
            }
            class 5 {
                description "TELNET - SSH"
                match 1 {
                    destination {
                        port telnet
                    }
                    mark {
                        dscp 51
                    }
                    protocol tcp
                }
                match 2 {
                    mark {
                        dscp 51
                    }
                    protocol tcp
                    source {
                        port telnet
                    }
                }
                match 3 {
                    destination {
                        port ssh
                    }
                    mark {
                        dscp 51
                    }
                    protocol tcp_udp
                }
                match 4 {
                    mark {
                        dscp 51
                    }
                    protocol tcp_udp
                    source {
                        port ssh
                    }
                }
                profile NMC
            }
            class 6 {
                description SNMP
                match in {
                    destination {
                        port snmp
                    }
                    mark {
                        dscp 52
                    }
                    protocol udp
                }
                match out {
                    mark {
                        dscp 52
                    }
                    protocol udp
                    source {
                        port snmp
                    }
                }
                match trap-in {
                    destination {
                        port snmptrap
                    }
                    mark {
                        dscp 52
                    }
                    protocol udp
                }
                match trap-out {
                    mark {
                        dscp 52
                    }
                    protocol udp
                    source {
                        port snmptrap
                    }
                }
                profile NMC
            }
            class 7 {
                description ICMP
                match ICMP {
                    mark {
                        dscp 53
                    }
                    protocol icmp
                }
                profile NMC
            }
            class 8 {
                description "IPSEC and GRE"
                match 1 {
                    destination {
                        port isakmp
                    }
                    mark {
                        dscp 56
                    }
                    protocol udp
                }
                match 2 {
                    destination {
                    }
                    mark {
                        dscp 56
                    }
                    protocol udp
                    source {
                        port isakmp
                    }
                }
                match 3 {
                    dscp 48
                    mark {
                        dscp 56
                    }
                    protocol gre
                }
                profile NMC
            }
            class 9 {
                description TFTP
                match in {
                    destination {
                        port tftp
                    }
                    mark {
                        dscp 55
                    }
                    protocol udp
                }
                match out {
                    protocol udp
                    source {
                        port tftp
                    }
                }
                profile NMC
            }
            class 10 {
                bandwidth-limit 3Mbit {
                }
                description COS1
                match in {
                    destination {
                        port 2081
                    }
                    mark {
                        dscp 46
                    }
                    protocol udp
                }
                match out {
                    mark {
                        dscp 46
                    }
                    protocol udp
                    source {
                        port 2081
                    }
                }
                profile COS1
            }
            default DEFAULT
            profile COS1 {
                bandwidth 3Mbit
                burst 375000
                map {
                    dscp 46 {
                        to 1
                    }
                }
            }
            profile COS4_APP {
                bandwidth 1496
                burst 187000
            }
            profile DEFAULT {
                bandwidth 49472
                burst 197888
            }
            profile NMC {
                bandwidth 16000
                burst 8000
                map {
                    dscp 48-56 {
                        to 0
                    }
                }
            }
            traffic-class 0 {
                bandwidth 10Mbit
                description "NMC Traffic"
                queue-limit 512
                random-detect {
                    filter-weight 1
                    mark-probability 10
                    max-threshold 300
                    min-threshold 250
                }
            }
            traffic-class 1 {
                bandwidth 30Mbit
                burst 3750000
                description COS1
                queue-limit 2048
            }
            traffic-class 2 {
                bandwidth 59Mbit
                queue-limit 2048
                random-detect {
                    max-threshold 1023
                    min-threshold 820
                }
            }
            traffic-class 3 {
                bandwidth 39Mbit
                description "Lowest priority"
                queue-limit 2048
                random-detect {
                    max-threshold 720
                    min-threshold 540
                }
            }
        }
    }
