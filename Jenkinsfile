pipeline {
    agent {
        label 'docker'
    }

    environment {
        AWS_REGION = 'us-east-2'
        ECR_REGISTRY = '404268098300.dkr.ecr.us-east-2.amazonaws.com'
        PRODUCTION_HOST = '172.31.45.112'
        PRODUCTION_URL = 'https://3-17-7-24.sslip.io'
    }

    parameters {
        booleanParam(
            name: 'DEPLOY_TO_PRODUCTION',
            defaultValue: false,
            description: 'Offer production deployment after successful publication; approval is still required.'
        )
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
                archiveArtifacts(
                    artifacts: 'compose.release.yaml,scripts/deploy.sh,scripts/backup.sh,scripts/deployment_check.py'
                )
            }
        }

        stage('Approve production deployment') {
            when {
                expression { params.DEPLOY_TO_PRODUCTION }
            }
            steps {
                timeout(time: 15, unit: 'MINUTES') {
                    input message: "Deploy ${env.RELEASE_TAG} to production?", ok: 'Deploy'
                }
            }
        }

        stage('Deploy and verify production') {
            when {
                expression { params.DEPLOY_TO_PRODUCTION }
            }
            steps {
                sshagent(credentials: ['pd-production-ssh']) {
                    sh '''#!/usr/bin/env bash
set -euo pipefail
remote="ubuntu@$PRODUCTION_HOST"
directory="/opt/prisoners/releases/$RELEASE_TAG"
ssh_options=(-o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10)
rm -f reports/deployment.log

ssh "${ssh_options[@]}" "$remote" "mkdir -p '$directory/scripts'"
scp "${ssh_options[@]}" compose.release.yaml "$remote:$directory/"
scp "${ssh_options[@]}" scripts/deploy.sh scripts/backup.sh scripts/deployment_check.py \
    "$remote:$directory/scripts/"

ssh "${ssh_options[@]}" "$remote" \
    "bash '$directory/scripts/deploy.sh' '$RELEASE_TAG'" \
    2>&1 | tee reports/deployment.log

curl --fail --silent --show-error --max-time 15 \
    "$PRODUCTION_URL" --output /dev/null
'''
                }
            }
            post {
                always {
                    archiveArtifacts(
                        artifacts: 'reports/deployment.log',
                        allowEmptyArchive: true
                    )
                }
            }
        }
    }
}
