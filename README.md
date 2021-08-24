# Overview

This package has the Vyatta configuration and operational templates and scripts for dataplane Qos.

# Environment
## Dependencies
This repository contains 3 types of dependencies.
**Debian build packaging dependencies**: 
Needed on the host machine to package the scripts into .deb files.
Located in the [debian control file](debian/control) under the `Build-Depends:` section.
**Developer dependencies**:
Needed on the host machine to run quality checks on the source code.
Located in the [requirements file](dev-requirements.txt).
**Debian deployed dependencies**:
Needed on the target machine.
Located in the [debian control file](debian/control) under the packages `Depends:` section.

## Container
A containerized environment is provided with all the host dependencies installed.

The [Dockerfile](Dockerfile) gives docker instructions on how to create an image with all the necessary dependencies. 

(// TODO: Would it be better to replace this with docker compose?)
1. Change directory to the top of the project directory where the dockerfile exists
2. Build the image and tag it
```
docker image build --tag vplane-config-qos . 
```
3. Build the container from the image and start the bash shell
```
docker run --interactive --tty --mount type=bind,src=${PWD},dst=/tmp/vplane-config-qos --user $(id -u):$(id -g) --rm vplane-config-qos
```
* `--interactive`: Keep STDIN open even if not attached
* `--tty`: Allocate a pseudo-TTY
* `--mount`: Attach a filesystem mount to the container. Lets container access the repository.
  * `type=bind`:   
  * `src=${PWD}`: Mount current working directory on the host
  *  `dst=/tmp/vplane-config-qos`: Directory to mount in the container.
* `--user $(id -u):$(id -g)`: Make container use the same UID & GID as the host to stop the container creating files with root as the owner.
* `--rm`: Automatically clean up the container and remove the file system when the container exits.
* `vplane-config-qos` The name of the image created in step 2

# Tasks
This project uses [Invoke](http://www.pyinvoke.org/) as a task runner. From the root of the project directory type `invoke --list` to see a list of tasks.

Most checks can either check all files or just the changed files. The changed files are determined by using git to compare branches. By default most checks will compare the current branch to master. 
  
Run Flake8 over files changed between current branch and master  
`invoke flake8`  
Run Flake8 over all files  
`invoke flake8 --commits all`  
Run Flake8 over files changed between arbitrary commits or references  
`invoke flake8 --commits master-next...master`  

When opening a pull request you should ensure all stages are successful. 

# Packaging
Run `invoke package`.  
The generated Debian packages will be generated in the child directory "deb_packages".
Copy them to a system running DANOS and install them.



