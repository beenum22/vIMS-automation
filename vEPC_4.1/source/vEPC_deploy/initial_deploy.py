#============python lib imports===========#
import os
import time
import select
import sys
from collections import namedtuple
import readline
import paramiko
import json
import logging
import datetime
#==========================================#
#============functions import==============#
from os_defs import *
from consts import *
from file_defs import *
from funcs import *
#==========================================#
#=====openstack client API imports=========#
import neutronclient.v2_0.client as ntrnclient
import glanceclient
import keystoneclient.v2_0.client as ksClient
from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient import client
#==========================================#

#initializing log files
now = datetime.datetime.now()
date_time = now.strftime("%Y-%m-%d_%H-%M")
filename_activity = 'logs/deploy_' + date_time + '.log'
filename_error = 'logs/deploy_error_' + date_time + '.log'
#defining the log structure for log files
logging.basicConfig(filename = filename_activity, level = logging.INFO, filemode = 'w',
					format = '%(asctime)s %(levelname)-8s %(name)-23s [-]  %(message)s')

#initializing name of logging statements
logger = logging.getLogger(__name__)
logger_nova = logging.getLogger('nova')
logger_neutron = logging.getLogger('neutron')
logger_glance = logging.getLogger('glance')
logger_ssh = logging.getLogger('paramiko')
error_logger = logging.getLogger('error_log')

# creating logger with 'Error Loging'
error_logger.setLevel(logging.ERROR)
fh = logging.FileHandler(filename_error, mode = 'w')
fh.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
error_logger.addHandler(fh)

#initializing instance names and hostname files to be used while creating instances
name_list = ['VEM', 'SDB', 'CPE', 'CDF', 'UDB', 'DPE', 'RIF']
file_list = ['vem1.txt', 'sdb1.txt', 'cpe1.txt', 'cdf1.txt', 'udb1.txt', 'dpe1.txt', 'rif1.txt']
file_list2 = ['vem2.txt', 'sdb2.txt', 'cpe2.txt', 'cdf2.txt', 'udb2.txt', 'dpe2.txt', 'rif2.txt']

# paths for VCM configuration files
local_path_mme_cfg = "source/vEPC_deploy/vcm-mme-start"
remote_path_mme_cfg = "/opt/VCM/etc/scripts/vcm-mme-start"

local_path_dell_cfg = "Dell-VCM.cfg"
remote_path_dell_cfg = "/opt/VCM/config/Dell-VCM.cfg"

remote_path_hostname = "/etc/sysconfig/network"
remote_path_hosts = "/etc/hosts"

# named tuple to store VCM component information (instance name and floating IP)
InstanceObj = namedtuple("InstanceObj", "name ip")
InstanceObj2 = namedtuple("InstanceObj", "name ip")
instance_list = []
instance_list2 = []

# get credentials from creds.txt and save in json file
input_configurations(error_logger, logger)

# get configurations from json file
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

# ========= resource check function to check available resources on compute node ========== #
logger_nova.info("Checking if resources available on compute nodes ...")
logger_nova.info("Getting hypervisors list ...")
list = nova.hypervisors.list()
temp_list = list[0].__dict__
node = 'Compute 1'
val1 = check_resource(nova, node, temp_list, logger)
temp_list = list[1].__dict__
node = 'Compute 2'
val2 = check_resource(nova, node, temp_list, logger)

if val1 and val2:
	logger.info("Successfully checked resources. All required resources on compute nodes are availabile ...")
elif not val1:
	print("[" + time.strftime("%H:%M:%S")+ "] Warning! Not enough resources available on Compute 1. Please see logs directory for details.")
	inp = check_input(lambda x: x in ['yes', 'no'],
					"[" + time.strftime("%H:%M:%S")+ "] Do you still want to deploy vEPC? <yes/no> ")
	if inp == 'no':
		sys.exit()
elif not val2:
	print("[" + time.strftime("%H:%M:%S")+ "] Warning! Not enough resources available on Compute 2. Please see activity logs for details.")
	inp = check_input(lambda x: x in ['yes', 'no'],
					"[" + time.strftime("%H:%M:%S")+ "] Do you still want to deploy vEPC? <yes/no> ")
	if inp == 'no':
		sys.exit()
#============================================#

#======= creating VCM and EMS image using glance =========#
#creating VCM Image
img_name = 'VCM_IMG'
if not image_exists(glance, img_name, error_logger, logger_glance):
	print("[" + time.strftime("%H:%M:%S")+ "] Creating VCM image...")
	check_image_directory(img_name, logger_glance, error_logger)
	create_image(glance, img_name, logger_glance, error_logger)
	print("[" + time.strftime("%H:%M:%S")+ "] Successfully created VCM image")
