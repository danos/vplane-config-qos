FROM debian:11
USER root

# Set working dir where files describing dependencies will be copied to
# and where the shared drive should be mounted when docker run is executed
WORKDIR /tmp/vplane-config-qos

# Prevent apt from asking the user questions like which time zone
ARG DEBIAN_FRONTEND=noninteractive

# Add Vyatta tools repository
RUN apt-get update --yes && \
    apt-get install --yes wget gnupg2 && \
    wget -q -O- http://repos.eng.vyatta.net/Vyatta:/Tools/Debian11/Release.key | apt-key add - && \
    echo 'deb http://repos.eng.vyatta.net/Vyatta:/Tools/Debian11/ ./' >> /etc/apt/sources.list && \
    apt-get update --yes

#-----Debian build/packaging dependencies------
# Install mk-build-deps program
RUN apt-get install --yes devscripts equivs

# Only copy the debian control file as it describes the projects build/packaging dependencies
COPY ./debian/control /tmp/vplane-config-qos/debian/control

# Install application's build/packaging dependencies
RUN mk-build-deps --install --remove --tool='apt-get --yes'

# Install vyatta configuration for debian lintian tool
RUN apt-get install --yes --fix-missing lintian-profile-vyatta
#------------------------------------------------

#-----------Pip development dependencies---------
COPY ./dev-requirements.txt /tmp/vplane-config-qos/dev-requirements.txt
RUN apt-get update --yes && \
    apt-get install --yes python3-pip && \
    pip3 install --requirement dev-requirements.txt
#------------------------------------------------

# Jenkins mounts the directory at /var/lib/jenkins/workspace/DANOS_vplane-config-qos_PR-XXX
# Non root users do not have write permissions in /var so cannot write above the mounted directory
# dpkg-buildpackage deposits debs (and temp files) in the parent directory
# Currently there is no way to specify a different directory (https://groups.google.com/g/linux.debian.bugs.dist/c/1KiGKfuFH3Y)
RUN mkdir -p /var/lib/jenkins/workspace/ \
 && chmod -R a+w /var/lib/jenkins/workspace/

# Add sudo permissions
RUN apt-get install --yes sudo
RUN useradd docker && echo "docker:docker" | chpasswd && adduser docker sudo