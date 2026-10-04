pipeline {
    agent {
        label 'docker'
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
    }
}
