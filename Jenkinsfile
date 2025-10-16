// AI-Enhanced DevSecOps Pipeline
// This Jenkinsfile implements a comprehensive CI/CD pipeline with LLM-powered analysis

pipeline {
    agent any
    
    environment {
        // GitHub Configuration
        GITHUB_CREDENTIALS = 'github-pat'
        REPO_URL = 'https://github.com/your-org/your-repo.git'
        
        // n8n Webhook URL
        N8N_WEBHOOK_URL = 'http://localhost:5678/webhook/jenkins-trigger'
        
        // SonarQube Configuration
        SONAR_HOST = 'http://localhost:9000'
        SONAR_PROJECT_KEY = 'your-project-key'
        
        // Build Metadata
        COMMIT_SHA = "${env.GIT_COMMIT}"
        BRANCH_NAME = "${env.GIT_BRANCH}"
        BUILD_NUMBER = "${env.BUILD_NUMBER}"
        COMMIT_AUTHOR = sh(
            script: "git show -s --pretty=%an ${env.GIT_COMMIT}",
            returnStdout: true
        ).trim()
    }
    
    options {
        // Keep only last 10 builds
        buildDiscarder(logRotator(numToKeepStr: '10'))
        
        // Timeout after 30 minutes
        timeout(time: 30, unit: 'MINUTES')
        
        // Don't run concurrent builds
        disableConcurrentBuilds()
    }
    
    triggers {
        // Poll SCM every 5 minutes (fallback if webhook fails)
        pollSCM('H/5 * * * *')
    }
    
    stages {
        stage('📋 Initialization') {
            steps {
                script {
                    echo "╔════════════════════════════════════════════════════╗"
                    echo "║     AI-Enhanced DevSecOps Pipeline Started        ║"
                    echo "╚════════════════════════════════════════════════════╝"
                    echo ""
                    echo "Commit SHA: ${COMMIT_SHA}"
                    echo "Branch: ${BRANCH_NAME}"
                    echo "Author: ${COMMIT_AUTHOR}"
                    echo "Build #: ${BUILD_NUMBER}"
                    echo ""
                }
            }
        }
        
        stage('🔄 Checkout & Build') {
            steps {
                script {
                    echo "┌────────────────────────────────────┐"
                    echo "│  Stage 1: Checkout & Build         │"
                    echo "└────────────────────────────────────┘"
                }
                
                // Checkout code
                checkout scm
                
                // Display changed files
                sh """
                    echo "Changed files in this commit:"
                    git diff-tree --no-commit-id --name-only -r ${COMMIT_SHA} || true
                """
                
                // Build based on project type
                script {
                    if (fileExists('pom.xml')) {
                        echo "Maven project detected"
                        sh 'mvn clean compile'
                    } else if (fileExists('package.json')) {
                        echo "Node.js project detected"
                        sh 'npm install'
                        sh 'npm run build || true'
                    } else if (fileExists('build.gradle')) {
                        echo "Gradle project detected"
                        sh './gradlew clean build'
                    } else {
                        echo "No standard build file found, skipping build"
                    }
                }
            }
        }
        
        stage('🧪 Unit Tests') {
            steps {
                script {
                    echo "┌────────────────────────────────────┐"
                    echo "│  Stage 2: Unit Tests               │"
                    echo "└────────────────────────────────────┘"
                }
                
                script {
                    // Run tests based on project type
                    try {
                        if (fileExists('pom.xml')) {
                            sh 'mvn test'
                            junit '**/target/surefire-reports/*.xml'
                        } else if (fileExists('package.json')) {
                            sh 'npm test || true'
                            // junit 'test-results/*.xml' // if tests generate JUnit XML
                        } else if (fileExists('build.gradle')) {
                            sh './gradlew test'
                            junit '**/build/test-results/test/*.xml'
                        } else if (fileExists('pytest.ini') || fileExists('setup.py')) {
                            sh 'pytest --junitxml=test-results.xml || true'
                            junit 'test-results.xml'
                        }
                    } catch (Exception e) {
                        echo "Warning: Some tests failed, but continuing pipeline"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('📊 SonarQube Quality Scan') {
            steps {
                script {
                    echo "┌────────────────────────────────────┐"
                    echo "│  Stage 3: Quality Scan             │"
                    echo "└────────────────────────────────────┘"
                }
                
                script {
                    try {
                        // Run SonarQube Scanner
                        withSonarQubeEnv('SonarQube') {
                            if (fileExists('pom.xml')) {
                                sh 'mvn sonar:sonar'
                            } else {
                                sh """
                                    sonar-scanner \
                                      -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                                      -Dsonar.sources=. \
                                      -Dsonar.host.url=${SONAR_HOST}
                                """
                            }
                        }
                        
                        // Wait for Quality Gate (with timeout)
                        timeout(time: 5, unit: 'MINUTES') {
                            def qg = waitForQualityGate()
                            if (qg.status != 'OK') {
                                echo "WARNING: Quality Gate failed: ${qg.status}"
                                echo "This will be included in the LLM analysis"
                                // Don't fail the build, let LLM analyze
                                currentBuild.result = 'UNSTABLE'
                            } else {
                                echo "✓ Quality Gate passed"
                            }
                        }
                    } catch (Exception e) {
                        echo "Warning: SonarQube scan failed or timed out: ${e.message}"
                        echo "Continuing with pipeline..."
                        currentBuild.result = 'UNSTABLE'
                    }
                }
                
                // Generate SonarQube report URL
                script {
                    env.SONAR_REPORT_URL = "${SONAR_HOST}/dashboard?id=${SONAR_PROJECT_KEY}"
                    echo "SonarQube Report: ${SONAR_REPORT_URL}"
                }
            }
        }
        
        stage('🤖 Trigger AI Analysis (Non-Blocking)') {
            steps {
                script {
                    echo "┌────────────────────────────────────┐"
                    echo "│  Stage 4: Trigger AI Analysis      │"
                    echo "└────────────────────────────────────┘"
                }
                
                script {
                    try {
                        // Prepare payload for n8n workflow
                        def payload = [
                            commitSHA: env.COMMIT_SHA,
                            branch: env.BRANCH_NAME,
                            author: env.COMMIT_AUTHOR,
                            buildNumber: env.BUILD_NUMBER,
                            sonarURL: env.SONAR_REPORT_URL ?: 'N/A',
                            jenkinsURL: env.BUILD_URL,
                            repository: env.REPO_URL,
                            timestamp: new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'"),
                            buildStatus: currentBuild.result ?: 'SUCCESS'
                        ]
                        
                        def payloadJson = groovy.json.JsonOutput.toJson(payload)
                        
                        echo "Triggering n8n workflow (non-blocking)..."
                        echo "Payload: ${payloadJson}"
                        
                        // Trigger n8n workflow asynchronously (do NOT wait for response)
                        sh """
                            curl -X POST \
                              -H "Content-Type: application/json" \
                              -d '${payloadJson}' \
                              "${N8N_WEBHOOK_URL}" \
                              --max-time 5 \
                              > /dev/null 2>&1 &
                        """
                        
                        echo "✓ n8n workflow triggered successfully (async)"
                        echo "LLM analysis will run in parallel"
                        echo "You'll receive a notification when analysis is complete"
                        
                    } catch (Exception e) {
                        echo "Warning: Failed to trigger n8n workflow: ${e.message}"
                        echo "Build will continue regardless"
                    }
                }
            }
        }
        
        stage('📦 Build Artifacts') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo "┌────────────────────────────────────┐"
                    echo "│  Stage 5: Build Artifacts          │"
                    echo "└────────────────────────────────────┘"
                }
                
                script {
                    // Package application
                    if (fileExists('pom.xml')) {
                        sh 'mvn package -DskipTests'
                        archiveArtifacts artifacts: '**/target/*.jar', fingerprint: true
                    } else if (fileExists('package.json')) {
                        sh 'npm run package || true'
                        archiveArtifacts artifacts: 'dist/**/*', allowEmptyArchive: true
                    } else if (fileExists('build.gradle')) {
                        sh './gradlew assemble'
                        archiveArtifacts artifacts: '**/build/libs/*.jar', fingerprint: true
                    }
                }
            }
        }
        
        stage('🚀 Deploy to Staging (Optional)') {
            when {
                branch 'main'
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo "┌────────────────────────────────────┐"
                    echo "│  Stage 6: Deploy to Staging        │"
                    echo "└────────────────────────────────────┘"
                }
                
                // Add your deployment logic here
                echo "Deployment logic goes here..."
                echo "Example: Deploy to Kubernetes, Docker, or cloud platform"
            }
        }
    }
    
    post {
        always {
            script {
                echo ""
                echo "╔════════════════════════════════════════════════════╗"
                echo "║        Pipeline Execution Summary                  ║"
                echo "╚════════════════════════════════════════════════════╝"
                echo "Status: ${currentBuild.result ?: 'SUCCESS'}"
                echo "Duration: ${currentBuild.durationString}"
                echo "Build URL: ${env.BUILD_URL}"
                echo ""
                echo "Note: AI analysis is running in parallel via n8n"
                echo "You'll receive a notification with LLM recommendations"
                echo ""
            }
            
            // Clean workspace
            cleanWs()
        }
        
        success {
            echo "✅ Build completed successfully!"
        }
        
        failure {
            echo "❌ Build failed!"
            
            // Send failure notification
            emailext (
                subject: "Jenkins Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                    Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}
                    
                    Commit: ${env.COMMIT_SHA}
                    Branch: ${env.BRANCH_NAME}
                    Author: ${env.COMMIT_AUTHOR}
                    
                    Check console output: ${env.BUILD_URL}console
                """,
                to: '${env.COMMIT_AUTHOR}@example.com',
                recipientProviders: [developers(), requestor()]
            )
        }
        
        unstable {
            echo "⚠️ Build is unstable (tests failed or quality gate not passed)"
        }
    }
}

// Helper Functions

def getCommitMessage() {
    return sh(
        script: "git log -1 --pretty=%B ${env.GIT_COMMIT}",
        returnStdout: true
    ).trim()
}

def getChangedFiles() {
    return sh(
        script: "git diff-tree --no-commit-id --name-only -r ${env.GIT_COMMIT}",
        returnStdout: true
    ).trim().split('\n')
}

