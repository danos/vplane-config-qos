README-python-tests.txt
=======================
The python scripts (tests_*.py) in this directory (VR/vplane_config_qos/tests)
are the unit-tests for the VR/vplane_config_qos/vyatta_policy_qos_vci/*.py
python scripts that convert the QoS configuration from JSON to Vyatta Dataplane
QoS configuration commands.

These unit-tests are run automatically everytime vplane_config_qos is built.

You can run these unit-tests by hand by invoking pytest-3 (which you may need
to install on your laptop using "sudo apt-get install python3-pytest") from your
vplane_config_qos directory as shown below:

$ cd ~/stash-repos/vplane_config_qos
$
$ ls
AUTHORS       debian       platform      tests
cfg-version   doc          README        vyatta
configure.ac  lib          scripts       vyatta_policy_qos_vci
COPYING       Makefile.am  templates-op  yang
$
$ pytest-3
======================== test session starts =========================
platform linux -- Python 3.6.8, pytest-3.3.2, py-1.5.2, pluggy-0.6.0
rootdir: /home/adewar/stash-repos/vplane-config-qos, inifile:
collected 25 items

tests/test_action.py .                                         [  4%]
tests/test_bandwidth.py .                                      [  8%]
tests/test_dscp.py .                                           [ 12%]
tests/test_ingress_map.py .                                    [ 16%]
tests/test_interface.py .                                      [ 20%]
tests/test_mark_map.py .                                       [ 24%]
tests/test_pipe_queue.py .                                     [ 28%]
tests/test_policer.py ...                                      [ 40%]
tests/test_policy.py .                                         [ 44%]
tests/test_profile.py .                                        [ 48%]
tests/test_provisioner.py .                                    [ 52%]
tests/test_qclass.py .                                         [ 56%]
tests/test_qos_config.py .                                     [ 60%]
tests/test_qos_op_mode.py .                                    [ 64%]
tests/test_queue.py .                                          [ 68%]
tests/test_rule.py .                                           [ 72%]
tests/test_shaper.py .                                         [ 76%]
tests/test_subport.py .                                        [ 80%]
tests/test_traffic_class.py .                                  [ 84%]
tests/test_traffic_class_block.py .                            [ 88%]
tests/test_wred.py .                                           [ 92%]
tests/test_wred_dscp_group.py ..                               [100%]

===================== 25 passed in 0.11 seconds ======================


You can also run each test individually like so:

$ pytest-3 tests/test_action.py
======================== test session starts =========================
platform linux -- Python 3.6.8, pytest-3.3.2, py-1.5.2, pluggy-0.6.0
rootdir: /home/adewar/stash-repos/vplane-config-qos, inifile:
collected 1 item

tests/test_action.py .                                         [100%]

====================== 1 passed in 0.01 seconds ======================
$
