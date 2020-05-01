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
                                python pie.py setup
                                python pie.py build
                            '''
                        }
                    }
                }

                stage('Run Testing') {
                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/shared-db-channel/")  {
                            sh '''#!/bin/bash
                                python pie.py test
                            '''
                        }
                    }

                    post {
                        always {
                            dir("${env.DOCKER_BUILD_DIR}/test/shared-db-channel/") {
                                junit 'api/tests/*.xml'
                            }
                        }
                    }

                }
            }

            post {
                cleanup {
                    dir("${env.DOCKER_BUILD_DIR}/test/shared-db-channel/") {
                        sh '''#!/bin/bash
                            python pie.py destroy
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                if ( env.BRANCH_NAME == 'master' ) {
                    build job: '../cotp-devnet/build-shared-db-channel/master', parameters: [
                        string(name: 'branchref_shareddbchannel', value: "${GIT_COMMIT}")
                    ]
                }
            }
        }

        cleanup {
            cleanWs()
        }
    }
}
