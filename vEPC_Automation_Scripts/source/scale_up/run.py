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
configurations = get_configurations()
credsks = get_keystone_creds(configurations)
creds = get_nova_creds(configurations)
# Get authorized instance of nova client
nova = nvclient.Client(**creds)
# Get authorized instance of neutron client
neutron = ntrnclient.Client(**credsks)

check_network('S1', neutron, configurations)

k_val = int(configurations['scale-up-val'])
zone_val = int(configurations['zone-val'])

for j in range(0, 3):
	create_cloud_file(name_list[j]+ "-" + str(k_val), (file_list[j]+str(k_val)))
	create_hosts_file(name_list[j]+ "-" + str(k_val), (file_list[j]+str(k_val)))

os.system("chmod +x source/scale_up/at/cloud-config/*")
print("[" + time.strftime("%H:%M:%S")+ "] Starting scale-up...")
#---------------aggregate-group------------------#
#getting name of availability zone to be used in instance creation
avl_zone = get_avlzoneA()
if zone_val == 0:
	avl_zone = get_avlzoneA()
elif zone_val == 1:
	avl_zone = get_avlzoneB()

##----------------------------##
#------changing json values-----#
if zone_val == 0:
	zone_val = 1
elif zone_val == 1:
	zone_val = 0
#----writing increased k_val-----#
input_configurations((k_val+1), zone_val)

# deploy VM's, assign floating IP's

for i in range(0, 3):
	instance_name = configurations['vcm-cfg']['name-prefix'] + name_list[i] + "-" + str(k_val)
	ip_ins = deploy_instance(k_val=k_val, vm_name = instance_name, nova = nova, f_path = (file_list[i]+str(k_val)), neutron = neutron, configurations=configurations, avl_zone=avl_zone)
	ins = InstanceObj(instance_name, ip_ins)
	instance_list.append(ins)
##----------------------------##

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
time.sleep(10)
# check if VM's accept PING to make sure boot-up, time out if they take too long
for i in range(0, 3):
	check_ping_status(instance_list[i].ip, instance_list[i].name)
print("[" + time.strftime("%H:%M:%S")+ "] Assigning new host-names please wait..")
# wait for boot-up completion
time.sleep(10)
# copy files for new hostnames
for i in range(0, 3):
	hostname_config(ssh, instance_list[i].name, instance_list[i].ip, instance_list[i].name, (file_list[i]+str(k_val)), REMOTE_PATH_HOSTNAME)

print("[" + time.strftime("%H:%M:%S")+ "] Initial scale-up process complete! Please wait for configurations..")
time.sleep(30)
# start running scripts on VMs
inst_id = k_val
for i in range(0, 3):
	print("[" + time.strftime("%H:%M:%S")+ "] Configuring " + instance_list[i].name)
	while(True):
		try:
			ssh.connect(instance_list[i].ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] " + instance_list[i].name + " not ready for SSH waiting...")
			time.sleep(5)
	print("[" + time.strftime("%H:%M:%S")+ "] \t Running deploy_script...")
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc "+name_list[i]+" --instance_id " + str(inst_id) + " --internal_if eth0")
	ssh_stdout.readlines()
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	ssh_stdout.readlines()
	ssh.close()

# Start VCM services on rest of components
for i in range(0, 3):
	vcm_start(ssh, instance_list[i].ip, instance_list[i].name)

print("[" + time.strftime("%H:%M:%S")+ "] vEPC scale-up complete... Now exiting ...")