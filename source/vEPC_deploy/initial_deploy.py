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

# VCM-RIF-1, VCM-DPE-1, VCM-UDB-1, VCM-SDB-1, VCM-CPE-1, VCM-CDF-1, VCM-VEM-1

name_list = ['VEM', 'SDB', 'CPE', 'CDF', 'UDB', 'DPE', 'RIF']
file_list = ['vem1.txt', 'sdb1.txt', 'cpe1.txt', 'cdf1.txt', 'udb1.txt', 'dpe1.txt', 'rif1.txt']
file_list2 = ['vem2.txt', 'sdb2.txt', 'cpe2.txt', 'cdf2.txt', 'udb2.txt', 'dpe2.txt', 'rif2.txt']

# Paths for configuration files
LOCAL_PATH_MME_CFG = "source/vEPC_deploy/vcm-mme-start"
REMOTE_PATH_MME_CFG = "/opt/VCM/etc/scripts/vcm-mme-start"

LOCAL_PATH_DAT_CFG = "source/vEPC_deploy/data.txt"
REMOTE_PATH_DAT_CFG = "/opt/VCM/etc/data.txt"

LOCAL_PATH_CSV_CFG = "source/vEPC_deploy/SubscriptionData.csv"
REMOTE_PATH_CSV_CFG = "/opt/VCM/etc/SubscriptionData.csv"

LOCAL_PATH_DELL_CFG = "Dell-VCM.cfg"
REMOTE_PATH_DELL_CFG = "/opt/VCM/config/Dell-VCM.cfg"

REMOTE_PATH_HOSTNAME = "/etc/sysconfig/network"

# Named tuple to store VCM component information
InstanceObj = namedtuple("InstanceObj", "name ip")
InstanceObj2 = namedtuple("InstanceObj", "name ip")
instance_list = []
instance_list2 = []
# Get credentials
input_configurations(error_logger, logger)
#print('getting credentials') 
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
	error_logger.exception("Unable to create nova client instance")
	print ("[" + time.strftime("%H:%M:%S")+ "] Error creating nova client")
	sys.exit()
# Get authorized instance of neutron client
logger_neutron.info("Getting authorized instance of neutron client")
try:
	neutron = ntrnclient.Client(**credsks)
except:
	error_logger.exception("Unable to create neutron client instance")
	print ("[" + time.strftime("%H:%M:%S")+ "] Error creating neutron client")
	sys.exit()
try:
	create_IP_file('s1', configurations, logger)
except:
	error_logger.exception("Unable to create s1 IP file")
try:
	create_IP_file('sgi', configurations, logger)
except:
	error_logger.exception("Unable to create sgi IP file")

write_cfg_file('Dell-VCM.cfg', configurations)
#-----------------resouce check---------#
logger_nova.info("Getting hypervisors list")
list = nova.hypervisors.list()
temp_list = list[0].__dict__
node = 'Compute 1'
val1 = check_resource(nova, node, temp_list, logger)
temp_list = list[1].__dict__
node = 'Compute 2'
val2 = check_resource(nova, node, temp_list, logger)
if val1 and val2:
	#print("[" + time.strftime("%H:%M:%S")+ "] All required resources availabile")
	logger.info("Successfully checked resources. All required resources availabile")
elif not val1:
	print("[" + time.strftime("%H:%M:%S")+ "] Warning! Not enough resources available on Compute 1. Please see activity logs for details.")
	while True:
		prompt = raw_input("[" + time.strftime("%H:%M:%S")+ "] Do you still want to deploy vEPC? <yes/no> ")
		if prompt == 'no':
			sys.exit()
		elif prompt == 'yes':
			break
		else:
			print("Illegal input")
elif not val2:
	print("[" + time.strftime("%H:%M:%S")+ "] Warning! Not enough resources available on Compute 2. Please see activity logs for details.")
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

#-----VCM and EMS image------#
logger.info("Getting authorized instance of keystone client")
try:
	keystone = ksClient.Client(**credsks)
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

