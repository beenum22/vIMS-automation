import os    
import sys
import time
import readline
import json
from heatclient.v1.stacks import *
from heatclient.client import Client as Heat_Client
import keystoneclient.v2_0.client as ksClient
from collections import namedtuple
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
name_list = ['VEM', 'SDB', 'CPE', 'CDF', 'UDB', 'DPE', 'RIF']
file_list = ['vem1.txt', 'sdb1.txt', 'cpe1.txt', 'cdf1.txt', 'udb1.txt', 'dpe1.txt', 'rif1.txt']
file_list2 = ['vem2.txt', 'sdb2.txt', 'cpe2.txt', 'cdf2.txt', 'udb2.txt', 'dpe2.txt', 'rif2.txt']


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

#---------------------------------------------------------#
InstanceObj = namedtuple("InstanceObj", "name ip")
InstanceObj2 = namedtuple("InstanceObj", "name ip")
instance_list = []
instance_list2 = []

#------------------ input configurations ------------------#
input_configurations(error_logger, logger)
configurations = get_configurations(logger, error_logger)
cred = get_keystone_creds(configurations)

#------------------ Glance Image creation ------------------#
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
	
img_name = 'EMS_IMG'
if not image_exists(glance, img_name, error_logger, logger_glance):
	print ("[" + time.strftime("%H:%M:%S")+ "] Creating EMS image...")
	check_image_directory(img_name, logger_glance, error_logger)
	create_image(glance, img_name, logger_glance, error_logger)
	print("[" + time.strftime("%H:%M:%S")+ "] Successfully created EMS image")

img_name = 'VCM_IMG'
if not image_exists(glance, img_name, error_logger, logger_glance):
	print("[" + time.strftime("%H:%M:%S")+ "] Creating VCM image...")
	check_image_directory(img_name, logger_glance, error_logger)
	create_image(glance, img_name, logger_glance, error_logger)
	print("[" + time.strftime("%H:%M:%S")+ "] Successfully created VCM image")

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

#--------------------- aggregate group creation --------------------#
create_aggregate_groups(nova, error_logger, logger_nova)
avl_zoneA = get_avlzoneA()
avl_zoneB = get_avlzoneB()

#--------------------- Heat stack creation --------------------#
heat_endpoint = keystone.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
heatclient = Heat_Client('1', heat_endpoint, token=keystone.auth_token)

create_cluster(heatclient,STACK_NAME)

cluster_details=heatclient.stacks.get(STACK_NAME)
while(cluster_details.status!= 'COMPLETE'):
	time.sleep(30)
	if cluster_details.status == 'IN_PROGRESS':
		print('Stack Creation in progress..')
	cluster_details=heatclient.stacks.get(STACK_NAME)
	if cluster_details.status == 'FAILED':
		print('Stack Creation failed')
		sys.exit()
print cluster_details.outputs
