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
        quietPeriod 60
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
        stage('Setup') {
            steps {
                dir("${env.DOCKER_BUILD_DIR}/test/shared-db-channel/") {
                    script {
                        def repoSharedDb = checkout scm
                        env["GIT_COMMIT"] = repoSharedDb.GIT_COMMIT
                    }
                }
            }
        }

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
                                echo Starting Shared DB
                                export COMPOSE_PROJECT_NAME=au_sg_channel
                                python3 pie.py shared_db.destroy
                                python3 pie.py shared_db.start
                                
                                echo Starting API
                                export COMPOSE_PROJECT_NAME=au_sg_channel_au_endpoint
                                python3 pie.py api.build
                                python3 pie.py api.upgrade_db_schema
                                python3 pie.py api.start
                            '''
                        }
                    }
                }

                stage('Run Testing') {
                    steps {
                        dir("${env.DOCKER_BUILD_DIR}/test/shared-db-channel/")  {
                            sh '''#!/bin/bash
                                export COMPOSE_PROJECT_NAME=au_sg_channel_au_endpoint
                                python3 pie.py api.test
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
                            export COMPOSE_PROJECT_NAME=au_sg_channel
                            python3 pie.py shared_db.destroy
                            export COMPOSE_PROJECT_NAME=au_sg_channel_au_endpoint
                            python3 pie.py api.destroy
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
