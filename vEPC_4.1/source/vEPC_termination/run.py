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
import glanceclient
import keystoneclient.v2_0.client as ksClient
#----------------------------------#
from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient import client
#----------------------------------#
import logging
import datetime
now = datetime.datetime.now()
date_time = now.strftime("%Y-%m-%d_%H-%M")
filename_activity = 'logs/termination_' + date_time + '.log'
filename_error = 'logs/termination_error_' + date_time + '.log'

logging.basicConfig(filename = filename_activity, level = logging.INFO, filemode = 'w', format = '%(asctime)s %(levelname)-8s %(name)-23s [-]  %(message)s')

logger = logging.getLogger(__name__)
logger_nova = logging.getLogger('nova')
logger_neutron = logging.getLogger('neutron')
logger_glance = logging.getLogger('glance')
logger_ssh = logging.getLogger('paramiko')
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
	prompt = raw_input("[" + time.strftime("%H:%M:%S") + "] Are you sure you want to terminate vEPC ? <yes/no> ")
	if prompt == 'no':
	    sys.exit()
	elif prompt == 'yes':
	    break
	else:
	    print("Illegal input")

#logger.info("vEPC termination started")
name_list = ['VEM', 'SDB', 'CPE', 'CDF', 'UDB', 'DPE', 'RIF']
scale_up_list = ['SDB', 'CPE', 'DPE']

configurations = get_configurations(logger, error_logger)

#check OS environment
name = check_env(logger, error_logger)
#authenticating client APIs
if name != 'unknown-environment':
	
	keystone = keytsone_auth(name, configurations, logger, error_logger)

	nova = nova_auth(name, configurations, logger_nova, error_logger)

	neutron = neutron_auth(name, configurations, logger_neutron, error_logger)

	glance = glance_auth(name, configurations, keystone, logger_glance, error_logger)
else:
	name = 'CentOS'
	keystone = keytsone_auth(name, configurations, logger, error_logger)

	nova = nova_auth(name, configurations, logger_nova, error_logger)

	neutron = neutron_auth(name, configurations, logger_neutron, error_logger)

	glance = glance_auth(name, configurations, keystone, logger_glance, error_logger)
##

configurations['auto-del'] = 'yes'
configurations['deploy-ems'] = 'yes'
#try:
for i in range(0, 7):
	instance_name = name_list[i] + "-1"
	instance_name2 = name_list[i] + "-2"
	clear_instance(instance_name, nova, configurations['auto-del'], configurations,
					neutron, logger, error_logger, logger_nova, logger_neutron)
	clear_instance(instance_name2, nova, configurations['auto-del'], configurations,
					neutron, logger, error_logger, logger_nova, logger_neutron)

del_networks(neutron, configurations, error_logger, logger_neutron)

while True:
	chk = raw_input("[" + time.strftime("%H:%M:%S") + "] Do you also want to terminate EMS ? <yes/no> ")
	if chk == 'no' or chk == 'yes':
		break
	else:
		print("Invalid input")
	
if chk == 'yes':
	clear_instance(configurations['vcm-cfg']['ems-vm-name'], nova, configurations['auto-del'], 
					configurations, neutron, logger, error_logger, logger_nova, logger_neutron)
	router_id = get_router_id(configurations['router']['name'], neutron)
	if (router_id != 'router-not-found'):
		int_net = get_subnet_id(neutron, configurations['networks']['net-int-name'])
		if (int_net != 'subnet-not-found'):
			try:
				remove_interface(neutron, int_net, router_id)
			except:
				error_logger.exception(configurations['networks']['net-int-name'] + " has no interface with VCM Router ...")
			try:
				clear_network(configurations['networks']['net-int-name'], neutron,
								configurations, error_logger, logger_neutron)
			except:
				error_logger.exception(configurations['networks']['net-int-name'] + " doesn't exist ...")
		delete_router(neutron, configurations['router']['name'])
	try:
		group = nova.security_groups.find(name = configurations['sec-group-name'])
		nova.security_groups.delete(group.id)
	except:
		logger.exception("Security group " + configurations['sec-group-name'] + " doesn't exist")
#=====clearing IP files=====#
clear_IP_files(logger)
#============================#
print("[" + time.strftime("%H:%M:%S") + "] vEPC Termination complete ...")

while True:
	chk = raw_input("[" + time.strftime("%H:%M:%S") + "] Do you want to delete aggregate groups ? <yes/no> ")
	if chk == 'no' or chk == 'yes':
	    break
	else:
	    print("Invalid input")
if chk == 'yes':
	print("[" + time.strftime("%H:%M:%S") + "] Deleting Aggregates : ")
	del_agg(nova, error_logger, logger_nova)
	print("[" + time.strftime("%H:%M:%S") + "] Successful ... ")

while True:
	chk = raw_input("[" + time.strftime("%H:%M:%S") + "] Do you want to delete Images of VCM and EMS ? <yes/no> ")
	if chk == 'no':
	    sys.exit()
	elif chk == 'yes':
	    break
	else:
	    print("Invalid input")
logger.info("Getting authorized instance of keystone client")
keystone = ksClient.Client(**credsks)
logger_glance.info("Getting authorized instance of glance client")
glance_endpoint = keystone.service_catalog.url_for(service_type = 'image', endpoint_type = 'publicURL')
glance = glanceclient.Client('2', glance_endpoint, token = keystone.auth_token)

if chk == 'yes':
	img_name = 'EMS_IMG'
	if (image_exists(glance, img_name, error_logger, logger_glance)):
		del_image(glance, img_name, error_logger, logger_glance)
		print("[" + time.strftime("%H:%M:%S") + "] EMS image deleted")
	
	img_name = 'VCM_IMG'
	if (image_exists(glance, img_name, error_logger, logger_glance)):
		del_image(glance, img_name, error_logger, logger_glance)
		print("[" + time.strftime("%H:%M:%S") + "] VCM image deleted")
	
print("[" + time.strftime("%H:%M:%S") + "] All vEPC components have been terminated...")

logger.info("Successfully terminated vEPC")	
#================================================================#