#----------------------------------#

# Allow PING and SSH
logger_nova.info("Allowing Ping, SSH, EMS and VEM ports")
group = nova.security_groups.find(name="default")
try:
	nova.security_group_rules.create(group.id, ip_protocol="icmp",
                                 from_port=-1, to_port=-1)
except:
  error_logger.exception("ICMP rule already exists")
  pass #print('ICMP rule already exists')
try:
	nova.security_group_rules.create(group.id, ip_protocol='tcp', from_port=22, to_port=22, cidr='0.0.0.0/0')
except:
  error_logger.exception("SSH rule already exists")
  pass #print("SSH rule already exists")

try:
	nova.security_group_rules.create(group.id, ip_protocol='tcp', from_port=8980, to_port=8980, cidr='0.0.0.0/0')
except:
  error_logger.exception("EMS port 8980 already allowed")
  pass #print("SSH rule already exists")

try:
	nova.security_group_rules.create(group.id, ip_protocol='tcp', from_port=1, to_port=65535, cidr='0.0.0.0/0')
except:
  error_logger.exception("Port 5000 for VCM-VEM already allowed")
  pass #print("SSH rule already exists")

logger_nova.info("Successfully allowed Ping, SSH, EMS and VEM ports")

#check if instances already exist
logger.info("Checking if VCM-1 already exists")
for i in range(0, 7):
	instance_name = configurations['vcm-cfg']['name-prefix']+name_list[i]+"-1"
	if is_server_exists(instance_name, nova, logger_nova):
		print("[" + time.strftime("%H:%M:%S")+ "] vEPC components exist. Please run vEPC Termination script first and then re-try...")
		error_logger.error("vEPC components already exist")
		sys.exit()
logger.info("Done checking no instance of VCM-1 exists")
logger.info("Checking if VCM-2 already exists")
#check if instances 2 already exist
for i in range(0, 7):
	instance_name = configurations['vcm-cfg']['name-prefix']+name_list[i]+"-2"
	if is_server_exists(instance_name, nova, logger_nova):
		print("[" + time.strftime("%H:%M:%S")+ "] vEPC components exist. Please run vEPC Termination script first and then re-try...")
		error_logger.error("vEPC components already exist")
		sys.exit()

logger.info("Done checking no instance of VCM-2 exists")
#----------------creating host aggregates--------------
create_agg(nova, error_logger, logger_nova)
#getting name of availability zone A to be used in instance creation
avl_zoneA = get_avlzoneA()
avl_zoneB = get_avlzoneB()

logger.info("Starting vEPC deployment")
print("[" + time.strftime("%H:%M:%S")+ "] Starting vEPC deployment ...")
# create networks S1 and SGi
create_network(network_name = configurations['networks']['s1-name'], neutron=neutron, configurations=configurations, logger_neutron=logger_neutron )
create_network(network_name = configurations['networks']['sgi-name'], neutron=neutron, configurations=configurations, logger_neutron=logger_neutron)
'''
#ports_file_write('s1_u', 's1_u.txt', configurations['networks']['s1-cidr'], neutron)
#ports_file_write('s1_u2', 's1_u2.txt', configurations['networks']['s1-cidr'], neutron)
#ports_file_write('s1_mme', 's1_mme.txt', configurations['networks']['s1-cidr'], neutron)
#ports_file_write('s1_mme2', 's1_mme2.txt', configurations['networks']['s1-cidr'], neutron)
#ports_file_write('sgi', 'sgi.txt', configurations['networks']['sgi-cidr'], neutron)
#ports_file_write('sgi2', 'sgi2.txt', configurations['networks']['sgi-cidr'], neutron)
'''

os.system("chmod +x source/vEPC_deploy/at/cloud-config/*")

