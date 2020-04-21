#!groovy

// Testing pipeline

pipeline {
    agent {
        label 'hamlet-latest'
    }
    options {
        timestamps ()
        buildDiscarder(
            logRotator(
                numToKeepStr: '10'
            )
        )
        disableConcurrentBuilds()
        durabilityHint('PERFORMANCE_OPTIMIZED')
        parallelsAlwaysFailFast()
        skipDefaultCheckout()
    }

    environment {
        DOCKER_BUILD_DIR = "${env.DOCKER_STAGE_DIR}/${BUILD_TAG}"
    }

    parameters {
        booleanParam(
            name: 'all_tests',
            defaultValue: false,
            description: 'Run tests for all components'
        )
    }

    stages {
        // intergov required for running full test suite
        stage('Testing') {

            when {
                anyOf {
                    changeRequest()
                    equals expected: true, actual: params.all_tests
                }
            }


            stages {
                stage('Setup') {
                    when {
                        changeRequest()
                    }

                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/shared-db-channel/") {

                            checkout scm

                            sh '''#!/bin/bash
                                docker-compose build
                                docker-compose up -d
                            '''
                        }
                    }
                }

                stage('Run Testing') {
                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/shared-db-channel/")  {
                            sh '''#!/bin/bash
                                docker-compose run api pytest
                            '''
                        }
                    }

                }
            }

            post {
                cleanup {
                    dir("${env.DOCKER_BUILD_DIR}/test/shared-db-channel/") {
                        sh '''#!/bin/bash
                            if [[ -f docker-compose.yml ]]; then
                                docker-compose down --rmi local -v --remove-orphans
                            fi
                        '''
                    }
                }
            }
        }
    }

    post {
        cleanup {
            cleanWs()
        }
    }
}
