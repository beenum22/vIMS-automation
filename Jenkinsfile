pipeline {
    agent any
	ansiColor('xterm') {
    stages {
        stage('build') {
            steps {
		// sh 'python hugepages_unittesting/test.py'
		// installing the packages using pip install"
		sh 'sudo pip install mock'
		sh 'sudo pip install openpyxl'  
		sh 'sudo pip install paramiko' 
		sh 'sudo pip install requests'
		sh 'sudo pip install openpyxl'
		// running the hugepages test script
		sh 'python hugepages_unittesting/test.py'
            }
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
		// deleteDir()
		}
	}
}