# deploy VM's 1, assign floating IP's
for i in range(0, 7):
	instance_name = configurations['vcm-cfg']['name-prefix']+name_list[i]+"-1"	
	info_msg = "Deploying... " + instance_name
	ip_ins = deploy_instance(instance_name, nova, file_list[i], neutron, configurations, avl_zoneA, error_logger, logger_nova, logger_neutron)
	ins = InstanceObj(instance_name, ip_ins)
	instance_list.append(ins)

logger_ssh.info("Getting authorized client of paramiko")
try:
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
except:
	error_logger.exception("Unable to create paramiko client instance")
	print("[" + time.strftime("%H:%M:%S")+ "] Error creating paramiko client")
	sys.exit()
# wait for boot-up completion
time.sleep(30)
# check if VM's accept PING to make sure boot-up, time out if they take too long
for i in range(0, 7):
	#print(instance_list[i].ip + "    " + instance_list[i].name)
	check_ping_status(instance_list[i].ip, instance_list[i].name, logger)
print("[" + time.strftime("%H:%M:%S")+ "] Assigning new host-names please wait..")
# copy files for new hostnames
for i in range(0, 7):
	hostname_config(ssh, name_list[i], instance_list[i].ip, instance_list[i].name, file_list[i], REMOTE_PATH_HOSTNAME, error_logger, logger_ssh)

print("[" + time.strftime("%H:%M:%S")+ "] VCM-1 instances deployment complete! Please wait for configurations..")
time.sleep(30)
#-------update vcm-mme-start file-----#
mme_file_edit(configurations, neutron, logger)
#-------------------------------------#
# start running scripts on VCM-1
for i in range(0, 7):
	print("[" + time.strftime("%H:%M:%S")+ "] Configuring " + instance_list[i].name)
	while(True):
		try:
			info_msg = "Connecting to " + instance_list[i].name
			logger_ssh.info(info_msg)
			ssh.connect(instance_list[i].ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] " +instance_list[i].name + " not ready for SSH waiting...")
			error_msg = instance_list[i].name + " not ready for SSH "
			logger_ssh.warning(error_msg)
			error_logger.exception(error_msg)
			time.sleep(4)
	
	info_msg = "Connected to " + instance_list[i].name
	logger_ssh.info(info_msg)
	print("[" + time.strftime("%H:%M:%S")+ "] \t Running deploy_script..." )
	info_msg = "executing command: ./deploy_script --vnfc "+name_list[i]+" --instance_id 1 --internal_if eth0"
	logger_ssh.info(info_msg)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc "+name_list[i]+" --instance_id 1 --internal_if eth0")
	ssh_stdout.readlines()
	if i == 0 or i == 6 or i == 4:
		print("[" + time.strftime("%H:%M:%S")+ "] \t Copying config file...")
		logger_ssh.info("Opening stfp session")	
		sftp = ssh.open_sftp()
		logger_ssh.info("Copying config files")
		if i == 0:
			sftp.put(LOCAL_PATH_DELL_CFG, REMOTE_PATH_DELL_CFG)
		elif i == 4:
			print("[" + time.strftime("%H:%M:%S")+ "] \t Deleting data.txt")
			logger_ssh.info("Deleting file data.txt")
			sftp.remove(REMOTE_PATH_DAT_CFG)
			logger_ssh.info("Deleted file CSV")
			print("[" + time.strftime("%H:%M:%S")+ "] \t Deleting CSV")
			logger_ssh.info("Deleting file data.txt")
			sftp.remove(REMOTE_PATH_CSV_CFG)
			logger_ssh.info("Deleted file CSV")
			print("[" + time.strftime("%H:%M:%S")+ "] \t Adding new data.txt")
			logger_ssh.info("Adding new data.txt file")
			sftp.put(LOCAL_PATH_DAT_CFG, REMOTE_PATH_DAT_CFG)
			logger_ssh.info("Added new data.txt file")
			print("[" + time.strftime("%H:%M:%S")+ "] \t Adding new CSV")
			logger_ssh.info("Adding new CSV file")
			sftp.put(LOCAL_PATH_CSV_CFG, REMOTE_PATH_CSV_CFG)
			logger_ssh.info("Added new data.txt file")
			
			ssh.exec_command('chmod 777 '+REMOTE_PATH_DAT_CFG)
			ssh.exec_command('chmod 777 '+REMOTE_PATH_CSV_CFG)
		elif i == 6:
			sftp.put(LOCAL_PATH_MME_CFG, REMOTE_PATH_MME_CFG)
		logger_ssh.info("Successfully copied")
		sftp.close()
	info_msg = "executing command: ./validate_deploy.sh"
	logger_ssh.info(info_msg)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	ssh_stdout.readlines()
	ssh.close()

