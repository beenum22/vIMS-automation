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
# from __future__ import print_function

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
input_configurations()
#print('getting credentials') 
configurations = get_configurations()
credsks = get_keystone_creds(configurations)
creds = get_nova_creds(configurations)
# Get authorized instance of nova client
nova = nvclient.Client(**creds)
# Get authorized instance of neutron client
neutron = ntrnclient.Client(**credsks)

#-----VCM and EMS image------#
keystone = ksClient.Client(**credsks)
glance_endpoint = keystone.service_catalog.url_for(service_type='image', endpoint_type='publicURL')
glance = glanceclient.Client('2', glance_endpoint, token=keystone.auth_token)

img_name = 'EMS_IMG'
if not image_exists(glance, img_name):
	print ("[" + time.strftime("%H:%M:%S")+ "] Creating EMS image...")
	create_image(glance, img_name)
	print("[" + time.strftime("%H:%M:%S")+ "] Successfully created EMS image")

img_name = 'VCM_IMG'
if not image_exists(glance, img_name):
	print("[" + time.strftime("%H:%M:%S")+ "] Creating VCM image...")
	create_image(glance, img_name)
	print("[" + time.strftime("%H:%M:%S")+ "] Successfully created VCM image")

#----------------------------------#

# Allow PING and SSH
group = nova.security_groups.find(name="default")
try:
	nova.security_group_rules.create(group.id, ip_protocol="icmp",
                                 from_port=-1, to_port=-1)
except:
	pass #print('ICMP rule already exists')
try:
	nova.security_group_rules.create(group.id, ip_protocol='tcp', from_port=22, to_port=22, cidr='0.0.0.0/0')
except:
	pass #print("SSH rule already exists")

#terminate instances if already exist
for i in range(0, 7):
	instance_name = configurations['vcm-cfg']['name-prefix']+name_list[i]+"-1"
	clear_instance(instance_name, nova, configurations['auto-del'])

#terminate instances 2 if already exist
for i in range(0, 7):
	instance_name = configurations['vcm-cfg']['name-prefix']+name_list[i]+"-2"
	clear_instance(instance_name, nova, configurations['auto-del'])

#----------------creating host aggregates--------------
create_agg(nova)
#getting name of availability zone A to be used in instance creation
avl_zoneA = get_avlzoneA()
avl_zoneB = get_avlzoneB()

print("[" + time.strftime("%H:%M:%S")+ "] Starting vEPC deployment ...")
# create networks S1 and SGi
create_network(network_name = configurations['networks']['s1-name'], neutron=neutron, configurations=configurations)
create_network(network_name = configurations['networks']['sgi-name'], neutron=neutron, configurations=configurations)
'''
ports_file_write('s1_u', 's1_u.txt', configurations['networks']['s1-cidr'], neutron)
ports_file_write('s1_u2', 's1_u2.txt', configurations['networks']['s1-cidr'], neutron)
ports_file_write('s1_mme', 's1_mme.txt', configurations['networks']['s1-cidr'], neutron)
ports_file_write('s1_mme2', 's1_mme2.txt', configurations['networks']['s1-cidr'], neutron)
ports_file_write('sgi', 'sgi.txt', configurations['networks']['sgi-cidr'], neutron)
ports_file_write('sgi2', 'sgi2.txt', configurations['networks']['sgi-cidr'], neutron)
'''

os.system("chmod +x source/vEPC_deploy/at/cloud-config/*")

# deploy VM's 1, assign floating IP's
for i in range(0, 7):
	instance_name = configurations['vcm-cfg']['name-prefix']+name_list[i]+"-1"	
	ip_ins = deploy_instance(vm_name = instance_name, nova = nova, f_path = file_list[i], neutron = neutron, configurations=configurations, avl_zone=avl_zoneA)
	ins = InstanceObj(instance_name, ip_ins)
	instance_list.append(ins)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# check if VM's accept PING to make sure boot-up, time out if they take too long
