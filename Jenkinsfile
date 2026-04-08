pipeline {
    agent any

    environment {
        DOCKER_HUB = "adityarrudola"
    }

    stages {

        stage('Build & Push Images') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub') {

                        docker.build("${DOCKER_HUB}/auth-service:latest", "./auth-service").push()
                        docker.build("${DOCKER_HUB}/user-service:latest", "./user-service").push()
                        docker.build("${DOCKER_HUB}/product-service:latest", "./product-service").push()
                        docker.build("${DOCKER_HUB}/order-service:latest", "./order-service").push()
                        docker.build("${DOCKER_HUB}/streamlit-ui:latest", "./ui").push()

                    }
                }
            }
        }
    }
}