import novaclient.v1_1.client as nvclient
import neutronclient.v2_0.client as ntrnclient
import sys
import os
from heatclient.client import Client as Heat_Client
from keystoneclient.v2_0 import Client as Keystone_Client
import glanceclient 
import keystoneclient.v2_0.client as ksClient
import json
import time

################################### File path function ###################################
import subprocess
p = subprocess.Popen(["pwd"], stdout=subprocess.PIPE , shell=True)
PATH = p.stdout.read()
PATH = PATH.rstrip('\n')

############################## Time Stamp Function #######################################
import sys
from datetime import datetime as dt

old_f = sys.stdout

class F:
    nl = True

    def write(self, x):
        if x == '\n':
            old_f.write(x)
            self.nl = True
        elif self.nl == True:
            old_f.write('%s> %s' % (str(dt.now()), x))
            self.nl = False
        else:
            old_f.write(x)

sys.stdout = F()

############################## Global Variables ##########################################
os.environ['IMAGE_PATH'] = PATH+'/IMG'
CONFIG_PATH = PATH+'/configurations.json'
USER_CONFIG_PATH = PATH+'/user_config.json'
STACK_NAME = 'test'
IMAGE_NAME = 'IMS'
############################## Keystone Credentials Functions ############################

def get_keystone_creds(configurations):
    d = {}
    d['username'] = configurations['os-creds']['os-user']
    d['password'] = configurations['os-creds']['os-pass']
    d['auth_url'] = configurations['os-creds']['os-authurl']
    d['tenant_name'] = configurations['os-creds']['os-tenant-name']
    return d

def get_nova_creds(configurations):
	d = {}
	d['username'] = configurations['os-creds']['os-user']
	d['api_key'] = configurations['os-creds']['os-api-key']
	d['auth_url'] = configurations['os-creds']['os-authurl']
	d['project_id'] = configurations['os-creds']['os-project-id']
	return d
print('Getting credentials')  
def get_configurations():
	file = open(CONFIG_PATH)
	configurations = json.load(file)
	file.close()
	return configurations
print('Credentials Loaded')  
config = get_configurations()

credsks = get_keystone_creds(config)
creds = get_nova_creds(config)

# Get authorized instance of nova client
nova = nvclient.Client(**creds)   
# Get authorized instance of neutron client
neutron = ntrnclient.Client(**credsks)

############################ Delete Heat Stack ###########################################

def delete_cluster(heat,cluster_name):
   cluster_full_name=cluster_name
   try:
    heat.stacks.delete(cluster_full_name)
    print('Removing heat stack')
   except:
     print ("Cannot find the Cluster to be deleted. Exiting ...") 
     sys.exit()
     
# Get authorized instance of heat client
cred = get_keystone_creds(config)
ks_client = Keystone_Client(**cred)
heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token)

delete_cluster(heatclient, STACK_NAME)

########################## Delete Nova Key Pair ##########################################
try:
  nova.keypairs.delete('test')
  print('Deleted keypair')
except:
  print('Could not delete keypair')