for i in range(0, 7):
	#print(instance_list[i].ip + "    " + instance_list[i].name)
	check_ping_status(instance_list[i].ip, instance_list[i].name)
print("[" + time.strftime("%H:%M:%S")+ "] Assigning new host-names please wait..")
# wait for boot-up completion
time.sleep(30)
# copy files for new hostnames
for i in range(0, 7):
	hostname_config(ssh, name_list[i], instance_list[i].ip, instance_list[i].name, file_list[i], REMOTE_PATH_HOSTNAME)

print("[" + time.strftime("%H:%M:%S")+ "] Instances deployment complete! Please wait for configurations..")
time.sleep(30)
# start running scripts on VCM-1
for i in range(0, 7):
	print("[" + time.strftime("%H:%M:%S")+ "] Configuring " + instance_list[i].name)
	while(True):
		try:
			ssh.connect(instance_list[i].ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] " +instance_list[i].name + " not ready for SSH waiting...")
			time.sleep(4)
	print("[" + time.strftime("%H:%M:%S")+ "] \t Running deploy_script..." )
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc "+name_list[i]+" --instance_id 1 --internal_if eth0")
	ssh_stdout.readlines()
	if i == 0 or i == 6 or i == 4:
		print("[" + time.strftime("%H:%M:%S")+ "] \t Copying config file...")
		sftp = ssh.open_sftp()
		if i == 0:
			sftp.put(LOCAL_PATH_DELL_CFG, REMOTE_PATH_DELL_CFG)
		elif i == 4:
			print("[" + time.strftime("%H:%M:%S")+ "] \t Deleting data.txt")
			sftp.remove(REMOTE_PATH_DAT_CFG)
			print("[" + time.strftime("%H:%M:%S")+ "] \t Deleting CSV")
			sftp.remove(REMOTE_PATH_CSV_CFG)
			print("[" + time.strftime("%H:%M:%S")+ "] \t Adding new data.txt")
			sftp.put(LOCAL_PATH_DAT_CFG, REMOTE_PATH_DAT_CFG)
			print("[" + time.strftime("%H:%M:%S")+ "] \t Adding new CSV")
			sftp.put(LOCAL_PATH_CSV_CFG, REMOTE_PATH_CSV_CFG)
			
			ssh.exec_command('chmod 777 '+REMOTE_PATH_DAT_CFG)
			ssh.exec_command('chmod 777 '+REMOTE_PATH_CSV_CFG)
		elif i == 6:
			sftp.put(LOCAL_PATH_MME_CFG, REMOTE_PATH_MME_CFG)
		sftp.close()
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	ssh_stdout.readlines()
	ssh.close()

#--------------------------------#
# Update ports to allow addresses < portsS1 => 0 == s1_mme(1.4)[1.20], 1 == s1_u(1.5)[1.21] >
update_neutron_port(neutron, get_port_id('s1_u', neutron), configurations['allowed-ip-s1u'], 'S1-u')
update_neutron_port(neutron, get_port_id('s1_mme', neutron), configurations['allowed-ip-s1mme'], 'S1-mme')
update_neutron_port(neutron, get_port_id('sgi', neutron), configurations['allowed-ip-sgi'], 'SGi')

# start VCM services on VEM and SDB
vcm_start(ssh, instance_list[0].ip, instance_list[0].name)
vcm_start(ssh, instance_list[1].ip, instance_list[1].name)

#---------------configuring vcm-vem-1----------#
print("[" + time.strftime("%H:%M:%S")+ "] Please wait for VEM configuration...")
print("[" + time.strftime("%H:%M:%S")+ "] Configuring VCM-VEM-1...")
time.sleep(30)
ssh.connect(instance_list[0].ip, username='root', password='root123')
time_out = 0
while(True):
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	opt = ssh_stdout.readlines()
	# print(opt)
	err = False
	for temp in opt:
		if(("Fail" in temp) or("Not Ready" in temp)):
			print("error")
			err = True
	if not err:
		print("[" + time.strftime("%H:%M:%S")+ "] VCM service up and running on VEM-1...")
		break
	print("[" + time.strftime("%H:%M:%S")+ "] VEM-1 not ready, waiting...")
	time.sleep(30)
	time_out = time_out + 30
