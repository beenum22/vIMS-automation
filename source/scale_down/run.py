import os
import time
import select
import sys
from os_defs import *
from consts import *
import novaclient.v1_1.client as nvclient
import neutronclient.v2_0.client as ntrnclient
from collections import namedtuple
import readline
import json

#----------------------------------#
from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient import client
#----------------------------------#

import glanceclient
import keystoneclient.v2_0.client as ksClient
# from __future__ import print_function

import logging
import datetime
now = datetime.datetime.now()
date_time = now.strftime("%Y-%m-%d_%H-%M")
filename_activity = 'logs/scale_down_' + date_time + '.log'
filename_error = 'logs/scale_down_error_' + date_time + '.log'
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

logger.info("Starting Scale Down")


while True:
	logger.info("Confirming from user to scale-down")
	prompt = raw_input("[" + time.strftime("%H:%M:%S")+ "] Are you sure you want to scale-down ? <yes/no> ")
	if prompt == 'no':
		logger.info("No scale-down required")
		print("[" + time.strftime("%H:%M:%S")+ "] Exiting ...")
		sys.exit()
	elif prompt == 'yes':
	    break
	else:
	    print("Illegal input")
name_list = ['SDB', 'CPE', 'DPE']
configurations = get_configurations(logger, error_logger)
logger.info("Getting keystone credentials for authorization")
credsks = get_keystone_creds(configurations)
logger_nova.info("Getting nova credentials")
nova_creds = get_nova_creds(configurations)
# Get authorized instance of nova client

logger_nova.info("Getting authorized instance of nova client")
try:
	auth = v2.Password(auth_url=nova_creds['auth_url'],
						   username=nova_creds['username'],
						   password=nova_creds['password'],
						   tenant_name=nova_creds['project_id'])
	sess = session.Session(auth=auth)
	nova = client.Client(nova_creds['version'], session=sess)
except:
	error_logger.exception("creating nova client instance")
# Get authorized instance of neutron client
logger_neutron.info("Getting authorized instance of neutron client")
try:
	neutron = ntrnclient.Client(**credsks)
except:
	error_logger.exception("creating neutron client instance")
configurations['auto-del'] = 'yes'
k_val = int (configurations['scale-up-val'])

#terminating instances
if k_val >= 3:
	if k_val > 3:
		k_val = k_val - 1
	vm_name = configurations['vcm-cfg']['name-prefix']+name_list[0]+"-" + str(k_val)
	if not (is_server_exists(vm_name, nova, logger_nova)):
		logger.warning("No scale-up instances exist")
		print("[" + time.strftime("%H:%M:%S")+ "] No scale-up instances exist... Exiting...")
		sys.exit()
		
	print("[" + time.strftime("%H:%M:%S")+ "] Starting scale-down ...")
	for j in range (0, 3):
		instance_name = configurations['vcm-cfg']['name-prefix']+name_list[j]+"-" + str(k_val)
		clear_instance(instance_name, nova, configurations, neutron, logger, error_logger, logger_nova, logger_neutron)
	clear_network_ports(k_val, neutron, configurations, logger_neutron)
	print("[" + time.strftime("%H:%M:%S")+ "] Scale-down Complete ... Now exiting ...")	
	input_configurations(k_val, logger)
	logger.info("Successfully scaled down")

else:
	logger.warning("No scale-up instances exists")
	print("[" + time.strftime("%H:%M:%S")+ "] No scale-up instances exist... Exiting...")