#--------------------------------#
(s1_mme1, s1_u1) = get_assigned_IP_from_file('s1', error_logger)
sgi1 = get_assigned_IP_from_file('sgi', error_logger)
# Update ports to allow addresses < portsS1 => 0 == s1_mme(1.4)[1.20], 1 == s1_u(1.5)[1.21] >
update_neutron_port(neutron, get_port_id('s1_u', neutron), s1_u1, 'S1-u', logger_neutron, error_logger)
update_neutron_port(neutron, get_port_id('s1_mme', neutron), s1_mme1, 'S1-mme', logger_neutron, error_logger)
update_neutron_port(neutron, get_port_id('sgi', neutron), sgi1, 'SGi', logger_neutron, error_logger)

# start VCM services on VEM and SDB
vcm_start(ssh, instance_list[0].ip, instance_list[0].name, logger_ssh)
vcm_start(ssh, instance_list[1].ip, instance_list[1].name, logger_ssh)

#---------------configuring vcm-vem-1----------#
print("[" + time.strftime("%H:%M:%S")+ "] Please wait for VEM configuration...")
print("[" + time.strftime("%H:%M:%S")+ "] Configuring VCM-VEM-1...")
time.sleep(5)
info_msg = "Connecting to " + instance_list[0].name
logger_ssh.info(info_msg)
ssh.connect(instance_list[0].ip, username='root', password='root123')
info_msg = "Connected to " + instance_list[0].name
logger_ssh.info(info_msg)
time_out = 0
while(True):
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	opt = ssh_stdout.readlines()
	# print(opt)
	err = False
	for temp in opt:
		if(("Fail" in temp) or("Not Ready" in temp)):
			logger_ssh.warning("VCM service is not ready on VCM-VEM-1")
			print("[" + time.strftime("%H:%M:%S")+ "] VCM service is not ready on VCM-VEM-1")
			print ("[" + time.strftime("%H:%M:%S")+ "] SDB Connection check failed")
			err = True
			break
	if not err:
		print("[" + time.strftime("%H:%M:%S")+ "] VCM service up and running on VCM-VEM-1...")
		break
	print("[" + time.strftime("%H:%M:%S")+ "] VCM-VEM-1 not ready, waiting...")
	time.sleep(30)
	time_out = time_out + 30
	if time_out >= 120:
		break
# Source the configuration file Dell-VCM.cfg for VEM-1
source_config(ssh, logger_ssh)

#----------------------------------------------------------------#
# Start VCM services on rest of components
for i in range(2, 7):
	vcm_start(ssh, instance_list[i].ip, instance_list[i].name, logger_ssh)

# Run LTE provisioning script 1
info_msg = "Connecting to " + instance_list[4].name
logger_ssh.info(info_msg)
ssh.connect(instance_list[4].ip, username='root', password='root123')
info_msg = "Connected to " + instance_list[0].name
logger_ssh.info(info_msg)
sftp_client = ssh.open_sftp()
logger_ssh.info("Reading file runLteProv.sh")
remote_file = sftp_client.open("/opt/VCM/etc/scripts/runLteProv.sh", 'r')
logger.info("Getting mme IP")
mme_ip = get_IP_address("VCM-SDB-1", nova, net_int_name=configurations['networks']['net-int-name'])
output = []
for line in remote_file:
	if not "-mem-url " in line:
		output.append(line)
	else:
		output.append("./vcmProv -mem-url "+mme_ip+"\n")