# Source the configuration file Dell-VCM.cfg for VEM-1
source_config(ssh)

#----------------------------------------------------------------#
# Start VCM services on rest of components
for i in range(2, 7):
	vcm_start(ssh, instance_list[i].ip, instance_list[i].name)

# Run LTE provisioning script 1
ssh.connect(instance_list[4].ip, username='root', password='root123')
sftp_client = ssh.open_sftp()
remote_file = sftp_client.open("/opt/VCM/etc/scripts/runLteProv.sh", 'r')

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
remote_file.writelines(output)
remote_file.close()
sftp_client.close()
print("[" + time.strftime("%H:%M:%S")+ "] Running LTE Prov script on UDB-1...")
time.sleep(5)

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
print(ssh_stdout.readlines())
ssh.close()
#-------------------------------#
#-------------------------------------------------------------deploying vcm-2--------------------------#
#----------------------------------------#######################################----------------------#
# deploy VM's 2 assign floating IP's
for i in range(0, 7):
	instance_name = configurations['vcm-cfg']['name-prefix']+name_list[i]+"-2"		
	ip_ins = deploy_instance(vm_name = instance_name, nova = nova, f_path = file_list[i], neutron = neutron, configurations=configurations, avl_zone=avl_zoneB)
	ins = InstanceObj2(instance_name, ip_ins)
	instance_list2.append(ins)

for i in range(0, 7):
	check_ping_status(instance_list2[i].ip, instance_list2[i].name)
print("[" + time.strftime("%H:%M:%S")+ "] Assigning new host-names please wait..")
# wait for boot-up completion
time.sleep(30)
	
# copy files for new hostnames
for i in range(0, 7):
	hostname_config(ssh, name_list[i], instance_list2[i].ip, instance_list2[i].name, file_list2[i], REMOTE_PATH_HOSTNAME)

#---------------------VCM 2-------------------#
for i in range(0, 7):
	print("[" + time.strftime("%H:%M:%S")+ "] Configuring " + instance_list2[i].name)
	while(True):
		try:
			ssh.connect(instance_list2[i].ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] " + instance_list2[i].name + " not ready for SSH waiting...")
			time.sleep(5)
	print("[" + time.strftime("%H:%M:%S")+ "] \t Running deploy_script..." )
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc "+name_list[i]+" --instance_id 2 --internal_if eth0")
	ssh_stdout.readlines()
	if i == 0 or i == 6 or i == 4:
		print("[" + time.strftime("%H:%M:%S")+ "] \t Copying config file...")
		sftp = ssh.open_sftp()
		if i == 0:
			sftp.put(LOCAL_PATH_DELL_CFG, REMOTE_PATH_DELL_CFG)
		elif i == 4:
			print("[" + time.strftime("%H:%M:%S")+ "] \t Deleting data.txt")
			sftp.remove(REMOTE_PATH_DAT_CFG)
			print("[" + time.strftime("%H:%M:%S")+ "] \t Deleting CSV")
			sftp.remove(REMOTE_PATH_CSV_CFG)
			print("[" + time.strftime("%H:%M:%S")+ "] \t Adding new data.txt")
			sftp.put(LOCAL_PATH_DAT_CFG, REMOTE_PATH_DAT_CFG)
			print("[" + time.strftime("%H:%M:%S")+ "] \t Adding new CSV")
			sftp.put(LOCAL_PATH_CSV_CFG, REMOTE_PATH_CSV_CFG)
			
			ssh.exec_command('chmod 777 '+REMOTE_PATH_DAT_CFG)
			ssh.exec_command('chmod 777 '+REMOTE_PATH_CSV_CFG)
		elif i == 6:
			sftp.put(LOCAL_PATH_MME_CFG, REMOTE_PATH_MME_CFG)
		sftp.close()
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	ssh_stdout.readlines()
	ssh.close()
