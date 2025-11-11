pipeline {
    agent any

    environment {
        PROJECT_ID = 'courseproject-473823'
        CLUSTER_NAME = 'hadoop-cluster'
        REGION = 'us-central1'
        GCS_BUCKET = 'hadoop-cluster-gcs'
        SONARQUBE_URL = 'http://34.70.75.17:9000'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from repository...'
                checkout scm
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    echo 'Running SonarQube analysis...'

                    withSonarQubeEnv('SonarQube') {
                        script {
                            def scannerHome = tool 'sonar-scanner' 
                            sh """
                            ${scannerHome}/bin/sonar-scanner \
                                -Dsonar.projectKey=python-code-disasters \
                                -Dsonar.sources=. \
                                -Dsonar.python.version=3.8,3.9,3.10
                            """
                        }
                    }
                }
            }
        }

        stage('Check for Blockers') {
            steps {
                script {
                    echo 'Checking SonarQube for blocker issues...'
                    sleep(time: 10, unit: 'SECONDS')

                    withSonarQubeEnv('SonarQube') {
                        
                        def resp = sh(
                        script: """curl -sf -H 'Authorization: Bearer ${env.SONAR_AUTH_TOKEN}' \
                            '${env.SONAR_HOST_URL}/api/qualitygates/project_status?projectKey=python-code-disasters'""",
                        returnStdout: true
                        ).trim()

                        def qgStatus = sh(
                        script: "echo '${resp}' | sed -n 's/.*\"status\"[[:space:]]*:[[:space:]]*\"\\([A-Z]*\\)\".*/\\1/p'",
                        returnStdout: true
                        ).trim()

                        echo "Quality Gate status: ${qgStatus}"

                        env.BLOCKER_COUNT = (qgStatus == 'OK') ? '0' : '1'

                        if (qgStatus != 'OK') {
                        error('Build failed: Quality Gate is not OK. See SonarQube dashboard for details.')
                        } else {
                        echo 'Quality Gate OK. Proceeding to Hadoop deployment...'
                        }
                    }
                }
            }
        }

        stage('Deploy to Hadoop') {
            when {
                expression { env.QUALITY_GATE_STATUS == 'OK' || env.BLOCKER_COUNT == '0' }
            }
            steps {
                script {
                    echo "No blocker issues found. Deploying to Hadoop..."

                    withEnv(["PATH=${env.WORKSPACE}/google-cloud-sdk/bin:${env.PATH}"]) {
                        withCredentials([file(credentialsId: 'gcp-credentials', variable: 'GCP_KEY')]) {
                            sh '''
                                set -euo pipefail

                                if ! command -v gcloud >/dev/null 2>&1; then
                                echo "Installing Google Cloud SDK locally in workspace..."
                                GCLOUD_VERSION=481.0.0
                                curl -sSLO "https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${GCLOUD_VERSION}-linux-x86_64.tar.gz"
                                tar -xzf "google-cloud-cli-${GCLOUD_VERSION}-linux-x86_64.tar.gz"
                                ./google-cloud-sdk/install.sh \
                                    --quiet \
                                    --usage-reporting=false \
                                    --path-update=false \
                                    --command-completion=false \
                                    --additional-components=gsutil || true
                                fi

                                gcloud --version
                                gsutil --version

                                gcloud auth activate-service-account --key-file="${GCP_KEY}"
                                gcloud config set project "${PROJECT_ID}"

                                echo "Uploading PySpark script to GCS..."
                                gsutil cp count_lines.py "gs://${GCS_BUCKET}/scripts/"

                                echo "Checking for input data in GCS..."
                                gsutil ls "gs://${GCS_BUCKET}/input/" || echo "Warning: No input files found"

                                echo "Cleaning up old output..."
                                gsutil rm -rf "gs://${GCS_BUCKET}/output/" || true

                                echo "Submitting PySpark job to Dataproc Hadoop cluster..."
                                gcloud dataproc jobs submit pyspark \
                                "gs://${GCS_BUCKET}/scripts/count_lines.py" \
                                --cluster="${CLUSTER_NAME}" \
                                --region="${REGION}" \
                                --project="${PROJECT_ID}" \
                                -- "gs://${GCS_BUCKET}/input/*.py" "gs://${GCS_BUCKET}/output/"

                                echo "Waiting briefly for job output..."
                                sleep 5

                                echo "============================================================"
                                echo "FETCHING HADOOP JOB RESULTS FROM GCS..."
                                echo "============================================================"
                                gsutil cat "gs://${GCS_BUCKET}/output/part-*" 2>/dev/null || echo "No results found"

                                echo ""
                                echo "Results stored at: gs://${GCS_BUCKET}/output/"
                                echo "All output files:"
                                gsutil ls "gs://${GCS_BUCKET}/output/"
                            '''
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the logs for details.'
        }
        always {
            echo 'Cleaning up workspace...'
            cleanWs()
        }
    }
}
