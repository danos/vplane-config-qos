#!groovy
// Copyright (c) 2020-2021, AT&T Intellectual Property. All rights reserved.
// SPDX-License-Identifier: GPL-2.0-only

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

    // Stashykins can't clean up files if the container creates them as root.
    // Set user ID and group ID to be the as the jenkins user's IDs
    // TODO: https://stackoverflow.com/questions/44805076/setting-build-args-for-dockerfile-agent-using-a-jenkins-declarative-pipeline
    agent {
        dockerfile true
    }

    options {
        timeout(time: 180, unit: 'MINUTES') // Hopefully maximum even when Valgrind is included!
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
                stage('flake8') {
                    steps {
                            sh "invoke flake8 --commits upstream/${env.CHANGE_TARGET}...origin/${env.BRANCH_NAME}"
                    }
                }
                stage('mypy') {
                    steps {
                            sh "invoke mypy --commits upstream/${env.CHANGE_TARGET}...origin/${env.BRANCH_NAME}"
                    }
                }
                stage(' ') {
                    stages {
                        stage('pytest') {
                            steps {
                                    sh "invoke pytest"
                            }
                        }
                        stage('coverage') {
                            steps {
                                    sh "invoke coverage"
                            }
                            post {
                                always {
                                    archiveArtifacts artifacts: 'htmlcov/', fingerprint: true
                                }
                            }
                        }
                    }
                }
                stage('gitlint') {
                    steps {
                            sh "invoke gitlint --commits upstream/${env.CHANGE_TARGET}...origin/${env.BRANCH_NAME}"
                    }
                }
                stage('licence') {
                    steps {
                            sh "invoke licence --commits upstream/${env.CHANGE_TARGET}...origin/${env.BRANCH_NAME}"
                    }
                }
                stage('whitespace') {
                    steps {
                            sh "invoke whitespace --commits upstream/${env.CHANGE_TARGET}...origin/${env.BRANCH_NAME}"
                    }
                }
                stage('perlcritic') {
                    steps {
                            sh script: "perlcritic --quiet --severity 5 . 2>&1 | tee perlcritic.txt", returnStatus: true
                    }
                    post {
                        always {
                                discoverGitReferenceBuild()
                                recordIssues tool: perlCritic(pattern: 'perlcritic.txt'),
                                    enabledForFailure: true,
                                    qualityGates: [[type: 'TOTAL', threshold: 10, unstable: true]]
                        }
                    }
                }
            } // parallel
        } // Stage ' '
        // Run build after so nothing is changing whilst it is building
        stage('package') {
            steps {
                sh "invoke package"
            }
        }
    } // stages

    post {
        always {
            deleteDir()
        }
    }
}