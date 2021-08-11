FROM ubuntu:20.04
USER root

# Prevent apt from asking the user questions like what time zone
ARG DEBIAN_FRONTEND=noninteractive 

# Add Vyatta Repositories
# Having problems resolving build.eng.vyatta.net so hard coded in the IP address.
# TODO: Consider finding a better fix
RUN echo 'deb [trusted=yes] http://10.156.50.45:82/Vyatta:/Tools/xUbuntu_20.04/ ./' >> /etc/apt/sources.list
RUN apt update --yes

# Install mk-build-deps program
RUN apt install --yes devscripts equivs

# Only copy the debian control file as it describes the projects dependencies
COPY ./debian/control /tmp/vplane-config-qos/debian/control
WORKDIR /tmp/vplane-config-qos

# Install application dependencies
RUN mk-build-deps \
 && apt install --yes --fix-missing ./vplane-config-qos-build-deps_*_all.deb

# Jenkins mounts the directory at /var/lib/jenkins/workspace/DANOS_vplane-config-qos_PR-XXX
# Non root users do not have write permissions in /var so cannot write above the mounted directory
# dpkg-buildpackage deposits debs (and temp files) in the parent directory
# Currently there is no way to specify a different directory (https://groups.google.com/g/linux.debian.bugs.dist/c/1KiGKfuFH3Y)
RUN mkdir -p /var/lib/jenkins/workspace/ \
 && chmod -R a+w /var/lib/jenkins/workspace/