pipeline {
    agent {
        label 'docker'
    }

    environment {
        AWS_REGION = 'us-east-2'
        ECR_REGISTRY = '404268098300.dkr.ecr.us-east-2.amazonaws.com'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('CI checks') {
            steps {
                sh './scripts/ci.sh'
            }
            post {
                always {
                    junit(
                        testResults: 'reports/backend.xml',
                        allowEmptyResults: true
                    )
                    archiveArtifacts(
                        artifacts: 'reports/*.log',
                        allowEmptyArchive: true
                    )
                }
            }
        }

        stage('Build release images') {
            steps {
                script {
                    def commit = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()
                    env.RELEASE_TAG = "${commit}-${env.BUILD_NUMBER}"
                }
                sh '''
                    set -eu
                    docker build --target runtime \
                        --tag "$ECR_REGISTRY/prisoners-api:$RELEASE_TAG" \
                        ./backend
                    docker build --target runtime \
                        --tag "$ECR_REGISTRY/prisoners-frontend:$RELEASE_TAG" \
                        ./frontend
                '''
            }
        }

        stage('Publish images to ECR') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
set +x
export DOCKER_CONFIG="$(mktemp -d)"
trap 'rm -rf -- "$DOCKER_CONFIG"' EXIT

aws ecr get-login-password --region "$AWS_REGION" |
    docker login --username AWS --password-stdin "$ECR_REGISTRY"

docker push "$ECR_REGISTRY/prisoners-api:$RELEASE_TAG"
docker push "$ECR_REGISTRY/prisoners-frontend:$RELEASE_TAG"

printf 'Published release: %s\\n' "$RELEASE_TAG"
'''
            }
        }
    }
}
