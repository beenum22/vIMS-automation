import os
import time
import select
import sys
from os_defs import *
import novaclient.v1_1.client as nvclient
import neutronclient.v2_0.client as ntrnclient
from consts import *
from utils import print_values_ip
from collections import namedtuple
import readline
import paramiko
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
filename_activity = 'logs/scale_up_' + date_time + '.log'
filename_error = 'logs/scale_up_error_' + date_time + '.log'

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

logger.info("Starting Scale up")


name_list = ['SDB', 'CPE', 'DPE']
file_list = ['sdb', 'cpe', 'dpe']

# Paths for configuration files
LOCAL_PATH_MME_CFG = "source/scale_up/vcm-mme-start"
REMOTE_PATH_MME_CFG = "/opt/VCM/etc/scripts/vcm-mme-start"

LOCAL_PATH_DAT_CFG = "source/scale_up/./data.txt"
REMOTE_PATH_DAT_CFG = "/opt/VCM/etc/data.txt"

LOCAL_PATH_CSV_CFG = "source/scale_up/SubscriptionData.csv"
REMOTE_PATH_CSV_CFG = "/opt/VCM/etc/SubscriptionData.csv"

LOCAL_PATH_DELL_CFG = "Dell-VCM.cfg"
REMOTE_PATH_DELL_CFG = "/opt/VCM/config/Dell-VCM.cfg"

REMOTE_PATH_HOSTNAME = "/etc/sysconfig/network"

# Named tuple to store VCM component information
InstanceObj = namedtuple("InstanceObj", "name ip")
instance_list = []
#input_configurations()
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
check_network('S1', neutron, error_logger, logger_neutron)

k_val = int(configurations['scale-up-val'])
zone_val = int(configurations['zone-val'])

for j in range(0, 3):
	create_cloud_file(name_list[j]+ "-" + str(k_val), (file_list[j]+str(k_val)), logger)
	create_hosts_file(name_list[j]+ "-" + str(k_val), (file_list[j]+str(k_val)), logger)

os.system("chmod +x source/scale_up/at/cloud-config/*")
print("[" + time.strftime("%H:%M:%S")+ "] Starting scale-up...")
#---------------aggregate-group------------------#
#getting name of availability zone to be used in instance creation
avl_zone = get_avlzoneA()
if zone_val == 0:
	avl_zone = get_avlzoneA()
elif zone_val == 1:
	avl_zone = get_avlzoneB()

#-----------------resouce check---------#
logger_nova.info("Getting hypervisors list")
list = nova.hypervisors.list()
if zone_val == 0:
	temp_list = list[0].__dict__
	node = 'Compute 1'
	val1 = check_resource(nova, node, temp_list, logger)
elif zone_val == 1:
	temp_list = list[1].__dict__
	node = 'Compute 2'
	val1 = check_resource(nova, node, temp_list, logger)
if val1:
	#print("[" + time.strftime("%H:%M:%S")+ "] All required resources availabile")
	logger.info("Successfully checked resources. All required resources availabile")
else:
	print("[" + time.strftime("%H:%M:%S")+ "] Warning! Not enough resources available on " + node +". Please see activity logs for details.")
	while True:
		prompt = raw_input("[" + time.strftime("%H:%M:%S")+ "] Do you still want to deploy vEPC? <yes/no> ")
		if prompt == 'no':
			sys.exit()
		elif prompt == 'yes':
			break
		else:
			print("Illegal input")
#end resource check#
#-------------------------------------------#

##----------------------------##
#------changing json values-----#
if zone_val == 0:
	zone_val = 1
elif zone_val == 1:
	zone_val = 0
#----writing increased k_val-----#
input_configurations((k_val+1), zone_val, error_logger, logger)

# deploy VM's, assign floating IP's

for i in range(0, 3):
	instance_name = configurations['vcm-cfg']['name-prefix'] + name_list[i] + "-" + str(k_val)
	ip_ins = deploy_instance(k_val, instance_name, nova, (file_list[i]+str(k_val)), neutron, configurations, avl_zone, error_logger, logger_nova, logger_neutron)
	ins = InstanceObj(instance_name, ip_ins)
	instance_list.append(ins)
##----------------------------##
logger_ssh.info("Getting authorized client of paramiko")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
time.sleep(10)
# check if VM's accept PING to make sure boot-up, time out if they take too long
for i in range(0, 3):
	check_ping_status(instance_list[i].ip, instance_list[i].name, logger)
print("[" + time.strftime("%H:%M:%S")+ "] Assigning new host-names please wait..")
# wait for boot-up completion
time.sleep(10)
# copy files for new hostnames
for i in range(0, 3):
	hostname_config(ssh, instance_list[i].name, instance_list[i].ip, instance_list[i].name, (file_list[i]+str(k_val)), REMOTE_PATH_HOSTNAME, error_logger, logger_ssh)

print("[" + time.strftime("%H:%M:%S")+ "] Initial scale-up process complete! Please wait for configurations..")
time.sleep(30)
# start running scripts on VMs
inst_id = k_val
for i in range(0, 3):
	print("[" + time.strftime("%H:%M:%S")+ "] Configuring " + instance_list[i].name)
	while(True):
		try:
			info_msg = "Connecting to " + instance_list[i].name
			logger_ssh.info(info_msg)
			ssh.connect(instance_list[i].ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] " + instance_list[i].name + " not ready for SSH waiting...")
			error_msg = instance_list[i].name + " not ready for SSH"
			error_logger.exception(error_msg)
			time.sleep(5)
	
	info_msg = "Connected to " + instance_list[i].name
	logger_ssh.info(info_msg)
	
	print("[" + time.strftime("%H:%M:%S")+ "] \t Running deploy_script...")
	info_msg = "Running Command ./deploy_script --vnfc "+name_list[i]+" --instance_id " + str(inst_id) + " --internal_if eth0"
	logger_ssh.info(info_msg)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc "+name_list[i]+" --instance_id " + str(inst_id) + " --internal_if eth0")
	ssh_stdout.readlines()
#	info_msg = ssh_stdout.readlines()[0]
	logger_ssh.info(info_msg)
	logger_ssh.info("Running Command ./validate_deploy.sh")
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
#	info_msg = ssh_stdout.readlines()[0]
	logger_ssh.info(info_msg)
	ssh_stdout.readlines()
	ssh.close()

# Start VCM services on rest of components
for i in range(0, 3):
	vcm_start(ssh, instance_list[i].ip, instance_list[i].name, logger_ssh)
logger.info("Successfully Scaled up")
print("[" + time.strftime("%H:%M:%S")+ "] vEPC scale-up complete... Now exiting ...")