remote_file.close()

# print(output)
remote_file = sftp_client.open("/opt/VCM/etc/scripts/runLteProv.sh", 'w')		
logger_ssh.info("Adding mme IP to runLteProv.sh file")
remote_file.writelines(output)
logger_ssh.info("Successfully added IP")
remote_file.close()
sftp_client.close()
print("[" + time.strftime("%H:%M:%S")+ "] Running LTE Prov script on UDB-1...")
time.sleep(5)

logger_ssh.info("Running LTE Prov script on UDB-1")
transport = ssh.get_transport()
channel = transport.open_session()
channel.exec_command("/opt/VCM/etc/scripts/runLteProv.sh")
while True:
	if channel.exit_status_ready():
		break
	rl, wl, xl = select.select([channel],[],[],0.0)
	if len(rl) > 0:
		# Must be stdout
		print channel.recv(1024)
channel.close()
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("service opensafd restart")
logger_ssh.info("restarting opensafd service")
print(ssh_stdout.readlines())
ssh.close()
#-------------------------------#
#-------------------------------------------------------------deploying vcm-2--------------------------#
#----------------------------------------#######################################----------------------#
# deploy VM's 2 assign floating IP's
logger.info("Successfully deployed VCM-1")
logger.info("Starting VCM-2 deployement ")
for i in range(0, 7):
	instance_name = configurations['vcm-cfg']['name-prefix']+name_list[i]+"-2"		
	ip_ins = deploy_instance(instance_name, nova, file_list[i], neutron, configurations, avl_zoneB, error_logger, logger_nova, logger_neutron)
	ins = InstanceObj2(instance_name, ip_ins)
	instance_list2.append(ins)
# wait for boot-up completion
time.sleep(10)
for i in range(0, 7):
	check_ping_status(instance_list2[i].ip, instance_list2[i].name, logger)
print("[" + time.strftime("%H:%M:%S")+ "] Assigning new host-names please wait..")
# copy files for new hostnames
for i in range(0, 7):
	hostname_config(ssh, name_list[i], instance_list2[i].ip, instance_list2[i].name, file_list2[i], REMOTE_PATH_HOSTNAME, error_logger, logger_ssh)
