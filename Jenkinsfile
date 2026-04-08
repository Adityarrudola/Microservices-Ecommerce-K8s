pipeline {
    agent any

    environment {
        DOCKER_HUB = "adityarrudola"
        GIT_REPO = "https://github.com/Adityarrudola/Microservices-Ecommerce-K8s.git"
        BRANCH = "main"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: "${BRANCH}", url: "${GIT_REPO}"
            }
        }

        stage('Build & Push Images') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub') {

                        docker.build("${DOCKER_HUB}/auth-service:${BUILD_NUMBER}", "./auth-service").push()
                        docker.build("${DOCKER_HUB}/user-service:${BUILD_NUMBER}", "./user-service").push()
                        docker.build("${DOCKER_HUB}/product-service:${BUILD_NUMBER}", "./product-service").push()
                        docker.build("${DOCKER_HUB}/order-service:${BUILD_NUMBER}", "./order-service").push()
                        docker.build("${DOCKER_HUB}/streamlit-ui:${BUILD_NUMBER}", "./ui").push()

                    }
                }
            }
        }

        stage('Update Helm Values') {
            steps {
                sh """
                yq -i -y '.auth.tag = "'"${BUILD_NUMBER}"'"' microservices-chart/values.yaml
                yq -i -y '.user.tag = "'"${BUILD_NUMBER}"'"' microservices-chart/values.yaml
                yq -i -y '.product.tag = "'"${BUILD_NUMBER}"'"' microservices-chart/values.yaml
                yq -i -y '.order.tag = "'"${BUILD_NUMBER}"'"' microservices-chart/values.yaml
                yq -i -y '.ui.tag = "'"${BUILD_NUMBER}"'"' microservices-chart/values.yaml
                """
            }
        }

        stage('Commit & Push Changes') {
            steps {
                withCredentials([string(credentialsId: 'github-token', variable: 'GIT_TOKEN')]) {
                    sh """
                    git config user.name "jenkins"
                    git config user.email "jenkins@local"

                    git add microservices-chart/values.yaml
                    git commit -m "Update image tags to ${BUILD_NUMBER}" || echo "No changes to commit"

                    git push https://adityarrudola:${GIT_TOKEN}@github.com/Adityarrudola/Microservices-Ecommerce-K8s.git ${BRANCH}
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline Success: Images pushed + GitOps triggered"
        }
        failure {
            echo "Pipeline Failed"
        }
    }
}