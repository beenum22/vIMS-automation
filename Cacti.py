import novaclient.v1_1.client as nvclient
import neutronclient.v2_0.client as ntrnclient
import sys
import os
from os_fun import *
from heatclient.client import Client as Heat_Client
from keystoneclient.v2_0 import Client as Keystone_Client
import glanceclient 
import keystoneclient.v2_0.client as ksClient
import json
import time
import paramiko
import select

##################################### File path function ##################################
import subprocess
p = subprocess.Popen(["pwd"], stdout=subprocess.PIPE , shell=True)
PATH = p.stdout.read()
PATH = PATH.rstrip('\n')

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
IMAGE_PATH = PATH+'/cacti-image.qcow2'
os.environ['IMAGE_PATH'] = PATH+'/IMG'
CONFIG_PATH = PATH+'/configurations.json'
USER_CONFIG_PATH = PATH+'/user_config.json'
STACK_NAME = 'Cacti'
REPO_URL = 'http://repo.cw-ngv.com/stable'
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

############################## Create Ubuntu 14.04 Image ###################################

#os.system("sudo -s")
#os.system("mkdir $IMAGE_PATH")
#os.system("cd $IMAGE_PATH")
#os.system("wget http://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img")

#Get authorized instance of glance client
creden = get_keystone_creds(config)
keystone = ksClient.Client(**creden)
glance_endpoint = keystone.service_catalog.url_for(service_type='image', endpoint_type='publicURL')
glance = glanceclient.Client('2',glance_endpoint, token=keystone.auth_token)
if not image_exists(glance, 'Cacti-image'):
  image = glance.images.create(name="Cacti-image",disk_format = 'ami',container_format = 'ami')
  image = glance.images.upload(image.id, open(IMAGE_PATH, 'rb'))
print ('Successfully added image')

############################# Create Availability Zones #################################

def get_aggnameA():   
   return 'GroupA'
def get_aggnameB():
   return 'GroupB'

def get_avlzoneA():
   return 'compute1'
def get_avlzoneB():
   return 'compute2'

def create_agg(nova):
 hyper_list = nova.hypervisors.list()
 hostnA = hyper_list[0].service['host']
 print hostnA
 try:
   agg_idA = nova.aggregates.create(get_aggnameA(), get_avlzoneA())
 except:
   print('Error')
   pass
 try:
   agg_idB = nova.aggregates.create(get_aggnameB(), get_avlzoneB())
 except:
   print('Error')
   pass
 try:
   nova.aggregates.add_host(aggregate=agg_idA, host=hostnA)
 except:
   print('Error')
   pass
 try:
   nova.aggregates.add_host(aggregate=agg_idB, host=hostnB)
 except:
   print('Error')
   pass

print('Successfully added availaibility zones')

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

############################## Create Keypair #############################################

# Creating a keypair
if not keypair_exists(nova ,'cacti'):
	# Creating a keypair
  print('Creating Keypair')
  keypair = nova.keypairs.create(name = 'cacti')
  # Open a file for storing the private key
  f_private = open('/root/.ssh/cacti.pem', "w")
  # Store the private key
  f_private.write(keypair.private_key)
  f_private.close()
  # Open a file for storing the public key
  f_public = open('/root/.ssh/cacti.pub', "w")
  # Store the public key
  f_public.write(keypair.public_key)
  f_public.close()
  print('Finished Creating Keypairs')
########################### Fetch network ID of private network ###########################

def get_private_id(netname, neutron):
	netw = neutron.list_networks()
	for net in netw['networks']:
		if(net['name'] == netname):
			# print(net['id'])
			return net['id']
	return 'net-not-found'

private_id = get_network_id('IMS-private', neutron = neutron)
private_id = str(private_id)
print ('Network ID of private network = ' + private_id)
############################## Heat Stack Create ##########################################
def create_cluster(heat,cluster_name):
  cluster_full_name=STACK_NAME

  file_main= open(PATH+'/cacti.yaml', 'r')                

  cluster_body={
   "stack_name":cluster_full_name,
   "template":file_main.read(),
   "parameters": {
   "public_net_id": net_id,
   "zone" : domain,
   "flavor": "m1.medium",
   "image": "Cacti-image",     
	 "key_name":"cacti",
   "private_net_id": private_id
 #    "availability_zone":"compute1"
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

######################################## Get Bono IP ##########################################

def get_bono_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='bono_ip':
        bono_ip= i['output_value']
   return bono_ip[0]

#Get Bono IP
bono_ip = get_bono_ip(heatclient , 'IMS')
##################################### Get Node IP ################################################

def get_node_ip(heat, cluster_name):
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='public_ip':
        public_ip= i['output_value']
   return public_ip

node_ip = get_node_ip(heatclient , STACK_NAME)

#################################### Get Sprout IP ############################################

def get_sprout_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='sprout_ip':
        sprout_ip= i['output_value']
   return sprout_ip[0]			

################################# Configure Sprout Node #######################################
#Get Sprout IP
sprout_ip = get_sprout_ip(heatclient , 'IMS')

#Connect to Sprout
#k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print ("Connecting To Sprout Node with IP " + sprout_ip)
ssh.connect( hostname = sprout_ip , username = "root", password = "root123" )
print ("Connected")
stdin, stdout, stderr = ssh.exec_command("sudo -s")  


stdin, stdout, stderr = ssh.exec_command("sudo cat >> /etc/snmp/snmpd.conf")
stdin.write('rocommunity clearwater '+ node_ip + '\n')
stdin.flush()
stdin.write('rocommunity public  default    -V systemonly \n')
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command("service snmpd restart")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
###############################################################################################

print 'To access Cacti enter = '+ node_ip+'/cacti'