#creating EMS Image
img_name = 'EMS_IMG'
if not image_exists(glance, img_name, error_logger, logger_glance):
	print("[" + time.strftime("%H:%M:%S") + "] Creating EMS image...")
	check_image_directory(img_name, logger_glance, error_logger)
	create_image(glance, img_name, logger_glance, error_logger)
	print("[" + time.strftime("%H:%M:%S") + "] Successfully created EMS image")

#=========================================#

sec_group_name = configurations['sec-group-name']
logger_nova.info("Checking if security group " + configurations['sec-group-name'] + " already exist and creating if not ...")
try:
	group = nova.security_groups.find(name = sec_group_name)
except:
	error_logger.exception(sec_group_name + " doesn't exist.")
	logger_nova.info("Creating security group VCM-vEPC ...")
	nova.security_groups.create(name = sec_group_name, description = 'Security Group for VCM vEPC traffic')
	
# Allow PING, SSH and all TCP ingress and egress traffic on default security group of Openstack
logger_nova.info("Allowing Ping, SSH and All TCP ingress and egress traffic on default security group")
group = nova.security_groups.find(name = sec_group_name)
try:
	nova.security_group_rules.create(group.id, ip_protocol = "icmp",
									from_port = -1, to_port = -1)
except:
	error_logger.exception("ICMP rule already exists")

try:
	nova.security_group_rules.create(group.id, ip_protocol = 'tcp', from_port = 22,
									to_port = 22, cidr = '0.0.0.0/0')
except:
	error_logger.exception("SSH rule already exists")

try:
	nova.security_group_rules.create(group.id, ip_protocol = 'tcp', from_port = 8980,
									to_port = 8980, cidr = '0.0.0.0/0')
except:
	error_logger.exception("EMS port 8980 already allowed")

try:
	nova.security_group_rules.create(group.id, ip_protocol = 'tcp', from_port = 1,
									to_port = 65535, cidr = '0.0.0.0/0')
except:
	error_logger.exception("Port 5000 for VEM already allowed")

logger_nova.info("Successfully allowed Ping, SSH, EMS and VEM ports for security group " + sec_group_name + " ...")
#check if instances already exist
logger.info("Checking if VCM-1 components already exist ...")
for i in range(0, 7):
	instance_name = name_list[i] + "-1"
	if is_server_exists(instance_name, nova, logger_nova):
		print("[" + time.strftime("%H:%M:%S")+ "] vEPC components exist. Please run vEPC Termination script first and then re-try...")
		error_logger.error("vEPC components already exist. Exiting ...")
		sys.exit()

logger.info("Done checking, no instance of VCM-1 exists")
logger.info("Now Checking if VCM-2 already exists")
#check if instances 2 already exist
for i in range(0, 7):
	instance_name = name_list[i]+"-2"
	if is_server_exists(instance_name, nova, logger_nova):
		print("[" + time.strftime("%H:%M:%S")+ "] vEPC components exist. Please run vEPC Termination script first and then re-try...")
		error_logger.error("vEPC components already exist. Exiting ...")
		sys.exit()

logger.info("Done checking, no instance of VCM-2 exists")
#========== creating host aggregates =============#
create_agg(nova, error_logger, logger_nova)
#getting name of availability zones for compute 1 and compute 2 to be used in instance creation
avl_zoneA = get_avlzoneA()
avl_zoneB = get_avlzoneB()

#===update quota values=====#
quota_update(nova, configurations, logger_nova, error_logger)
#===========================#
logger.info("Starting vEPC deployment ...")
print("[" + time.strftime("%H:%M:%S") + "] Starting vEPC deployment ...")
# create networks S1C, S1U, S6a, RADIUS, SGs and SGi and router

net_create(neutron, configurations, error_logger, logger_neutron)

os.system("chmod +x source/vEPC_deploy/at/cloud-config/*")

# deploy VCM-1 and VCM-2 instances, assign floating IP's
for i in range(0, 7):
	instance_name = name_list[i] + "-1"	
	info_msg = "Deploying... " + instance_name
	ip_ins = deploy_instance(instance_name, nova, file_list[i], neutron, configurations,
							avl_zoneA, error_logger, logger_nova, logger_neutron)
	ins = InstanceObj(instance_name, ip_ins)
	instance_list.append(ins)
	
	instance_name = name_list[i] + "-2"		
	ip_ins = deploy_instance(instance_name, nova, file_list[i], neutron, configurations,
							avl_zoneB, error_logger, logger_nova, logger_neutron)
	ins = InstanceObj2(instance_name, ip_ins)
	instance_list2.append(ins)