print("[" + time.strftime("%H:%M:%S")+ "] VCM-2 instances deployment complete! Please wait for configurations..")
# wait for boot-up completion
time.sleep(10)
#---------------------VCM 2-------------------#
for i in range(0, 7):
	print("[" + time.strftime("%H:%M:%S")+ "] Configuring " + instance_list2[i].name)
	while(True):
		try:
			info_msg = "Connecting to " + instance_list2[i].name
			logger_ssh.info(info_msg)
			ssh.connect(instance_list2[i].ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] " + instance_list2[i].name + " not ready for SSH waiting...")
			error_msg = instance_list2[i].name + " not ready for SSH "
			error_logger.exception(error_msg)
			time.sleep(5)
	info_msg = "Connected to " + instance_list2[i].name
	logger_ssh.info(info_msg)
	logger_ssh.info("Running deploy_script")
	print("[" + time.strftime("%H:%M:%S")+ "] \t Running deploy_script..." )
	info_msg = "executing command: ./deploy_script --vnfc "+name_list[i]+" --instance_id 2 --internal_if eth0"
	logger_ssh.info(info_msg)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc "+name_list[i]+" --instance_id 2 --internal_if eth0")
	ssh_stdout.readlines()
	
	if i == 0 or i == 6 or i == 4:
		print("[" + time.strftime("%H:%M:%S")+ "] \t Copying config file...")
		logger_ssh.info("Opening stfp session")
		sftp = ssh.open_sftp()
		logger_ssh.info("Copying config file")
		if i == 0:
			sftp.put(LOCAL_PATH_DELL_CFG, REMOTE_PATH_DELL_CFG)
		elif i == 4:
			print("[" + time.strftime("%H:%M:%S")+ "] \t Deleting data.txt")
			logger_ssh.info("Deleting file data.txt")
			sftp.remove(REMOTE_PATH_DAT_CFG)
			logger_ssh.info("Deleted file data.txt")
			print("[" + time.strftime("%H:%M:%S")+ "] \t Deleting CSV")
			logger_ssh.info("Deleting file CSV")
			sftp.remove(REMOTE_PATH_CSV_CFG)
			logger_ssh.info("Deleted file data.txt")
			print("[" + time.strftime("%H:%M:%S")+ "] \t Adding new data.txt")
			logger_ssh.info("Adding file data.txt")
			sftp.put(LOCAL_PATH_DAT_CFG, REMOTE_PATH_DAT_CFG)
			logger_ssh.info("Added file data.txt")
			print("[" + time.strftime("%H:%M:%S")+ "] \t Adding new CSV")
			logger_ssh.info("Adding new CSV")
			sftp.put(LOCAL_PATH_CSV_CFG, REMOTE_PATH_CSV_CFG)
			logger_ssh.info("Added file data.txt")
			ssh.exec_command('chmod 777 '+REMOTE_PATH_DAT_CFG)
			ssh.exec_command('chmod 777 '+REMOTE_PATH_CSV_CFG)
		elif i == 6:
			sftp.put(LOCAL_PATH_MME_CFG, REMOTE_PATH_MME_CFG)
		sftp.close()
	logger_ssh.info("Successfully copied files")
	logger_ssh.info("executing command: ./validate_deploy.sh")
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	ssh_stdout.readlines()
	ssh.close()
#---------------------#
(s1_mme1, s1_u1) = get_assigned_IP_from_file('s1', error_logger)
sgi1 = get_assigned_IP_from_file('sgi', error_logger)
# Update ports to allow addresses configurations['allowed-ip2']
update_neutron_port(neutron, get_port_id('s1_u2', neutron), s1_u1, 'S1-u2', logger_neutron, error_logger)
update_neutron_port(neutron, get_port_id('s1_mme2', neutron), s1_mme1, 'S1-mme2', logger_neutron, error_logger)
update_neutron_port(neutron, get_port_id('sgi2', neutron), sgi1, 'SGi2', logger_neutron, error_logger)
#------------------------------#

# start VCM services on VEM and SDB
vcm_start(ssh, instance_list2[0].ip, instance_list2[0].name, logger_ssh)
vcm_start(ssh, instance_list2[1].ip, instance_list2[1].name, logger_ssh)

#------------configuring vcm-vem-2--------------------#
print("[" + time.strftime("%H:%M:%S")+ "] Configuring VCM-VEM-2...")
time.sleep(30)
info_msg = "Connecting to " + instance_list2[0].name
logger_ssh.info(info_msg)
ssh.connect(instance_list2[0].ip, username='root', password='root123')
info_msg = "Connected to " + instance_list2[0].name
logger_ssh.info(info_msg)
time_out = 0
while(True):
	logger_ssh.info("executing command: ./validate_deploy.sh ")
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	opt = ssh_stdout.readlines()
	# print(opt)
	err = False
	for temp in opt:
		if(("Fail" in temp) or("Not Ready" in temp)):
			logger_ssh.warning("VCM service is not ready on VCM-VEM-2")
			print("VCM service is not ready on VCM-VEM-2\nSDB Connection check failed")
			err = True
			break
	if not err:
		print("[" + time.strftime("%H:%M:%S")+ "] VCM service up and running on VCM-VEM-2...")
		break
	print("[" + time.strftime("%H:%M:%S")+ "] VCM-VEM-2 not ready, waiting...")
	time.sleep(30)
	time_out = time_out + 30
	if time_out >= 120:
		break

