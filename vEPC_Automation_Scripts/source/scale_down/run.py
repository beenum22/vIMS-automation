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

while True:
	prompt = raw_input("[" + time.strftime("%H:%M:%S")+ "] Are you sure you want to scale-down ? <yes/no> ")
	if prompt == 'no':
		print("[" + time.strftime("%H:%M:%S")+ "] Exiting ...")
		sys.exit()
	elif prompt == 'yes':
	    break
	else:
	    print("Illegal input")
name_list = ['SDB', 'CPE', 'DPE']
configurations = get_configurations()
credsks = get_keystone_creds(configurations)
creds = get_nova_creds(configurations)
# Get authorized instance of nova client
nova = nvclient.Client(**creds)
# Get authorized instance of neutron client
neutron = ntrnclient.Client(**credsks)

configurations['auto-del'] = 'yes'
k_val = int (configurations['scale-up-val'])

#terminating instances
if k_val >= 3:
	if k_val > 3:
		k_val = k_val - 1
	vm_name = configurations['vcm-cfg']['name-prefix']+name_list[0]+"-" + str(k_val)
	if not (is_server_exists(vm_name, nova)):
		print("[" + time.strftime("%H:%M:%S")+ "] No scale-up instances exist... Exiting...")
		sys.exit()
		
	print("[" + time.strftime("%H:%M:%S")+ "] Starting scale-down ...")
	for j in range (0, 3):
		instance_name = configurations['vcm-cfg']['name-prefix']+name_list[j]+"-" + str(k_val)
		clear_instance(instance_name, nova, configurations['auto-del'])
	clear_network_ports(k_val, neutron, configurations)
	print("[" + time.strftime("%H:%M:%S")+ "] Scale-down Complete ... Now exiting ...")	
	input_configurations(k_val)

else:
	print("[" + time.strftime("%H:%M:%S")+ "] No scale-up instances exist... Exiting...")
