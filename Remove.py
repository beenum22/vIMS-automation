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
from Scale_down import *

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
STACK_NAME = 'IMS'
STACK_HA_NAME = 'IMS-HA'
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
############################ getting scale index ###########################################
file1 = open(PATH+ "/Scale_index.txt", "r")
scale_index= file1.read()
file1.close()


############################ Delete Heat Stack ###########################################

def delete_cluster(heat,cluster_name):
   cluster_full_name=cluster_name
   try:
    heat.stacks.delete(cluster_full_name)
    print('Removing heat stack')
   except:
     print ("Cannot find the Cluster to be deleted. Exiting ...") 
     
# Get authorized instance of heat client
cred = get_keystone_creds(config)
ks_client = Keystone_Client(**cred)
heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token)

delete_cluster(heatclient, STACK_NAME)
delete_cluster(heatclient, STACK_HA_NAME)
while (scale_index >= 2 ):
  try:
      scale_index= str(scale_index)
      delete_cluster(heatclient, 'Scale'+ scale_index)
      scale_index= int(scale_index)-1
  except:
      print('Cannot find cluster to be deleted')
      scale_index= int(scale_index)-1


cluster_details=heatclient.stacks.get(STACK_NAME)
#print cluster_details.status
while(cluster_details.status == 'IN_PROGRESS'):
    try:
      cluster_details=heatclient.stacks.get(STACK_NAME)
      print('Deleting cluster')
      time.sleep(10)
    except:
      print('Cluster Deleted')
      break

########################## Delete Nova Key Pair ##########################################
try:
  nova.keypairs.delete('secure')
  print('Deleted keypair')
except:
  print('Could not delete keypair')
########################## Delete Image File #############################################

def del_image(glance, img_name):
 images = glance.images.list()
 while True:
  try:
   image = images.next()
   if (img_name == image.name):
    glance.images.delete(image.id)
    print('Image Deleted')
    return True
  except StopIteration:
   break

# Get authorized instance of glance client
creden = get_keystone_creds(config)
keystone = ksClient.Client(**creden)
glance_endpoint = keystone.service_catalog.url_for(service_type='image', endpoint_type='publicURL')
glance = glanceclient.Client('2',glance_endpoint, token=keystone.auth_token)

try:
  del_image(glance, IMAGE_NAME)
except:
  print('Cannot find image to be deleted')
