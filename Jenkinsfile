pipeline {
    agent any

    environment {
        DOCKER_HUB = "adityarrudola"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/Adityarrudola/Microservices-Ecommerce-K8s.git'
            }
        }

        stage('Build & Push Images') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub') {

                        docker.build("${DOCKER_HUB}/auth-service:latest", "./auth").push()
                        docker.build("${DOCKER_HUB}/user-service:latest", "./user").push()
                        docker.build("${DOCKER_HUB}/product-service:latest", "./product").push()
                        docker.build("${DOCKER_HUB}/order-service:latest", "./order").push()
                        docker.build("${DOCKER_HUB}/streamlit-ui:latest", "./ui").push()

                    }
                }
            }
        }
    }
}