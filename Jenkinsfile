pipeline {
    agent any
    stages {
        stage('build') {
            steps {
		// sh 'python hugepages_unittesting/test.py'
		sh 'echo xflow@123 | sudo -S pip install mock'
		sh 'sudo pip install openpyxl'  
		sh 'sudo pip install paramiko'    
		sh 'python hugepages_unittesting/test.py'
            }
        }
    }
	
	post {
		success {
			mail body: "View console output at ${BUILD_URL}", subject: "${JOB_NAME} Build#  ${BUILD_NUMBER} SUCCESSFUL" , to: 'mahrukh.anwari@xflowresearch.com'
		sh 'echo cleaning directory'
		deleteDir()
		}		
	
		failure {
			mail body: "View console output at ${BUILD_URL}", subject: " ${JOB_NAME} Build#  ${BUILD_NUMBER} FAILED" , to: 'mahrukh.anwari@xflowresearch.com'
		sh 'echo cleaning directory'
		deleteDir()
		}
	}
}