logger.info("VCM service up and running on VCM-VEM-2")	
# Source the configuration file Dell-VCM.cfg for VEM-2
source_config(ssh, logger_ssh)
#-----------------------#


# Start VCM services on rest of components
for i in range(2, 7):
	vcm_start(ssh, instance_list2[i].ip, instance_list2[i].name, logger_ssh)

# Run LTE provisioning script on VCM-2
ssh.connect(instance_list2[4].ip, username='root', password='root123')

sftp_client = ssh.open_sftp()
remote_file = sftp_client.open("/opt/VCM/etc/scripts/runLteProv.sh", 'r')

mme_ip = get_IP_address("VCM-SDB-2", nova, net_int_name=configurations['networks']['net-int-name'])
output = []
for line in remote_file:
	if not "-mem-url " in line:
		output.append(line)
	else:
		output.append("./vcmProv -mem-url "+mme_ip+"\n")
remote_file.close()
# print(output)
remote_file = sftp_client.open("/opt/VCM/etc/scripts/runLteProv.sh", 'w')		
remote_file.writelines(output)
remote_file.close()
sftp_client.close()
print("[" + time.strftime("%H:%M:%S")+ "] Running LTE Prov script on UDB-2...")
time.sleep(5)

transport = ssh.get_transport()
channel = transport.open_session()
logger_ssh.info("executing command: /opt/VCM/etc/scripts/runLteProv.sh ")
channel.exec_command("/opt/VCM/etc/scripts/runLteProv.sh")
while True:
	if channel.exit_status_ready():
		break
	rl, wl, xl = select.select([channel],[],[],0.0)
	if len(rl) > 0:
		# Must be stdout
		print channel.recv(1024)
channel.close()
logger_ssh.info("restarting opensafd service ")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("service opensafd restart")
print(ssh_stdout.readlines())
logger_ssh.info(ssh_stdout.readlines())
logger_ssh.info("restarting opensafd restarted ")
ssh.close()
logger.info("VCM-2 Successfully deployed")
#---------------------------------------VCM-2 deploy end------------------------------------------#
#------------------------------------------------------------------------------------------------#
ems_name = configurations['vcm-cfg']['ems-vm-name']
#-----------------------------EMS Deploy-----------------------------#
logger.info("Starting " + ems_name + " deployement")
if not (is_server_exists(ems_name, nova, logger_nova)):
	if configurations['deploy-ems'] == 'yes':
		# Deploy EMS so that it's ready by the time vEPC is setup
		ems_ip = deploy_EMS(configurations['vcm-cfg']['ems-vm-name'], nova, neutron, configurations, avl_zoneA, error_logger, logger_neutron, logger_nova)
		# deploy EMS
		print("[" + time.strftime("%H:%M:%S")+ "] Setting up " + ems_name + "...")
		check_ping_status(ems_ip, configurations['vcm-cfg']['ems-vm-name'], logger)
		#time.sleep(10)
		create_EMS_hostsfile(configurations, nova)
		hostname_config(ssh, ems_name, ems_ip, ems_name, 'ems.txt', REMOTE_PATH_HOSTNAME, error_logger, logger_ssh)
		time.sleep(20)
		while(True):
			try:
				logger_ssh.info("Connecting to VCM-EMS")
				ssh.connect(ems_ip, username='root', password='root123')
				logger_ssh.info("Connected to VCM-EMS")
				break
			except:
				print("[" + time.strftime("%H:%M:%S")+ "] " + ems_name + " not ready for SSH waiting...")
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
server = nova.servers.find(name=ems_name).addresses
ems_ip = server[net_name][1]['addr']
logger_ssh.info("Successfully deployed " + ems_name)
print("[" + time.strftime("%H:%M:%S")+ "] " + ems_name + " GUI can be started from the browser with url http://"+ems_ip+":8980/vcmems/")
#------------------EMS deploy end-------------------------#

