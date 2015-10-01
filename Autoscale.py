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
import paramiko
import select
############################## Time Stamp Function ########################################
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
IMAGE_PATH = '/root/IMG/trusty-server-cloudimg-amd64-disk1.img'
IMAGE_DIRECTORY = '/root/IMG/'
os.environ['IMAGE_PATH'] = '/root/vIMS/IMG'
CONFIG_PATH = '/root/vIMS/configurations.json'
USER_CONFIG_PATH = '/root/vIMS/user_config.json'
STACK_NAME = 'Autoscale'
REPO_URL = 'http://repo.cw-ngv.com/stable'
ETCD_IP = ''
ELLIS_INDEX = '0'
BONO_INDEX = '0'
SPROUT_INDEX = '0'
HOMESTEAD_INDEX = '0'
HOMER_INDEX = '0'
DN_RANGE_START = '6505550000'
DN_RANGE_LENGTH = '1000'
############################## User Configuration Functions ##############################

def get_user_configurations():
	file = open(USER_CONFIG_PATH)
	configurations = json.load(file)
	file.close()
	return configurations

print('Getting user confiurations...')
user_config = get_user_configurations()
ext_net = user_config['networks']['external']
ext_net = str(ext_net)
domain = user_config['domain']['zone']
domain = str(domain)

print('Successfull')
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

########################### Fetch network ID of network netname ###########################

def get_network_id(netname, neutron):
	netw = neutron.list_networks()
	for net in netw['networks']:
		if(net['name'] == netname):
			# print(net['id'])
			return net['id']
	return 'net-not-found'

net_id = get_network_id(netname= ext_net, neutron = neutron)
net_id = str(net_id)
print ('Network ID of external network =' + net_id)

########################### Fetch network ID of private netwirk ###########################

def get_private_id(netname, neutron):
	netw = neutron.list_networks()
	for net in netw['networks']:
		if(net['name'] == netname):
			# print(net['id'])
			return net['id']
	return 'net-not-found'

private_id = get_private_id(netname= 'IMS-private', neutron = neutron)
private_id = str(private_id)
print ('Network ID of external network =' + private_id)
############################## Heat Stack Create ##########################################

def create_cluster(heat,cluster_name):
  cluster_full_name=STACK_NAME

  file_main= open('/root/vIMS/autoscaling.yaml', 'r')                
  file_instance= open('/root/vIMS/create_instance.yaml', 'r')

  cluster_body={
   "stack_name":cluster_full_name,
   "template":file_main.read(),
   "files":{
      "create_instance.yaml":file_instance.read()
     },
     
     "parameters": {
     "public_net_id": net_id,
     "private_net_id": private_id
#     "zone" : domain,
#     "flavor": "m1.medium",
#     "image": "IMS",     
#	    "dnssec_key": "evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==",
#	    "key_name":"secure",
#     "availability_zone":"compute1"
     }
    }
  #try:  
  heat.stacks.create(**cluster_body)
  #except:
  #print ("There is an error creating cluster, exiting...")
  #sys.exit()
  print ("Creating stack "+ cluster_full_name )

########################### Create Heat Stack from credentials of keystone #####################

cred = get_keystone_creds(config)
ks_client = Keystone_Client(**cred)
heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token, username='admin', passwork='admin')
create_cluster(heatclient,STACK_NAME)
#stack = heatclient.stacks.list()
#print stack.next()
print('Please wait while stack is deployed.......')
#time.sleep(180)
cluster_details=heatclient.stacks.get(STACK_NAME)
while(cluster_details.status!= 'COMPLETE'):
   time.sleep(30)
   if cluster_details.status == 'IN_PROGRESS':
     print('Stack Creation in progress..')
   cluster_details=heatclient.stacks.get(STACK_NAME)  
   
##################################### Get Instance IP ##########################################

def get_instance_ip(heat, cluster_name):
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='instance_ip':
        instance_ip= i['output_value']
   return instance_ip

while True:  
  cluster_details=heatclient.stacks.get('Autoscale')
  instance_ip = get_instance_ip(heatclient, STACK_NAME)
  print instance_ip
  print len(instance_ip)
#  print cluster_details.outputs
  time.sleep(30)
  
  