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

while True:
	prompt = raw_input("[" + time.strftime("%H:%M:%S")+ "] Are you sure you want to terminate vEPC ? <yes/no> ")
	if prompt == 'no':
	    sys.exit()
	elif prompt == 'yes':
	    break
	else:
	    print("Illegal input")
name_list = ['VEM', 'SDB', 'CPE', 'CDF', 'UDB', 'DPE', 'RIF']
configurations = get_configurations()
credsks = get_keystone_creds(configurations)
creds = get_nova_creds(configurations)
# Get authorized instance of nova client
nova = nvclient.Client(**creds)
# Get authorized instance of neutron client
neutron = ntrnclient.Client(**credsks)

if is_server_exists('VCM-SDB-3', nova):
	print("[" + time.strftime("%H:%M:%S")+ "] Please run scale-down script before terminating vEPC... Exiting...")
	sys.exit()

configurations['auto-del'] = 'yes'
configurations['deploy-ems'] = 'yes'
try:
	for i in range(0, 7):
		instance_name = configurations['vcm-cfg']['name-prefix']+name_list[i]+"-1"
		instance_name2 = configurations['vcm-cfg']['name-prefix']+name_list[i]+"-2"
		clear_instance(instance_name, nova, configurations['auto-del'])
		clear_instance(instance_name2, nova, configurations['auto-del'])
	clear_network('S1', neutron, configurations)
	clear_network('SGi', neutron, configurations)
	while True:
		chk = raw_input("[" + time.strftime("%H:%M:%S")+ "] Do you also want to terminate EMS ? <yes/no> ")
		if chk == 'no' or chk == 'yes':
			break
		else:
			print("Illegal input")
		
	if chk == 'yes':
		clear_instance(configurations['vcm-cfg']['ems-vm-name'], nova, configurations['auto-del'])
except:
	print("[" + time.strftime("%H:%M:%S")+ "] vEPC initial deployment doesn't exist ...")
	sys.exit()

print("[" + time.strftime("%H:%M:%S")+ "] vEPC Termination complete ...")

while True:
	chk = raw_input("[" + time.strftime("%H:%M:%S")+ "] Do you want to delete aggregate groups ? <yes/no> ")
	if chk == 'no' or chk == 'yes':
	    break
	else:
	    print("Illegal input")

print("[" + time.strftime("%H:%M:%S")+ "] Deleting Aggregates : ")
del_agg(nova)
print("[" + time.strftime("%H:%M:%S")+ "] Successful ... ")

while True:
	chk = raw_input("[" + time.strftime("%H:%M:%S")+ "] Do you want to delete Images of VCM and EMS ? <yes/no> ")
	if chk == 'no':
	    sys.exit()
	elif chk == 'yes':
	    break
	else:
	    print("Illegal input")
keystone = ksClient.Client(**credsks)
glance_endpoint = keystone.service_catalog.url_for(service_type='image', endpoint_type='publicURL')
glance = glanceclient.Client('2', glance_endpoint, token=keystone.auth_token)

if chk == 'yes':
	img_name = 'EMS_IMG'
	if (image_exists(glance, img_name)):
		del_image(glance, img_name)
		print("[" + time.strftime("%H:%M:%S")+ "] EMS image deleted")
	
	img_name = 'VCM_IMG'
	if (image_exists(glance, img_name)):
		del_image(glance, img_name)
		print("[" + time.strftime("%H:%M:%S")+ "] VCM image deleted")
	
print ("[" + time.strftime("%H:%M:%S")+ "] All vEPC components have been terminated...")
	
	