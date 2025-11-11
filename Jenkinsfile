pipeline {
    agent any

    environment {
        PROJECT_ID = 'courseproject-473823'
        CLUSTER_NAME = 'hadoop-cluster'
        REGION = 'us-central1'
        GCS_BUCKET = 'hadoop-cluster-gcs'
        SONARQUBE_URL = 'http://34.70.75.17:9000/'
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
                    returnStdout: true,
                    label: 'Query Sonar API (BLOCKER count)',
                    script: '''
                        set -e
                        curl -sf \
                        -H "Authorization: Bearer $SONAR_AUTH_TOKEN" \
                        "$SONAR_HOST_URL/api/issues/search?componentKeys=python-code-disasters&severities=BLOCKER&resolved=false"
                    '''
                    ).trim()

                    def json = new groovy.json.JsonSlurperClassic().parseText(resp)
                    def blockers = (json.total ?: 0) as Integer

                    echo "Blocker issues: ${blockers}"
                    env.BLOCKER_COUNT = blockers.toString()

                    if (blockers > 0) {
                    error "Found ${blockers} blocker issue(s). Stop."
                    } else {
                    echo "No blocker issues found. Proceeding to Hadoop deployment..."
                    }
                }
                }
            }
        }

        stage('Deploy to Hadoop') {
            when {
                expression { env.BLOCKER_COUNT == '0' }
            }
            steps {
                script {
                    echo "No blocker issues found. Deploying to Hadoop..."

                    withCredentials([file(credentialsId: 'gcp-credentials', variable: 'GCP_KEY')]) {
                        // Authenticate with GCP
                        sh """
                            gcloud auth activate-service-account --key-file=\${GCP_KEY}
                            gcloud config set project courseproject-473823
                        """

                        // Upload the Python script to GCS
                        echo "Uploading PySpark script to GCS..."
                        sh """
                            gsutil cp count_lines.py gs://${GCS_BUCKET}/scripts/
                        """

                        // Ensure input data exists
                        echo "Checking for input data in GCS..."
                        sh """
                            gsutil ls gs://${GCS_BUCKET}/input/ || echo "Warning: No input files found"
                        """

                        // Clean up old output
                        echo "Cleaning up old output..."
                        sh """
                            gsutil rm -rf gs://${GCS_BUCKET}/output/ || true
                        """

                        // Submit Hadoop job to Dataproc
                        echo "Submitting PySpark job to Dataproc Hadoop cluster..."
                        def jobOutput = sh(
                            script: """
                                gcloud dataproc jobs submit pyspark \
                                    gs://${GCS_BUCKET}/scripts/count_lines.py \
                                    --cluster=${CLUSTER_NAME} \
                                    --region=${REGION} \
                                    --project=${PROJECT_ID} \
                                    -- gs://${GCS_BUCKET}/input/*.py gs://${GCS_BUCKET}/output/
                            """,
                            returnStdout: true
                        )

                        echo "Job submission output:"
                        echo jobOutput

                        // Wait a moment for output to be written
                        sleep(time: 5, unit: 'SECONDS')

                        // Display the results
                        echo "\n" + "="*60
                        echo "FETCHING HADOOP JOB RESULTS FROM GCS..."
                        echo "="*60 + "\n"

                        def results = sh(
                            script: "gsutil cat gs://${GCS_BUCKET}/output/part-* 2>/dev/null || echo 'No results found'",
                            returnStdout: true
                        ).trim()

                        echo "\n" + "="*60
                        echo "HADOOP JOB OUTPUT - LINE COUNT RESULTS"
                        echo "="*60
                        echo results
                        echo "="*60

                        echo "\nResults stored at: gs://${GCS_BUCKET}/output/"
                        echo "View all output files:"
                        sh "gsutil ls gs://${GCS_BUCKET}/output/"
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
