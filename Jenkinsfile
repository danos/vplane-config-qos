#!groovy

/*
 * Copyright (c) 2020-2021, AT&T Intellectual Property.
 * All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-only
 */

/* SRC_DIR is where the project will be checked out,
 * and where all the steps will be run.
 */
def SRC_DIR="vplane-config-qos"

// Pull Request builds might fail due to missing diffs: https://issues.jenkins-ci.org/browse/JENKINS-45997
// Pull Request builds relationship to their targets branch: https://issues.jenkins-ci.org/browse/JENKINS-37491

@NonCPS
def cancelPreviousBuilds() {
    def jobName = env.JOB_NAME
    def buildNumber = env.BUILD_NUMBER.toInteger()
    /* Get job name */
    def currentJob = Jenkins.instance.getItemByFullName(jobName)

    /* Iterating over the builds for specific job */
    for (def build : currentJob.builds) {
        /* If there is a build that is currently running and it's not current build */
        if (build.isBuilding() && build.number.toInteger() != buildNumber) {
            /* Than stopping it */
            build.doStop()
        }
    }
}

pipeline {
    agent any

    environment {
        OBS_INSTANCE = 'build-release'
        OBS_TARGET_PROJECT = 'Vyatta:Unstable'
        OBS_TARGET_REPO = 'standard'
        OBS_TARGET_ARCH = 'x86_64'
        // # Replace : with _ in project name, as osc-buildpkg does
        OSC_BUILD_ROOT = "${WORKSPACE}" + '/build-root/' + "${env.OBS_TARGET_PROJECT.replace(':','_')}" + '-' + "${env.OBS_TARGET_REPO}" + '-' + "${OBS_TARGET_ARCH}"
        DH_VERBOSE = 1
        DH_QUIET = 0
        DEB_BUILD_OPTIONS = 'verbose'

        // CHANGE_TARGET is set for PRs.
        // When CHANGE_TARGET is not set it's a regular build so we use BRANCH_NAME.
        REF_BRANCH = "${env.CHANGE_TARGET != null ? env.CHANGE_TARGET : env.BRANCH_NAME}"
        SRC_DIR = "${SRC_DIR}"
    }

    options {
        timeout(time: 180, unit: 'MINUTES') // Hopefully maximum even when Valgrind is included!
        checkoutToSubdirectory("${SRC_DIR}")
        quietPeriod(30) // Wait in case there are more SCM pushes/PR merges coming
        ansiColor('xterm')
        timestamps()
    }

    stages {

        // A work around, until this feature is implemented: https://issues.jenkins-ci.org/browse/JENKINS-47503
        stage('Cancel older builds') { steps { script {
            cancelPreviousBuilds()
        }}}

        stage(' ') {
            parallel {
                stage('OSC') {
                    stages {
                        stage('OSC config') {
                            steps {
                                sh 'printenv'
                                // Build scripts with tasks to perform in the chroot
                                sh """
cat <<EOF > osc-buildpackage_buildscript_default
export BUILD_ID=\"${BUILD_ID}\"
export JENKINS_NODE_COOKIE=\"${JENKINS_NODE_COOKIE}\"
dpkg-buildpackage -jauto -us -uc -b
EOF
"""
                            }
                        }

                        // Workspace specific chroot location used instead of /var/tmp
                        // Allows parallel builds between jobs, but not between stages in a single job
                        // TODO: Enhance osc-buildpkg to support parallel builds from the same pkg_srcdir
                        // TODO: probably by allowing it to accept a .conf file from a location other than pkg_srcdir

                        stage('OSC Build') {
                            steps {
                                dir("${SRC_DIR}") {
                                    sh """
cat <<EOF > .osc-buildpackage.conf
OSC_BUILDPACKAGE_TMP=\"${WORKSPACE}\"
OSC_BUILDPACKAGE_BUILDSCRIPT=\"${WORKSPACE}/osc-buildpackage_buildscript_default\"
EOF
"""
                                    sh "osc-buildpkg -v -A ${env.OBS_INSTANCE} -g -T -P ${env.OBS_TARGET_PROJECT} ${env.OBS_TARGET_REPO} -- --trust-all-projects --build-uid='caller'"
                                }
                            }
                        }
                    } // stages
                } // stage OSC
                stage('flake8') {
                    steps {
                        dir("${SRC_DIR}") {
                               sh "invoke flake8 --commits upstream/${env.CHANGE_TARGET}...origin/${env.BRANCH_NAME}"
                        }
                    }
                }
                stage('mypy') {
                    steps {
                        dir("${SRC_DIR}") {
                            sh "invoke mypy --commits upstream/${env.CHANGE_TARGET}...origin/${env.BRANCH_NAME}"
                        }
                    }
                }
                stage(' ') {
                    stages {
                        stage('pytest') {
                            steps {
                                dir("${SRC_DIR}") {
                                    sh "invoke pytest"
                                }
                            }
                        }
                        stage('coverage') {
                            steps {
                                dir("${SRC_DIR}") {
                                    sh "invoke coverage"
                                }
                                //TODO: Archive htmlcov directory
                            }
                        }
                    }
                }
                stage('gitlint') {
                    steps {
                        dir("${SRC_DIR}") {
                            sh "invoke gitlint --commits upstream/${env.CHANGE_TARGET}...origin/${env.BRANCH_NAME}"
                        }
                    }
                }
                stage('licence') {
                    steps {
                        dir("${SRC_DIR}") {
                            sh "invoke licence --commits upstream/${env.CHANGE_TARGET}...origin/${env.BRANCH_NAME}"
                        }
                    }
                }
                stage('yang') {
                    steps {
                        dir("${SRC_DIR}") {
                            sh "invoke yang --commits upstream/${env.CHANGE_TARGET}...origin/${env.BRANCH_NAME}"
                               
                        }
                    }
                }
                stage('perlcritic') {
                    steps {
                        dir("${SRC_DIR}") {
                            sh script: "perlcritic --quiet --severity 5 . 2>&1 | tee perlcritic.txt", returnStatus: true
                        }
                    }
                    post {
                        always {
                            dir("${env.SRC_DIR}") {
                                discoverGitReferenceBuild()
                                recordIssues tool: perlCritic(pattern: 'perlcritic.txt'),
                                    enabledForFailure: true,
                                    qualityGates: [[type: 'TOTAL', threshold: 10, unstable: true]]
                            }
                        }
                    }
                }
            } // parallel
        } // Run tests
    } // stages

    post {
        always {
            sh 'rm -f *.deb' // top-level dir
            sh "osc chroot --wipe --force --root ${env.OSC_BUILD_ROOT}"
            deleteDir()
        }
        success {
            echo 'Winning'
        }
        failure {
            echo 'Argh... something went wrong'
            emailext (
                subject: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                body: """<p>FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</p>
                         <p>Check console output at "<a href="${env.BUILD_URL}">${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>"</p>""",
                recipientProviders: [culprits()]
            )
        }
    }
}