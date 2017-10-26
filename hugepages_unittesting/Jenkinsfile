pipeline {
    agent any
    stages {
        stage('build') {
            steps {
		sh 'python test.py'
            }
        }
    }
	
	post {
		success {
			mail body: "View console output at ${BUILD_URL}", subject: "${JOB_NAME} Build#  ${BUILD_NUMBER} SUCCESSFUL" , to: 'mahrukh.anwari@xflowresearch.com'
		}		
	
		failure {
			mail body: "View console output at ${BUILD_URL}", subject: " ${JOB_NAME} Build#  ${BUILD_NUMBER} FAILED" , to: 'mahrukh.anwari@xflowresearch.com'
		}
	}
}
