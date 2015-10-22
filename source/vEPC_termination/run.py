import os    
import sys
import time
from heatclient.v1.stacks import *
from heatclient.client import Client as Heat_Client
import keystoneclient.v2_0.client as ksClient
from os_defs import *
import logging
import datetime
import glanceclient
import paramiko
#----------------------------------#
from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient import client
#----------------------------------#

# global variables
STACK_NAME = "vEPC_test"

#------------------ logging configurations ------------------#
now = datetime.datetime.now()
date_time = now.strftime("%Y-%m-%d_%H-%M")
filename_activity = 'logs/deploy_' + date_time + '.log'
filename_error = 'logs/deploy_error_' + date_time + '.log'

logging.basicConfig(filename=filename_activity, level=logging.INFO, filemode='w', format='%(asctime)s %(levelname)-8s %(name)-23s [-]  %(message)s')

logger=logging.getLogger(__name__)
logger_nova=logging.getLogger('nova')
logger_neutron=logging.getLogger('neutron')
logger_glance = logging.getLogger('glance')
logger_ssh=logging.getLogger('paramiko')
error_logger = logging.getLogger('error_log')

# create logger with 'Error Loging'
error_logger.setLevel(logging.ERROR)
fh = logging.FileHandler(filename_error, mode = 'w')
fh.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
error_logger.addHandler(fh)

logger.info("Starting termination")

while True:
	logger.info("Confirming terminations")
	prompt = raw_input("[" + time.strftime("%H:%M:%S")+ "] Are you sure you want to terminate vEPC ? <yes/no> ")
	if prompt == 'no':
	    sys.exit()
	elif prompt == 'yes':
	    break
	else:
	    print("Illegal input")

#------------------ input configurations ------------------#
configurations = get_configurations(logger, error_logger)
cred = get_keystone_creds(configurations)

#------------------ KeyStone, Glance and Heat Clients  ------------------#
logger.info("Getting authorized instance of keystone client")
try:
	keystone = ksClient.Client(**cred)
except:
	error_logger.exception("Unable to create keystone client instance")
	print ("[" + time.strftime("%H:%M:%S")+ "] Error creating keystone client")
	sys.exit()
logger_glance.info("Getting authorized instance of glance client")
try:
	glance_endpoint = keystone.service_catalog.url_for(service_type='image', endpoint_type='publicURL')
	glance = glanceclient.Client('2', glance_endpoint, token=keystone.auth_token)
except:
	error_logger.exception("Unable to create glance client instance")
	print ("[" + time.strftime("%H:%M:%S")+ "] Error creating glance client")
	sys.exit()
try:
	heat_endpoint = keystone.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
	heatclient = Heat_Client('1', heat_endpoint, token=keystone.auth_token)
except:
	error_logger.exception("Unable to create heat client instance")
	print ("[" + time.strftime("%H:%M:%S")+ "] Error creating heat client")
	sys.exit()
#--------------------- nova client --------------------#
logger_nova.info("Getting nova credentials")
nova_creds = get_nova_creds(configurations)

logger_nova.info("Getting authorized instance of nova client")
try:
	auth = v2.Password(auth_url=nova_creds['auth_url'],
						   username=nova_creds['username'],
						   password=nova_creds['password'],
						   tenant_name=nova_creds['project_id'])
	sess = session.Session(auth=auth)
	nova = client.Client(nova_creds['version'], session=sess)
except:
	error_logger.exception("Unable to create nova client instance")
	print ("[" + time.strftime("%H:%M:%S")+ "] Error creating nova client")
	sys.exit()
#--------------------- delete heat stack --------------------#
delete_cluster(heatclient,STACK_NAME)

#------------------ delete aggregate gorups ------------------#
while True:
	chk = raw_input("[" + time.strftime("%H:%M:%S")+ "] Do you want to delete aggregate groups ? <yes/no> ")
	if chk == 'no' or chk == 'yes':
	    break
	else:
	    print("Illegal input")
if chk == 'yes':
	print("[" + time.strftime("%H:%M:%S")+ "] Deleting Aggregates : ")
	delete_aggregate_group(nova, error_logger, logger_nova)
	print("[" + time.strftime("%H:%M:%S")+ "] Successful ... ")

#--------------------- delete Images --------------------#
while True:
	chk = raw_input("[" + time.strftime("%H:%M:%S")+ "] Do you want to delete Images of VCM and EMS ? <yes/no> ")
	if chk == 'no' or chk == 'yes':
	    break
	else:
	    print("Illegal input")

if chk == 'yes':
	img_name = 'EMS_IMG'
	if (image_exists(glance, img_name, error_logger, logger_glance)):
		delete_image(glance, img_name, error_logger, logger_glance)
		print("[" + time.strftime("%H:%M:%S")+ "] EMS image deleted")
	
	img_name = 'VCM_IMG'
	if (image_exists(glance, img_name, error_logger, logger_glance)):
		delete_image(glance, img_name, error_logger, logger_glance)
		print("[" + time.strftime("%H:%M:%S")+ "] VCM image deleted")

#--------------- waiting for stack termination -----------------#
while(True):
	time.sleep(30)
	try:
		cluster_details=heatclient.stacks.get(STACK_NAME)
	except:
		error_logger.exception("Unable to get stack details")
		print ("[" + time.strftime("%H:%M:%S")+ "] Unable to get stack details")
		break
	if cluster_details.status == 'IN_PROGRESS':
		print('Stack Deletion in progress..')
	elif cluster_details.status == 'FAILED':
		print('Stack Deletion failed')
		delete_cluster(heatclient,STACK_NAME)
	elif cluster_details.status == 'COMPLETE':
		break