#---------------------#

# Update ports to allow addresses configurations['allowed-ip2']
update_neutron_port(neutron, get_port_id('s1_u2', neutron), configurations['allowed-ip-s1u'], 'S1-u2')
update_neutron_port(neutron, get_port_id('s1_mme2', neutron), configurations['allowed-ip-s1mme'], 'S1-mme2')
update_neutron_port(neutron, get_port_id('sgi2', neutron), configurations['allowed-ip-sgi'], 'SGi2')
#------------------------------#

# start VCM services on VEM and SDB
vcm_start(ssh, instance_list2[0].ip, instance_list2[0].name)
vcm_start(ssh, instance_list2[1].ip, instance_list2[1].name)

#------------configuring vcm-vem-2--------------------#
print("[" + time.strftime("%H:%M:%S")+ "] Configuring VCM-VEM-2...")
time.sleep(30)
ssh.connect(instance_list2[0].ip, username='root', password='root123')
time_out = 0
while(True):
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	opt = ssh_stdout.readlines()
	# print(opt)
	err = False
	for temp in opt:
		if(("Fail" in temp) or("Not Ready" in temp)):
			print("error")
			err = True
	if not err:
		print("[" + time.strftime("%H:%M:%S")+ "] VCM service up and running on VEM-2...")
		break
	print("[" + time.strftime("%H:%M:%S")+ "] VEM-2 not ready, waiting...")
	time.sleep(30)
	time_out = time_out + 30
	
# Source the configuration file Dell-VCM.cfg for VEM-2
source_config(ssh)
#-----------------------#

# Start VCM services on rest of components
for i in range(2, 7):
	vcm_start(ssh, instance_list2[i].ip, instance_list2[i].name)

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
print(ssh_stdout.readlines())
ssh.close()
#---------------------------------------VCM-2 deploy end------------------------------------------#
if not (is_server_exists('EMS', nova)):
	if configurations['deploy-ems'] == 'yes':
		# Deploy EMS so that it's ready by the time vEPC is setup
		ems_ip = deploy_EMS(configurations['vcm-cfg']['ems-vm-name'], nova, neutron, configurations, avl_zone=avl_zoneA)
		# deploy EMS
		print("[" + time.strftime("%H:%M:%S")+ "] Setting up EMS...")
		check_ping_status(ems_ip, configurations['vcm-cfg']['ems-vm-name'])
		#time.sleep(10)
		create_EMS_hostsfile(configurations, nova)
		hostname_config(ssh, "EMS", ems_ip, "EMS", 'ems.txt', REMOTE_PATH_HOSTNAME)
		time.sleep(20)
		while(True):
			try:
				ssh.connect(ems_ip, username='root', password='root123')
				break
			except:
				print("[" + time.strftime("%H:%M:%S")+ "] EMS not ready for SSH waiting...")
				time.sleep(3)
		stdin, stdout, stderr = ssh.exec_command("vcmems start")
		while not stdout.channel.exit_status_ready():
			# Only print data if there is data to read in the channel 
			if stdout.channel.recv_ready():
				rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
				if len(rl) > 0:
					# Print data from stdout
					print stdout.channel.recv(1024)
		ssh.close()
time.sleep(2)

net_name = configurations['networks']['net-int-name']
server = nova.servers.find(name="EMS").addresses
ems_ip = server[net_name][1]['addr']

print("[" + time.strftime("%H:%M:%S")+ "] EMS GUI can be started from the browser with url http://"+ems_ip+":8980/vcmems/")