# wait for boot-up completion
time.sleep(10)
logger_ssh.info("Getting authorized client of paramiko...")
try:
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
except:
	error_logger.exception("Unable to create paramiko client instance")
	print("[" + time.strftime("%H:%M:%S") + "] Error creating paramiko client for SSH ...")
	sys.exit()
print("[" + time.strftime("%H:%M:%S") + "] VCM-1 and VCM-2 instances deployment complete!")
#===============================================================================================#
#============================EMS Deploy=================================================#
ems_name = configurations['vcm-cfg']['ems-vm-name']
logger.info("Starting " + ems_name + " deployement")
if not (is_server_exists(ems_name, nova, logger_nova)):
	# Deploy EMS so that it's ready by the time vEPC is setup
	ems_ip = deploy_EMS(configurations['vcm-cfg']['ems-vm-name'], nova, neutron,
							configurations, avl_zoneA, error_logger, logger_neutron, logger_nova)
	# deploy EMS
	print("[" + time.strftime("%H:%M:%S") + "] Setting up " + ems_name + "...")
	time.sleep(10)
	check_ping_status(ems_ip, configurations['vcm-cfg']['ems-vm-name'], logger)
	
	create_EMS_hostsfile(configurations, nova)
	hostname_config(ssh, ems_name, ems_ip, ems_name, 'ems.txt', remote_path_hostname, error_logger, logger_ssh)
	time.sleep(50)
	while(True):
		try:
			logger_ssh.info("Connecting to " + configurations['vcm-cfg']['ems-vm-name'])
			ssh.connect(ems_ip, username = 'root', password = 'root123')
			logger_ssh.info("Connected to VCM-EMS")
			break
		except:
			print("[" + time.strftime("%H:%M:%S") + "] " + ems_name + " not ready for SSH waiting...")
			error_logger.exception(ems_name + " not ready for SSH")
			time.sleep(3)
	logger_ssh.info("Starting " + ems_name + " service")
	stdin, stdout, stderr = ssh.exec_command("vcmems start")
	while not stdout.channel.exit_status_ready():
		# Only print data if there is data to read in the channel 
		if stdout.channel.recv_ready():
			rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
			if len(rl) > 0:
				# Print data from stdout
				print stdout.channel.recv(1024)
	ssh.close()
	logger_ssh.info("Started " + ems_name + " service")
time.sleep(2)

net_name = configurations['networks']['net-int-name']
server = nova.servers.find(name = ems_name).addresses
ems_ip = server[net_name][1]['addr']
logger_ssh.info("Successfully deployed " + ems_name)
#=================================EMS deploy end====================================#

create_host_file(instance_list, instance_list2, configurations, nova)

# wait for boot-up completion
time.sleep(10)
# check if VM's accept PING to make sure boot-up, time out if they take too long
for i in range(0, 7):
	check_ping_status(instance_list[i].ip, instance_list[i].name, logger)
	check_ping_status(instance_list2[i].ip, instance_list2[i].name, logger)

print("[" + time.strftime("%H:%M:%S")+ "] Assigning new host-names please wait..")

# copy files for new hostnames
for i in range(0, 7):
	hostname_config(ssh, name_list[i], instance_list[i].ip, instance_list[i].name, 
					file_list[i], remote_path_hostname, error_logger, logger_ssh)
	hostname_config(ssh, name_list[i], instance_list2[i].ip, instance_list2[i].name, 
					file_list2[i], remote_path_hostname, error_logger, logger_ssh)

