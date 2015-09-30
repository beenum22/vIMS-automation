import os    
import sys
import time
import readline
import json
from heatclient.v1.stacks import *
import keystoneclient.v2_0.client as ksClient
from heatclient.client import Client as Heat_Client
from collections import namedtuple
from os_defs import *
import yaml

STACK_NAME = "vEPC_test"
name_list = ['VEM', 'SDB', 'CPE', 'CDF', 'UDB', 'DPE', 'RIF']

import logging
import datetime
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

InstanceObj = namedtuple("InstanceObj", "name ip")
InstanceObj2 = namedtuple("InstanceObj", "name ip")
instance_list = []
instance_list2 = []

#input_configurations(error_logger, logger)
configurations = get_configurations(logger, error_logger)

cred = get_keystone_creds(configurations)

ks_client = ksClient.Client(**cred)
heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token)

create_cluster(heatclient,STACK_NAME)

cluster_details=heatclient.stacks.get(STACK_NAME)
while(cluster_details.status!= 'COMPLETE'):
   time.sleep(30)
   if cluster_details.status == 'IN_PROGRESS':
     print('Stack Creation in progress..')
   cluster_details=heatclient.stacks.get(STACK_NAME)

print cluster_details
print "cluster output details \n "
print cluster_details.outputs
instance_tuple = get_instance_floatingip(heatclient, STACK_NAME, 'VEM')
print instance_tuple[0]

instance_tuple = get_instance_private_ip(heatclient, STACK_NAME, 'VEM')
print instance_tuple[0]

for vm_name in name_list:
	vm_ip = get_instance_floatingip(heatclient, STACK_NAME, vm_name)
	instance_obj = InstanceObj(vm_name, vm_ip)
	instance_list.append(instance_obj)
	print vm_ip
