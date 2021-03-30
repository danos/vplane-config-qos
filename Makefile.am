opdir = $(datadir)/vyatta-op/templates
share_perl5dir = /opt/vyatta/share/perl5/Vyatta/QoS
yangdir = /usr/share/configd/yang
testdir = /usr/share/Qos/tests

cpiop = find  . ! -regex '\(.*~\|.*\.bak\|.*\.swp\|.*\#.*\#\)' -print0 | \
	cpio -0pd

sbin_SCRIPTS = scripts/qos-validate.pl

bin_SCRIPTS = scripts/show-ext-buf.pl
bin_SCRIPTS += scripts/show-queueing.pl
bin_SCRIPTS += scripts/qos-op-mode.pl
bin_SCRIPTS += scripts/qos-clear-counters.pl
bin_SCRIPTS += scripts/show_gpc_rpc.py

share_perl5_DATA = lib/Vyatta/QoS/Shaper.pm
share_perl5_DATA += lib/Vyatta/QoS/Subport.pm
share_perl5_DATA += lib/Vyatta/QoS/Profile.pm
share_perl5_DATA += lib/Vyatta/QoS/Class.pm
share_perl5_DATA += lib/Vyatta/QoS/Queue.pm
share_perl5_DATA += lib/Vyatta/QoS/Bandwidth.pm
share_perl5_DATA += lib/Vyatta/QoS/TrafficClass.pm
share_perl5_DATA += lib/Vyatta/QoS/Red.pm
share_perl5_DATA += lib/Vyatta/QoS/Debug.pm
share_perl5_DATA += lib/Vyatta/QoS/Policy.pm

qos_TESTS = tests/action-group.sh
qos_TESTS += tests/perQwred-tests.sh
qos_TESTS += tests/perQwred-test1
qos_TESTS += tests/perQwred-test2
qos_TESTS += tests/perQwred-test3
qos_TESTS += tests/perQwred-test4
qos_TESTS += tests/perQwred-test5
qos_TESTS += tests/perQwred-test6
qos_TESTS += tests/QinQ-tests.sh
qos_TESTS += tests/QinQmark-test1
qos_TESTS += tests/QinQmark-test2
qos_TESTS += tests/QinQmark-test3
qos_TESTS += tests/QinQmark-test4
qos_TESTS += tests/QinQmark-test5
qos_TESTS += tests/QinQmark-test6
qos_TESTS += tests/QinQmark-test8
qos_TESTS += tests/QinQmark-test7
qos_TESTS += tests/QinQmark-test9
qos_TESTS += tests/po-policy-tests.sh
qos_TESTS += tests/po-ag-tests.sh
qos_TESTS += tests/po-firewall-tests.sh
qos_TESTS += tests/po-tests.sh
qos_TESTS += tests/ag-test4
qos_TESTS += tests/ag-test5
qos_TESTS += tests/ag-test6
qos_TESTS += tests/ag-test7
qos_TESTS += tests/qos-netconf-test.py
qos_TESTS += tests/README
qos_TESTS += tests/policer-tc.sh
qos_TESTS += tests/policer-tc-test1
qos_TESTS += tests/policer-tc-test2
qos_TESTS += tests/policer-tc-test3
qos_TESTS += tests/switch-test1
qos_TESTS += tests/switch-test2
qos_TESTS += tests/switch-test3
qos_TESTS += tests/switch-test4

install-exec-hook:
	mkdir -p $(DESTDIR)$(opdir)
	cd templates-op; $(cpiop) $(DESTDIR)$(opdir)
	mkdir -p $(DESTDIR)$(yangdir)
	cd yang && $(cpiop) $(DESTDIR)$(yangdir)
	mkdir -p $(DESTDIR)$(testdir)
	cd tests && $(cpiop) $(DESTDIR)$(testdir)