#================update vcm-mme-start file=============#
write_cfg_file(local_path_dell_cfg, configurations, nova, neutron)
mme_file_edit(configurations, neutron, logger)
#======================================================#
# start running scripts on VCM-1
for i in range(0, 7):
	print("[" + time.strftime("%H:%M:%S") + "] Configuring " + instance_list[i].name)
	while(True):
		try:
			info_msg = "Connecting to " + instance_list[i].name
			logger_ssh.info(info_msg)
			ssh.connect(instance_list[i].ip, username = 'root', password = 'root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] " + instance_list[i].name + " not ready for SSH waiting...")
			error_msg = instance_list[i].name + " not ready for SSH "
			logger_ssh.warning(error_msg)
			error_logger.exception(error_msg)
			time.sleep(4)
	
	info_msg = "Connected to " + instance_list[i].name
	logger_ssh.info(info_msg)
	print("[" + time.strftime("%H:%M:%S") + "] \t Running deploy_script..." )
	info_msg = "executing deploy_script ..."
	logger_ssh.info(info_msg)
	if i==0 or i==1 or i==2:
		ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc " + name_list[i] + " --instance_id 1 --internal_if eth0")
	elif i==3 or i==4:
		ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc " + name_list[i] + " --instance_id 1 --internal_if eth1")
	elif i==5 or i==6:
		ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc " + name_list[i] + " --instance_id 1 --internal_if eth2")
	
	output = ssh_stdout.readlines()
	
	if i == 0 or i == 6:
		print("[" + time.strftime("%H:%M:%S") + "] \t Copying config file...")
		logger_ssh.info("Opening stfp session")	
		sftp = ssh.open_sftp()
		logger_ssh.info("Copying config files")
		if i == 0:
			sftp.put(local_path_dell_cfg, remote_path_dell_cfg)
		elif i == 6:
			sftp.put(local_path_mme_cfg, remote_path_mme_cfg)
		logger_ssh.info("Successfully copied")
		sftp.close()
	
	ssh.close()
#===========================================================================================#

# start VCM services on VEM and SDB
vcm_start(ssh, instance_list[0].ip, instance_list[0].name, logger_ssh)
time.sleep(10)
vcm_start(ssh, instance_list[1].ip, instance_list[1].name, logger_ssh)

#=====================configuring vcm-vem-1====================#
print("[" + time.strftime("%H:%M:%S")+ "] Please wait for VEM configuration...")
print("[" + time.strftime("%H:%M:%S")+ "] Configuring VEM-1...")
time.sleep(5)
info_msg = "Connecting to " + instance_list[0].name
logger_ssh.info(info_msg)
ssh.connect(instance_list[0].ip, username = 'root', password = 'root123')
info_msg = "Connected to " + instance_list[0].name
logger_ssh.info(info_msg)

# Source the configuration file Dell-VCM.cfg for VEM-1
source_config(ssh, logger_ssh)

#==================================================#
# Start VCM services on rest of components
for i in range(2, 7):
	vcm_start(ssh, instance_list[i].ip, instance_list[i].name, logger_ssh)
for i in range (0, 7):
	validate_deploy(ssh, instance_list[i].ip, instance_list[i].name, logger_ssh)
#=======================configuring VCM 2 =======================#
for i in range(0, 7):
	print("[" + time.strftime("%H:%M:%S") + "] Configuring " + instance_list2[i].name)
	while(True):
		try:
			info_msg = "Connecting to " + instance_list2[i].name
			logger_ssh.info(info_msg)
			ssh.connect(instance_list2[i].ip, username = 'root', password = 'root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S") + "] " + instance_list2[i].name + " not ready for SSH waiting...")
			error_msg = instance_list2[i].name + " not ready for SSH "
			error_logger.exception(error_msg)
			time.sleep(5)
	info_msg = "Connected to " + instance_list2[i].name
	logger_ssh.info(info_msg)
	logger_ssh.info("Running deploy_script")
	print("[" + time.strftime("%H:%M:%S") + "] \t Running deploy_script..." )
	info_msg = "executing deploy_script ..."
	logger_ssh.info(info_msg)
	
	if i==0 or i==1 or i==2:
		ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc " + name_list[i] + " --instance_id 2 --internal_if eth0")
	elif i==3 or i==4:
		ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc " + name_list[i] + " --instance_id 2 --internal_if eth1")
	elif i==5 or i==6:
		ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc " + name_list[i] + " --instance_id 2 --internal_if eth2")
	
	ssh.close()
#=========================================#
# start VCM services on VEM and SDB
vcm_start(ssh, instance_list2[0].ip, instance_list2[0].name, logger_ssh)
vcm_start(ssh, instance_list2[1].ip, instance_list2[1].name, logger_ssh)

#------------configuring vem-2--------------------#
print("[" + time.strftime("%H:%M:%S") + "] Configuring VEM-2...")
time.sleep(30)
info_msg = "Connecting to " + instance_list2[0].name
logger_ssh.info(info_msg)
ssh.connect(instance_list2[0].ip, username = 'root', password = 'root123')
info_msg = "Connected to " + instance_list2[0].name
logger_ssh.info(info_msg)

logger.info("VCM service up and running on VEM-2")

# Start VCM services on rest of components
for i in range(2, 7):
	vcm_start(ssh, instance_list2[i].ip, instance_list2[i].name, logger_ssh)
for i in range (0, 7):
	validate_deploy(ssh, instance_list2[i].ip, instance_list2[i].name, logger_ssh)
print("[" + time.strftime("%H:%M:%S") + "] VCM-vEPC Deployment Complete ....")
#======================================== vEPC Deploy END ==================================================#
#===========EMS GUI IP ===============#
logger.info(ems_name + " GUI can be started from the browser with url http://"+ems_ip+":8980/vcmems/")
print("[" + time.strftime("%H:%M:%S")+ "] " + ems_name + " GUI can be started from the browser with url http://"+ems_ip+":8980/vcmems/")
