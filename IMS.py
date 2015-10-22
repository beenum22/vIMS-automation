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
import Scale
import Scale_down
from commands import getoutput
from multiprocessing import Process
from os import system
from time import sleep
#----------------------------------#
from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient import client
#----------------------------------#

##################################### File path function ###################################
import subprocess
p = subprocess.Popen(["pwd"], stdout=subprocess.PIPE , shell=True)
PATH = p.stdout.read()
PATH = PATH.rstrip('\n')

############################## logging #####################################################
import logging
import datetime
now = datetime.datetime.now()
date_time = now.strftime("%Y-%m-%d_%H-%M")
filename_activity = PATH+'/logs/deploy_' + date_time + '.log'
filename_error = PATH+'/logs/deploy_error_' + date_time + '.log'

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
IMAGE_PATH = PATH+'/vIMS.qcow2'
COMPRESSED_FILE_PATH = '/root/IMG/vIMS-image.tar.gz'
IMAGE_DIRECTORY = '/root/IMG/'
SNMP_CONFIG_PATH = '/etc/snmp/snmpd.conf'
SNMP_FILE_PATH = PATH+'/snmpd.conf'
MIB_PATH = "/usr/share/mibs/PROJECT-CLEARWATER-MIB.txt"
#MIB_FILE_PATH = "/root/vIMS/PROJECT-CLEARWATER-MIB.txt"
MIB_FILE_PATH = "/vIMS/PROJECT-CLEARWATER-MIB.txt"
os.environ['IMAGE_PATH'] = PATH+'/IMG'
CONFIG_PATH = PATH+'/configurations.json'
USER_CONFIG_PATH = PATH+'/user_config.json'
STACK_NAME = 'IMS'
REPO_URL = 'http://repo.cw-ngv.com/stable'
ETCD_IP = ''
ELLIS_INDEX = '0'
BONO_INDEX = '0'
SPROUT_INDEX = '0'
HOMESTEAD_INDEX = '0'
HOMER_INDEX = '0'
DN_RANGE_START = '6505550000'
DN_RANGE_LENGTH = '1000'
CALL_THRESHOLD = '20000'
CALL_LOWER_THRESHOLD = '10'
#LOCAL_IP = '10.204.110.42'
############################## User Configuration Functions ##############################

def get_user_configurations():
	file = open(USER_CONFIG_PATH)
	configurations = json.load(file)
	file.close()
	return configurations

print('Getting user confiurations...')
logger.info("Getting initial user confiurations.")
user_config = get_user_configurations()
ext_net = user_config['networks']['external']
ext_net = str(ext_net)
domain = user_config['domain']['zone']
domain = str(domain)

print('Successfull')
logger.info("Getting initial user confiurations Successfull.")
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
  d['password'] = configurations['os-creds']['os-pass']
  d['auth_url'] = configurations['os-creds']['os-authurl']
  d['project_id'] = configurations['os-creds']['os-project-id']
  d['version'] = "1.1"
  return d

print('Getting credentials')  
logger.info("Getting client credentials")
def get_configurations():
	file = open(CONFIG_PATH)
	configurations = json.load(file)
	file.close()
	return configurations
print('Credentials Loaded')
logger.info("Credentials Loaded")  
config = get_configurations()
credsks = get_keystone_creds(config)
logger.info("Getting Keystone credentials")
creds = get_nova_creds(config)
logger_nova.info("Getting of nova credentials")

# Get authorized instance of nova client
logger_nova.info("Getting authorized instance of nova client")

auth = v2.Password(auth_url=creds['auth_url'],
               username=creds['username'],
               password=creds['password'],
               tenant_name=creds['project_id'])
sess = session.Session(auth=auth)
nova = client.Client(creds['version'], session=sess)
#except:
#  error_logger.exception("Unable to create nova client instance")
#  print ("[" + time.strftime("%H:%M:%S")+ "] Error creating nova client")
#  sys.exit()
# Get authorized instance of neutron client
logger_neutron.info("Getting authorized instance of neutron client")


#nova = nvclient.Client(**creds) 
# Get authorized instance of neutron client
neutron = ntrnclient.Client(**credsks)
logger_neutron.info("Getting authorized instance of nova client")
############################### Create Keypair #########################################

# Creating a keypair
print('Creating Keypair')
logger.info("Creating Keypair")
keypair = nova.keypairs.create(name = 'secure')
# Open a file for storing the private key
f_private = open('/root/.ssh/secure.pem', "w")
# Store the private key
f_private.write(keypair.private_key)
f_private.close()
# Open a file for storing the public key
f_public = open('/root/.ssh/secure.pub', "w")
# Store the public key
f_public.write(keypair.public_key)
f_public.close()
print('Finished Creating Keypairs')
logger.info("Finished Creating Keypairs")

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
   logger_nova.info("creating nova aggregate group A and availability zone A")
 except:
   
   print('Err')
   error_logger.exception("Unable to create nova aggregate group A and availability zone A")
   pass
 try:
   agg_idB = nova.aggregates.create(get_aggnameB(), get_avlzoneB())
   logger_nova.info("creating nova aggregate group B and availability zone B")
 except:
   print('Err')
   error_logger.exception("Unable to create nova aggregate group B and availability zone B")
   pass
 try:
   nova.aggregates.add_host(aggregate=agg_idA, host=hostnA)
   logger_nova.info("Adding host to nova aggregate group A")
 except:
   print('Err')
   error_logger.exception("Error in adding host to nova aggregate group A")
   pass
 try:
   nova.aggregates.add_host(aggregate=agg_idB, host=hostnB)
   logger_nova.info("Adding host to nova aggregate group B")
 except:
   print('Err')
   error_logger.exception("Error in adding host to nova aggregate group B")
   pass

print('Successfully added availaibility zones')
logger.info("Successfully added availaibility zones")
############################## Create Ubuntu 14.04 Image ###################################

#os.system("sudo -s")
#os.system("cd /root/IMG")
#os.system("tar "+ COMPRESSED_FILE_PATH +" -C /tmp")
#os.system("mkdir $IMAGE_PATH")
#os.system("cd $IMAGE_PATH")
#os.system("wget http://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img")

# Get authorized instance of glance client
creden = get_keystone_creds(config)
logger.info("getting keystone client credentials")
keystone = ksClient.Client(**creden)
logger_glance.info("Creating Glance endpoint")
glance_endpoint = keystone.service_catalog.url_for(service_type='image', endpoint_type='publicURL')
logger_glance.info("Creating Glance client")
glance = glanceclient.Client('2',glance_endpoint, token=keystone.auth_token)

logger_glance.info("Creating Glance image")
image = glance.images.create(name="IMS",disk_format = 'ami',container_format = 'ami')
logger_glance.info("Uploading Glance Image")
image = glance.images.upload(image.id, open(IMAGE_PATH, 'rb'))
print ('Successfully added image')
logger_glance.info("Successfully added image")
 

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

############################ Get a DNS key ################################################
#dnssec_key = os.system("head -c 64 /dev/random | base64")
#dnssec_key = str(dnssec_key)
print ('Successfully created a DNS security key')
logger.info("Successfully created a DNS security key")
############################## Heat Stack Create ##########################################
def create_cluster(heat,cluster_name):
  cluster_full_name=STACK_NAME

  file_main= open(PATH+'/clearwater.yaml', 'r')                
  file_bono= open(PATH+'/bono.yaml', 'r')
  file_sprout= open(PATH+'/sprout.yaml', 'r')
  file_ralf= open(PATH+'/ralf.yaml', 'r')
  file_dns= open(PATH+'/dns.yaml', 'r')
  file_ellis= open(PATH+'/ellis.yaml', 'r')
  file_network= open(PATH+'/network.yaml', 'r')
  file_groups= open(PATH+'/security-groups.yaml', 'r')
  file_homestead= open(PATH+'/homestead.yaml', 'r')
  file_homer= open(PATH+'/homer.yaml', 'r')

  cluster_body={
   "stack_name":cluster_full_name,
   "template":file_main.read(),
   "files":{
      "bono.yaml":file_bono.read(),
      "homestead.yaml": file_homestead.read(),
      "sprout.yaml": file_sprout.read(),
      "ellis.yaml": file_ellis.read(),
      "network.yaml": file_network.read(),
	  "dns.yaml": file_dns.read(),
      "security-groups.yaml": file_groups.read(),
      "ralf.yaml": file_ralf.read(),
      "homer.yaml": file_homer.read()
     },
     "parameters": {
     "public_net_id": net_id,
     "zone" : domain,
     "flavor": "m1.medium",
     "image": "IMS",     
  	 "dnssec_key": "evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==",
  	 "key_name":"secure",
 #    "availability_zone":"compute1"
     }
    }
  #try:  
  heat.stacks.create(**cluster_body)
  #except:
  #print ("There is an Err creating cluster, exiting...")
  #sys.exit()
  print ("Creating stack "+ cluster_full_name )
  logger.info("Creating Heat Stack")
  

########################### Create Heat Stack from credentials of keystone #####################
logger.info("Getting keystone credentials to create heat client")
cred = get_keystone_creds(config)
logger.info("creating keystone client")
ks_client = Keystone_Client(**cred)
logger.info("creating heat endpoint")
heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
logger.info("creating heat client")
heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token, username='admin', passwork='admin')
logger.info("creating heatstack Cluster")
create_cluster(heatclient,STACK_NAME)
#stack = heatclient.stacks.list()
#print stack.next()
logger.info("Deployong Heat Stack")
print('Please wait while stack is deployed.......')
#time.sleep(180)
cluster_details=heatclient.stacks.get(STACK_NAME)
while(cluster_details.status!= 'COMPLETE'):
   time.sleep(30)
   if cluster_details.status == 'IN_PROGRESS':
     print('Stack Creation in progress..')
   cluster_details=heatclient.stacks.get(STACK_NAME)          
                        
##################################### Get DNS IP ################################################

def get_dns_ip(heat, cluster_name):
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='dns_ip':
        dns_ip= i['output_value']
   return dns_ip

#################################### Configure DNS Server #######################################
#Get DNS IP
logger.info("Getting DNS ip to configure DNS Server")
dns_ip = get_dns_ip(heatclient , STACK_NAME)
time.sleep(240) #Wait for the DNS server to spawn and install BIND
#Connect to DNS
while True:
  try:
#    k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print ("Connecting To DNS Node with IP " + dns_ip)
    logger_ssh.info("Connecting To DNS Node")
    ssh.connect( hostname = dns_ip , username = "root", password = "root123" )
    print ("Connected")
    break
  except:
    error_logger.exception("Unable to connect with DNS server")
    print("Could not connect. Retrying in 5 seconds...")
    time.sleep(5)
	


print('Updating Ubuntu..')
logger_ssh.info("Updating Ubuntu by apt-get update")
stdin, stdout, stderr = ssh.exec_command("apt-get update")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

print('Installing Bind DNS Server')
logger_ssh.info("Installing Bind DNS Server")
stdin, stdout, stderr = ssh.exec_command("sudo DEBIAN_FRONTEND=noninteractive apt-get install bind9 --yes")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
print('Updating BIND configuration with the specified zone and key')
logger_ssh.info("Updating BIND configuration with the specified zone and key")
stdin, stdout, stderr = ssh.exec_command("sudo cat >> /etc/bind/named.conf.local")
stdin.write('key ' + domain +'. {\n')
stdin.flush()
stdin.write('  algorithm "HMAC-MD5";\n')
stdin.flush()
stdin.write('  secret "evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==";\n')
stdin.flush()
stdin.write('};\n')
stdin.flush()
stdin.write('\n')
stdin.flush()
stdin.write('zone "'+domain+'" IN {\n')
stdin.flush()
stdin.write('  type master;\n')
stdin.flush()
stdin.write('  file "/var/lib/bind/db.' +domain+'";\n')
stdin.flush()
stdin.write('  allow-update {\n')
stdin.flush()
stdin.write('    key '+domain+'.;\n')
stdin.flush()
stdin.write('  };\n')
stdin.flush()
stdin.write('};\n')
stdin.flush()
stdin.channel.shutdown_write()

#Set environment variables
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
dns_host = stdout.read()
dns_host = str(dns_host)
print('dns_host = '+dns_host)
stdin, stdout, stderr = ssh.exec_command("date +%Y%m%d%H")
date = stdout.read()
date = str(date)

print('Creating basic zone configuration')
logger.info("Creating basic zone configuration")
stdin, stdout, stderr = ssh.exec_command("sudo cat > /var/lib/bind/db."+domain )
stdin.write('$ORIGIN '+domain+'.\n')
stdin.flush()
stdin.write('$TTL 1h\n')
stdin.flush()
stdin.write('@ IN SOA ns admin\@'+domain+'. ( '+date+' 1d 2h 1w 30s )\n')
stdin.flush()
stdin.write('@ NS ns\n')
stdin.flush()
stdin.write('ns A ' + dns_ip + '\n')
stdin.flush()
#stdin.write('EOF')
stdin.channel.shutdown_write()
stdin, stdout, stderr = ssh.exec_command('sudo chown root:bind /var/lib/bind/db.' + domain)


#Now that BIND configuration is correct, kick it to reload.
print('Finished creating configurations')
logger.info("Finished creating configurations")
print('Reloading Bind service')
logger.info("Reloading Bind service")

stdin, stdout, stderr = ssh.exec_command('sudo service bind9 reload')
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

	
######################################## Get Bono IP ##########################################

def get_bono_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='bono_ip':
        bono_ip= i['output_value']
   return bono_ip[0]
################################# Configure Bono Node #########################################
#Get Bono IP
logger.info("Configure Bono Node")
logger.info("Get Bono IP")
bono_ip = get_bono_ip(heatclient , STACK_NAME)

#Connect to Bono
while True:
  try:
#    k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print ("Connecting To Bono Node with IP " + bono_ip)
    logger_ssh.info("Connecting To Bono Node")
    ssh.connect( hostname = bono_ip , username = "root", password = "root123" )
    print ("Connected")
    logger.info("Connected To Bono Node")
    break
  except:
    print("Could not connect. Retrying in 5 seconds...")
    error_logger.exception("Unable to Connect To Bono Node")
    time.sleep(5) 


# Log all output to file.
stdin, stdout, stderr = ssh.exec_command("exec > >(tee -a /var/log/clearwater-heat-bono.log) 2>&1")

# Configure the APT software source.
print("Configuring APT software source")
logger.info("Configuring APT software source")
stdin, stdout, stderr = ssh.exec_command("echo 'deb "+REPO_URL+" binary/' > /etc/apt/sources.list.d/clearwater.list")
stdin, stdout, stderr = ssh.exec_command("curl -L http://repo.cw-ngv.com/repo_key | apt-key add -")
stdin, stdout, stderr = ssh.exec_command("apt-get update")

# Configure /etc/clearwater/local_config.
print ("Configuring clearwater local settings")
logger.info("Configuring clearwater local settings")
stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/clearwater")
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
stdout.flush()
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
bono_host = stdout.read()
bono_host = str(bono_host)
print('BONO Private IP = '+bono_host)
stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
stdin.write('local_ip='+bono_host+'\n')
stdin.flush()
stdin.write('public_ip='+bono_ip+'\n')
stdin.flush()
stdin.write('public_hostname=bono-'+BONO_INDEX+'.'+domain+'\n')
stdin.flush()
stdin.write('etcd_cluster="192.168.0.1,192.168.0.3,192.168.0.4,192.168.0.5,192.168.0.6,192.168.0.7,192.168.0.8"')
stdin.channel.shutdown_write()

# Configure and upload /etc/clearwater/shared_config.
print ("Configuring clearwater shared settings")
logger.info("Configuring clearwater shared settings")
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/shared_config")
stdin.write('home_domain='+domain+'\n')
stdin.flush()
stdin.write('sprout_hostname=sprout.'+domain+'\n')
stdin.flush()
stdin.write('hs_hostname=hs.'+domain+':8888\n')
stdin.flush()
stdin.write('hs_provisioning_hostname=hs.'+domain+':8889\n')
stdin.flush()
stdin.write('ralf_hostname=ralf.'+domain+':10888\n')
stdin.flush()
stdin.write('xdms_hostname=homer.'+domain+':7888\n')
stdin.write('\n')
stdin.flush()
stdin.write('# Email server configuration\n')
stdin.flush()
stdin.write('smtp_smarthost=localhost\n')
stdin.flush()
stdin.write('smtp_username=username\n')
stdin.flush()
stdin.write('smtp_password=password\n')
stdin.flush()
stdin.write('email_recovery_sender=clearwater@dellnfv.org\n')
stdin.flush()
stdin.write('\n')
stdin.flush()            
stdin.write('# Keys\n')
stdin.flush()
stdin.write('signup_key=secret\n')
stdin.flush()
stdin.write('turn_workaround=secret\n')
stdin.flush()
stdin.write('ellis_api_key=secret\n')
stdin.flush()
stdin.write('ellis_cookie_key=secret\n')
stdin.channel.shutdown_write()

# Installing the software
print('Installing Bono packages....')
logger.info("Installing Bono packages.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install bono --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install bono --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break
	
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break

# Installing the software
print('Installing Bono packages....')
logger.info("Installing Bono packages.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install bono --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install bono --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break	

print('Installing SNMP...')
logger.info("Installing SNMP.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    

print('Installing SNMPD...')
logger.info("Installing SNMPD.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    
print('Finished Installation..')
logger.info("Finished Installation in BONO")
		
print('Uploading shared configuration')
logger.info("Uploading shared configuration")
stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/upload_shared_config")
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
print('Applying shared configuration')
logger.info("Applying shared configuration")
stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/apply_shared_config")	
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

#Update DNS Server
logger.info("Updating DNS server")
print('Updating DNS server')
stdin, stdout, stderr = ssh.exec_command("cat > update.sh")
stdin.write('#!/bin/bash\n')
stdin.flush()
stdin.write('retries=0\n')
stdin.flush()
stdin.write('while ! { nsupdate -y "'+domain+':evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==" -v << EOF\n')
stdin.flush()
stdin.write('server '+dns_ip+'\n')
stdin.flush()
stdin.write('debug yes\n')
stdin.flush()
stdin.write('update add bono-'+BONO_INDEX+'.'+domain+'. 30 A '+bono_ip+'\n')
stdin.flush()
stdin.write('update add '+domain+'. 30 A '+dns_ip+'\n')
stdin.flush()
stdin.write('update add '+domain+'. 30 NAPTR 0 0 "s" "SIP+D2T" "" _sip._tcp.'+domain+'.\n')
stdin.flush()
stdin.write('update add '+domain+'. 30 NAPTR 0 0 "s" "SIP+D2U" "" _sip._udp.'+domain+'.\n')
stdin.flush()
stdin.write('update add _sip._tcp.'+domain+'. 30 SRV 0 0 5060 bono-'+BONO_INDEX+'.'+domain+'.\n')
stdin.flush()
stdin.write('update add _sip._udp.'+domain+'. 30 SRV 0 0 5060 bono-'+BONO_INDEX+'.'+domain+'.\n')
stdin.flush()
stdin.write('send\n')			
stdin.flush()
stdin.write('EOF\n')
stdin.flush()
stdin.write('} && [ $retries -lt 10 ]\n')
stdin.flush()
stdin.write('do')
stdin.flush()
stdin.write('  retries=$((retries + 1))\n')
stdin.flush()
stdin.write("echo 'nsupdate failed - retrying (retry '$retries')...'\n")
stdin.flush()
stdin.write("sleep 5\n")
stdin.flush()
stdin.write("done\n")
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command('chmod 755 update.sh')
stdin, stdout, stderr = ssh.exec_command('./update.sh')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

#Configure MIB's
print('Configuring SNMP')
logger.info("Configuring SNMP")
sftp = ssh.open_sftp()
sftp.put( MIB_FILE_PATH, MIB_PATH )
sftp.put( MIB_FILE_PATH, '/usr/share/snmp/mibs/PROJECT-CLEARWATER-MIB.txt')
sftp.put( SNMP_FILE_PATH, SNMP_CONFIG_PATH )
stdin, stdout, stderr = ssh.exec_command("service snmpd restart")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
time.sleep(30)
stdin, stdout, stderr = ssh.exec_command("snmpwalk -v 2c -c clearwater localhost UCD-SNMP-MIB::memory")

# Use the DNS server.
stdin, stdout, stderr = ssh.exec_command("echo 'nameserver "+dns_ip+"' > /etc/dnsmasq.resolv.conf")
stdin, stdout, stderr = ssh.exec_command("echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq")
stdin, stdout, stderr = ssh.exec_command("service dnsmasq force-reload")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

ssh.close()
			
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
logger.info("configuring sprout")
logger.info("Get Sprout IP")
sprout_ip = get_sprout_ip(heatclient , STACK_NAME)

#Connect to Sprout
#k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
logger_ssh.info("Connecting To Sprout Node")
print ("Connecting To Sprout Node with IP " + sprout_ip)
ssh.connect( hostname = sprout_ip , username = "root", password = "root123" )
logger.info("Connected to Sprout")
print ("Connected")
stdin, stdout, stderr = ssh.exec_command("sudo -s")  

# Log all output to file.
stdin, stdout, stderr = ssh.exec_command("exec > >(tee -a /var/log/clearwater-heat-ellis.log) 2>&1")
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
sprout_host = stdout.read()
sprout_host = str(sprout_host)

# Configure the APT software source.
print("Configuring APT software source")
logger.info("Configuring APT software source")
stdin, stdout, stderr = ssh.exec_command("echo 'deb "+REPO_URL+" binary/' > /etc/apt/sources.list.d/clearwater.list")
stdin, stdout, stderr = ssh.exec_command("curl -L http://repo.cw-ngv.com/repo_key | apt-key add -")
stdin, stdout, stderr = ssh.exec_command("apt-get update")

# Configure /etc/clearwater/local_config.
print ("Configuring clearwater local settings")
logger.info("Configuring clearwater local settings")
stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/clearwater")
stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
stdin.write('local_ip='+sprout_host+'\n')
stdin.flush()
stdin.write('public_ip='+sprout_ip+'\n')
stdin.flush()
stdin.write('public_hostname=sprout-'+SPROUT_INDEX+'.'+domain+'\n')
stdin.flush()
stdin.write('etcd_cluster="192.168.0.1,192.168.0.3,192.168.0.4,192.168.0.5,192.168.0.6,192.168.0.7,192.168.0.8"')
stdin.channel.shutdown_write()

# Configure and upload /etc/clearwater/shared_config.
print ("Configuring clearwater shared settings")
logger.info("Configuring clearwater shared settings")
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/shared_config")
stdin.write('home_domain='+domain+'\n')
stdin.flush()
stdin.write('sprout_hostname=sprout.'+domain+'\n')
stdin.flush()
stdin.write('hs_hostname=hs.'+domain+':8888\n')
stdin.flush()
stdin.write('hs_provisioning_hostname=hs.'+domain+':8889\n')
stdin.flush()
stdin.write('ralf_hostname=ralf.'+domain+':10888\n')
stdin.flush()
stdin.write('xdms_hostname=homer.'+domain+':7888\n')
stdin.write('\n')
stdin.flush()
stdin.write('# Email server configuration\n')
stdin.flush()
stdin.write('smtp_smarthost=localhost\n')
stdin.flush()
stdin.write('smtp_username=username\n')
stdin.flush()
stdin.write('smtp_password=password\n')
stdin.flush()
stdin.write('email_recovery_sender=clearwater@dellnfv.org\n')
stdin.flush()
stdin.write('\n')
stdin.flush()            
stdin.write('# Keys\n')
stdin.flush()
stdin.write('signup_key=secret\n')
stdin.flush()
stdin.write('turn_workaround=secret\n')
stdin.flush()
stdin.write('ellis_api_key=secret\n')
stdin.flush()
stdin.write('ellis_cookie_key=secret\n')
stdin.channel.shutdown_write()

# Create /etc/chronos/chronos.conf.
logger.info("Create /etc/chronos/chronos.conf.")
stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/chronos")
stdin, stdout, stderr = ssh.exec_command("cat > /etc/chronos/chronos.conf")
stdin.write('[http]\n')
stdin.flush()
stdin.write('bind-address = '+sprout_host+'\n')
stdin.flush()
stdin.write('bind-port = 7253\n')
stdin.flush()
stdin.write('threads = 50\n')
stdin.flush()
stdin.write('\n')
stdin.flush()
stdin.write('[logging]\n')
stdin.flush()
stdin.write('folder = /var/log/chronos\n')
stdin.flush()
stdin.write('level = 2\n')
stdin.flush()
stdin.write('\n')
stdin.flush()
stdin.write('[alarms]\n')
stdin.flush()
stdin.write('enabled = true\n')
stdin.flush()
stdin.write('\n')
stdin.flush()
stdin.write('[exceptions]\n')
stdin.flush()
stdin.write('max_ttl = 600\n')
stdin.flush()
stdin.channel.shutdown_write()

# Now install the software.
print('Installing Sprout packages....')
logger.info("Installing Sprout packages.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install sprout --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....',
			time.sleep(30)

while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install sprout --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break
	
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-management --yes --force-yes")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....'
			time.sleep(30)
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes")
    print('Retrying Installation...')
    logger.info("Retrying Installation.")
    time.sleep(5)	
  else:
    break			

print('Installing Sprout packages....')
logger.info("Installing Sprout packages.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install sprout --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....',
			time.sleep(30)

while True:	
  if('Err' in stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install sprout --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    
    
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-chronos --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....',
			time.sleep(30)

while True:	
  if('Err' in stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-chronos --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break     

stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-astaire --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....',
			time.sleep(30)

while True:	
  if('Err' in stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-astaire --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break     
print('Installing SNMP...')
logger.info("Installing SNMP in Sprout")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    

print('Installing SNMPD...')
logger.info("Installing SNMPD in Sprout")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    
print('Finished Installation..')
logger.info("Finished Installation")
		 
       
print('Installed Sprout packages')
logger.info("Installed Sprout packages")
	
print('Uploading shared configuration')
logger.info("Uploading shared configuration")
stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/upload_shared_config")
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
print('Applying shared configuration')
logger.info("Applying shared configuration")
stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/apply_shared_config")	
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

#Update DNS Server
print('Updating DNS server')
logger_ssh.info("Updating DNS server")
stdin, stdout, stderr = ssh.exec_command("cat > update.sh")
stdin.write('#!/bin/bash\n')
stdin.flush()
stdin.write('retries=0\n')
stdin.flush()
stdin.write('while ! { nsupdate -y "'+domain+':evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==" -v << EOF\n')
stdin.flush()
stdin.write('server '+dns_ip+'\n')
stdin.flush()
stdin.write('debug yes\n')
stdin.flush()
stdin.write('update add sprout-'+SPROUT_INDEX+'.'+domain+'. 30 A '+sprout_host+'\n')
stdin.flush()
stdin.write('update add sprout.'+domain+'. 30 A '+sprout_host+'\n')
stdin.flush()
stdin.write('update add sprout.'+domain+'. 30 NAPTR 0 0 "s" "SIP+D2T" "" _sip._tcp.sprout.'+domain+'.\n')
stdin.flush()
stdin.write('update add _sip._tcp.sprout.'+domain+'. 30 SRV 0 0 5054 sprout-'+SPROUT_INDEX+'.'+domain+'.\n')
stdin.flush()
stdin.write('update add icscf.sprout.'+domain+'. 30 NAPTR 0 0 "s" "SIP+D2T" "" _sip._tcp.icscf.sprout.'+domain+'.\n')
stdin.flush()
stdin.write('update add _sip._tcp.icscf.sprout.'+domain+'. 30 SRV 0 0 5052 sprout-'+SPROUT_INDEX+'.'+domain+'.\n')
stdin.flush()
stdin.write('send\n')	
stdin.flush()
stdin.write('EOF\n')
stdin.flush()
stdin.write('} && [ $retries -lt 10 ]\n')
stdin.flush()
stdin.write('do')
stdin.flush()
stdin.write('  retries=$((retries + 1))\n')
stdin.flush()
stdin.write("echo 'nsupdate failed - retrying (retry '$retries')...'\n")
stdin.flush()
stdin.write("sleep 5\n")
stdin.flush()
stdin.write("done\n")
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command('chmod 755 ./update.sh')
stdin, stdout, stderr = ssh.exec_command('./update.sh')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

#Configure MIB's
print('Configuring SNMP')
logger.info("Configuring SNMP in Sprout")
sftp = ssh.open_sftp()
sftp.put( MIB_FILE_PATH, MIB_PATH )
sftp.put( MIB_FILE_PATH, '/usr/share/snmp/mibs/PROJECT-CLEARWATER-MIB.txt')
sftp.put( SNMP_FILE_PATH, SNMP_CONFIG_PATH )
stdin, stdout, stderr = ssh.exec_command("service snmpd restart")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
time.sleep(30)
stdin, stdout, stderr = ssh.exec_command("snmpwalk -v 2c -c clearwater localhost UCD-SNMP-MIB::memory")

# Use the DNS server.
stdin, stdout, stderr = ssh.exec_command("echo 'nameserver "+dns_ip+"' > /etc/dnsmasq.resolv.conf")
stdin, stdout, stderr = ssh.exec_command("echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq")
stdin, stdout, stderr = ssh.exec_command("service dnsmasq force-reload")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

ssh.close()			
#################################### Get Homer IP ##############################################

def get_homer_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='homer_ip':
        homer_ip= i['output_value']
   return homer_ip[0]

################################# Configure Homer Node #########################################
#Get Homer IP
logger.info("Configure Homer Node")
logger.info("Get Homer IP")
homer_ip = get_homer_ip(heatclient , STACK_NAME)

#Connect to Homer
#k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print ("Connecting To Homer Node with IP " + homer_ip)
logger_ssh.info("Connecting To Homer Node")
ssh.connect( hostname = homer_ip , username = "root", password = "root123")
print ("Connected")
logger.info("Connected To Homer Node")
stdin, stdout, stderr = ssh.exec_command("sudo -s")  

# Log all output to file.
stdin, stdout, stderr = ssh.exec_command("exec > >(tee -a /var/log/clearwater-heat-ellis.log) 2>&1")
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
homer_host = stdout.read()
homer_host = str(homer_host)

# Configure the APT software source.
print("Configuring APT software source")
logger.info("Configuring APT software source")
stdin, stdout, stderr = ssh.exec_command("echo 'deb "+REPO_URL+" binary/' > /etc/apt/sources.list.d/clearwater.list")
stdin, stdout, stderr = ssh.exec_command("curl -L http://repo.cw-ngv.com/repo_key | apt-key add -")
stdin, stdout, stderr = ssh.exec_command("apt-get update")

# Configure /etc/clearwater/local_config.
print ("Configuring clearwater local settings")
logger.info("Configuring clearwater local settings")
stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/clearwater")
stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
stdin.write('local_ip='+homer_host+'\n')
stdin.flush()
stdin.write('public_ip='+homer_ip+'\n')
stdin.flush()
stdin.write('public_hostname=homer-'+HOMER_INDEX+'.'+domain+'\n')
stdin.flush()
stdin.write('etcd_cluster="192.168.0.1,192.168.0.3,192.168.0.4,192.168.0.5,192.168.0.6,192.168.0.7,192.168.0.8"')
stdin.channel.shutdown_write()

# Configure and upload /etc/clearwater/shared_config.
print ("Configuring clearwater shared settings")
logger.info("Configuring clearwater shared settings")
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/shared_config")
stdin.write('home_domain='+domain+'\n')
stdin.flush()
stdin.write('sprout_hostname=sprout.'+domain+'\n')
stdin.flush()
stdin.write('hs_hostname=hs.'+domain+':8888\n')
stdin.flush()
stdin.write('hs_provisioning_hostname=hs.'+domain+':8889\n')
stdin.flush()
stdin.write('ralf_hostname=ralf.'+domain+':10888\n')
stdin.flush()
stdin.write('xdms_hostname=homer.'+domain+':7888\n')
stdin.write('\n')
stdin.flush()
stdin.write('# Email server configuration\n')
stdin.flush()
stdin.write('smtp_smarthost=localhost\n')
stdin.flush()
stdin.write('smtp_username=username\n')
stdin.flush()
stdin.write('smtp_password=password\n')
stdin.flush()
stdin.write('email_recovery_sender=clearwater@dellnfv.org\n')
stdin.flush()
stdin.write('\n')
stdin.flush()            
stdin.write('# Keys\n')
stdin.flush()
stdin.write('signup_key=secret\n')
stdin.flush()
stdin.write('turn_workaround=secret\n')
stdin.flush()
stdin.write('ellis_api_key=secret\n')
stdin.flush()
stdin.write('ellis_cookie_key=secret\n')
stdin.channel.shutdown_write()

# Now install the software.

print('Installing Homer packages...')
logger.info("Installing Homer packages.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    logger.info("Retrying Installation.")
    time.sleep(5)	
  else:
    break
			
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install homer --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....'
			time.sleep(30)
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install homer --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    logger.info("Retrying Installation.")
    time.sleep(5)	
  else:
    break
	
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-management --yes --force-yes")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....'
			time.sleep(30)
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-management --yes --force-yes")
    print('Retrying Installation...')
    logger.info("Retrying Installation.")
    time.sleep(5)	
  else:
    break

print('Installing Homer packages...')
logger.info("Installing Homer packages.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if('Err' in stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break
			
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install homer --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....'
			time.sleep(30)
while True:	
  if('Err' in stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install homer --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break
print('Installing SNMP...')
logger.info("Installing SNMP in Homer")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    

print('Installing SNMPD...')
logger.info("Installing SNMPD in Homer")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    
print('Finished Installation..')
logger.info("Finished Installation in Homer")
		    
print('Installed Homer packages')
	
print('Uploading shared configuration')
logger.info("Uploading shared configuration")
stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/upload_shared_config")
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
print('Applying shared configuration')
logger.info("Applying shared configuration")
stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/apply_shared_config")	
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
	
#Update DNS Server
print('Updating DNS server')
logger.info("Updating DNS server for homer")
stdin, stdout, stderr = ssh.exec_command("cat > update.sh")
stdin.write('#!/bin/bash\n')
stdin.flush()
stdin.write('retries=0\n')
stdin.flush()
stdin.write('while ! { nsupdate -y "'+domain+':evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==" -v << EOF\n')
stdin.flush()
stdin.write('server '+dns_ip+'\n')
stdin.flush()
stdin.write('debug yes\n')
stdin.flush()
stdin.write('update add homer-'+HOMER_INDEX+'.'+domain+'. 30 A '+homer_ip+'\n')
stdin.flush()
stdin.write('update add homer.'+domain+'. 30 A '+homer_host+'\n')
stdin.flush()
stdin.write('send\n')	
stdin.flush()
stdin.write('EOF\n')
stdin.flush()
stdin.write('} && [ $retries -lt 10 ]\n')
stdin.flush()
stdin.write('do')
stdin.flush()
stdin.write('  retries=$((retries + 1))\n')
stdin.flush()
stdin.write("echo 'nsupdate failed - retrying (retry '$retries')...'\n")
stdin.flush()
stdin.write("sleep 5\n")
stdin.flush()
stdin.write("done\n")
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command('chmod 755 update.sh')
stdin, stdout, stderr = ssh.exec_command('./update.sh')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

# Use the DNS server.
stdin, stdout, stderr = ssh.exec_command("echo 'nameserver "+dns_ip+"' > /etc/dnsmasq.resolv.conf")
stdin, stdout, stderr = ssh.exec_command("echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq")
stdin, stdout, stderr = ssh.exec_command("service dnsmasq force-reload")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
   
#################################### Get Homestead IP ###########################################

def get_homestead_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='homestead_ip':
        homestead_ip= i['output_value']
   return homestead_ip[0]

################################# Configure Homestead Node ######################################
#Get Homestead IP
logger.info("Configure Homestead Node")
logger.info("Get Homestead IP")
homestead_ip = get_homestead_ip(heatclient , STACK_NAME)

#Connect to Homestead
#k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print ("Connecting To Homestead Node with IP " + homestead_ip)
logger_ssh.info("Connecting To Homestead Node")
ssh.connect( hostname = homestead_ip , username = "root", password = "root123" )
print ("Connected")
logger.info("Connected To Homestead Node")
stdin, stdout, stderr = ssh.exec_command("sudo -s")  

# Log all output to file.
stdin, stdout, stderr = ssh.exec_command("exec > >(tee -a /var/log/clearwater-heat-homestead.log) 2>&1")
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
homestead_host = stdout.read()
homestead_host = str(homestead_host)

# Configure the APT software source.
print("Configuring APT software source")
logger.info("Configuring APT software source")
stdin, stdout, stderr = ssh.exec_command("echo 'deb "+REPO_URL+" binary/' > /etc/apt/sources.list.d/clearwater.list")
stdin, stdout, stderr = ssh.exec_command("curl -L http://repo.cw-ngv.com/repo_key | apt-key add -")
stdin, stdout, stderr = ssh.exec_command("apt-get update")

# Configure /etc/clearwater/local_config.
print ("Configuring clearwater local settings")
logger.info("Configuring clearwater local settings")
stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/clearwater")
stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
stdin.write('local_ip='+homestead_host+'\n')
stdin.flush()
stdin.write('public_ip='+homestead_ip+'\n')
stdin.flush()
stdin.write('public_hostname=homestead-'+HOMESTEAD_INDEX+'.'+domain+'\n')
stdin.flush()
stdin.write('etcd_cluster="192.168.0.1,192.168.0.3,192.168.0.4,192.168.0.5,192.168.0.6,192.168.0.7,192.168.0.8"')
stdin.channel.shutdown_write()

# Configure and upload /etc/clearwater/shared_config.
print ("Configuring clearwater shared settings")
logger.info("Configuring clearwater shared settings")
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/shared_config")
stdin.write('home_domain='+domain+'\n')
stdin.flush()
stdin.write('sprout_hostname=sprout.'+domain+'\n')
stdin.flush()
stdin.write('hs_hostname=hs.'+domain+':8888\n')
stdin.flush()
stdin.write('hs_provisioning_hostname=hs.'+domain+':8889\n')
stdin.flush()
stdin.write('ralf_hostname=ralf.'+domain+':10888\n')
stdin.flush()
stdin.write('xdms_hostname=homer.'+domain+':7888\n')
stdin.write('\n')
stdin.flush()
stdin.write('# Email server configuration\n')
stdin.flush()
stdin.write('smtp_smarthost=localhost\n')
stdin.flush()
stdin.write('smtp_username=username\n')
stdin.flush()
stdin.write('smtp_password=password\n')
stdin.flush()
stdin.write('email_recovery_sender=clearwater@dellnfv.org\n')
stdin.flush()
stdin.write('\n')
stdin.flush()            
stdin.write('# Keys\n')
stdin.flush()
stdin.write('signup_key=secret\n')
stdin.flush()
stdin.write('turn_workaround=secret\n')
stdin.flush()
stdin.write('ellis_api_key=secret\n')
stdin.flush()
stdin.write('ellis_cookie_key=secret\n')
stdin.channel.shutdown_write()

# Now install the software.
print('Installing Homestead packages...')
logger.info("Installing Homestead packages.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    logger.info("Retrying Installation.")
    time.sleep(5)	
  else:
    break
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install homestead homestead-prov --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install homestead homestead-prov --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    logger.info("Retrying Installation.")
    time.sleep(5)	
  else:
    break			

stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-management --yes --force-yes")   
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-management --yes --force-yes")
    print('Retrying Installation...')
    logger.info("Retrying Installation.")
    time.sleep(5)	
  else:
    break		

stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if('Err' in stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install homestead homestead-prov --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if('Err' in stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install homestead homestead-prov --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break

stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-homestead --yes --force-yes")   
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-homestead --yes --force-yes")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break		    		

print('Installing SNMP...')
logger.info("Installing SNMP in Homestead")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    

print('Installing SNMPD...')
logger.info("Installing SNMPD in Homestead")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    
print('Finished Installation..')
logger.info("Finished Installation in Homestead")
		    
print('Installed Homestead packages')	

#Configure MIB's
print('Configuring SNMP')
logger.info("Configure MIB's in Homer")
sftp = ssh.open_sftp()
sftp.put( MIB_FILE_PATH, MIB_PATH )
sftp.put( MIB_FILE_PATH, '/usr/share/snmp/mibs/PROJECT-CLEARWATER-MIB.txt')
sftp.put( SNMP_FILE_PATH, SNMP_CONFIG_PATH )
stdin, stdout, stderr = ssh.exec_command("service snmpd restart")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
time.sleep(30)
stdin, stdout, stderr = ssh.exec_command("snmpwalk -v 2c -c clearwater localhost UCD-SNMP-MIB::memory")

	
print('Uploading shared configuration')
logger.info("Uploading shared configuration")
stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/upload_shared_config")
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
print('Applying shared configuration')
logger.info("Applying shared configuration")
stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/apply_shared_config")	
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

#Update DNS Server
print('Updating DNS server')
logger.info("Updating DNS server for homestead")
stdin, stdout, stderr = ssh.exec_command("cat > update.sh")
stdin.write('#!/bin/bash\n')
stdin.flush()
stdin.write('retries=0\n')
stdin.flush()
stdin.write('while ! { nsupdate -y "'+domain+':evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==" -v << EOF\n')
stdin.flush()
stdin.write('server '+dns_ip+'\n')
stdin.flush()
stdin.write('debug yes\n')
stdin.flush()
stdin.write('update add homestead-'+HOMESTEAD_INDEX+'.'+domain+'. 30 A '+homestead_ip+'\n')
stdin.flush()
stdin.write('update add hs.'+domain+'. 30 A '+homestead_host+'\n')
stdin.flush()
stdin.write('send\n')	
stdin.flush()
stdin.write('EOF\n')
stdin.flush()
stdin.write('} && [ $retries -lt 10 ]\n')
stdin.flush()
stdin.write('do')
stdin.flush()
stdin.write('  retries=$((retries + 1))\n')
stdin.flush()
stdin.write("echo 'nsupdate failed - retrying (retry '$retries')...'\n")
stdin.flush()
stdin.write("sleep 5\n")
stdin.flush()
stdin.write("done\n")
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command('chmod 755 update.sh')
stdin, stdout, stderr = ssh.exec_command('./update.sh')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("./update.sh")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break		
# Use the DNS server.
stdin, stdout, stderr = ssh.exec_command("echo 'nameserver "+dns_ip+"' > /etc/dnsmasq.resolv.conf")
stdin, stdout, stderr = ssh.exec_command("echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq")
stdin, stdout, stderr = ssh.exec_command("service dnsmasq force-reload")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),	
#################################### Get Ellis IP ############################################

def get_ellis_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='ellis_ip':
        ellis_ip= i['output_value']
   return ellis_ip

################################# Configure Ellis Node #######################################
#Get Ellis IP
logger.info("Configure Ellis Node")
logger.info("Get Ellis IP")
ellis_ip = get_ellis_ip(heatclient , STACK_NAME)

#Connect to Ellis
while True:
  try:
#    k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print ("Connecting To Ellis Node with IP " + ellis_ip)
    logger_ssh.info("Connecting To Ellis Node")
    ssh.connect( hostname = ellis_ip , username = "root", password = "root123" )
    print ("Connected")
    logger.info("Connected To Ellis Node")
    break
  except:
    print("Could not connect. Retrying in 5 seconds...")
    error_logger.exception("Could not connect to Ellis.")
    time.sleep(5) 
	
stdin, stdout, stderr = ssh.exec_command("sudo -s")  

# Log all output to file.
stdin, stdout, stderr = ssh.exec_command("exec > >(tee -a /var/log/clearwater-heat-ellis.log) 2>&1")

# Configure the APT software source.
print("Configuring APT software source")
logger.info("Configuring APT software source")
stdin, stdout, stderr = ssh.exec_command("echo 'deb "+REPO_URL+" binary/' > /etc/apt/sources.list.d/clearwater.list")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
stdin, stdout, stderr = ssh.exec_command("curl -L http://repo.cw-ngv.com/repo_key | apt-key add -")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
stdin, stdout, stderr = ssh.exec_command("apt-get update")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),


#Get Private IP address
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
ellis_host = stdout.read()
ellis_host = str(ellis_host)

# Configure /etc/clearwater/local_config.
print ("Configuring clearwater local settings")
logger.info("Configuring clearwater local settings")
stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/clearwater")
stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
stdin.write('local_ip='+ellis_host+'\n')
stdin.flush()
stdin.write('public_ip='+ellis_ip+'\n')
stdin.flush()
stdin.write('public_hostname=ellis-'+ELLIS_INDEX+'.'+domain+'\n')
stdin.flush()
stdin.write('etcd_cluster="192.168.0.1,192.168.0.3,192.168.0.4,192.168.0.5,192.168.0.6,192.168.0.7,192.168.0.8"')
stdin.channel.shutdown_write()

# Installing the software
print ("Installing Ellis software packages....")
logger.info("Installing Ellis software packages.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install ellis --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....'
			time.sleep(30)
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install ellis --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break				
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes") 
print ("Installed Ellis packages")
logger.info("Installed Ellis software packages.")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....'
			time.sleep(30)
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break		
print('Installing SNMP...')
logger.info("Installing SNMP in Ellis")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    

print('Installing SNMPD...')
logger.info("Installing SNMPD in Ellis")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    
print('Finished Installation..')
		    
# Configure and upload /etc/clearwater/shared_config.
print ("Configuring clearwater shared settings")
logger.info("Configuring clearwater shared settings")
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/shared_config")
stdin.write('home_domain='+domain+'\n')
stdin.flush()
stdin.write('sprout_hostname=sprout.'+domain+'\n')
stdin.flush()
stdin.write('hs_hostname=hs.'+domain+':8888\n')
stdin.flush()
stdin.write('hs_provisioning_hostname=hs.'+domain+':8889\n')
stdin.flush()
stdin.write('ralf_hostname=ralf.'+domain+':10888\n')
stdin.flush()
stdin.write('xdms_hostname=homer.'+domain+':7888\n')
stdin.write('\n')
stdin.flush()
stdin.write('# Email server configuration\n')
stdin.flush()
stdin.write('smtp_smarthost=localhost\n')
stdin.flush()
stdin.write('smtp_username=username\n')
stdin.flush()
stdin.write('smtp_password=password\n')
stdin.flush()
stdin.write('email_recovery_sender=clearwater@dellnfv.org\n')
stdin.flush()
stdin.write('\n')
stdin.flush()            
stdin.write('# Keys\n')
stdin.flush()
stdin.write('signup_key=secret\n')
stdin.flush()
stdin.write('turn_workaround=secret\n')
stdin.flush()
stdin.write('ellis_api_key=secret\n')
stdin.flush()
stdin.write('ellis_cookie_key=secret\n')
stdin.channel.shutdown_write()
		
print('Uploading shared configuration')
logger.info("Uploading shared configuration")
stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/upload_shared_config")
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
print('Applying shared configuration')
logger.info("Applying shared configuration")
stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/apply_shared_config")	
#Display Output on screen
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

# Allocate a allocate a pool of numbers to assign to users.
print('Allocating a pool of numbers to assign users')
logger.info("Allocating a pool of numbers to assign users")
stdin, stdout, stderr = ssh.exec_command("/usr/share/clearwater/ellis/env/bin/python /usr/share/clearwater/ellis/src/metaswitch/ellis/tools/create_numbers.py --start "+DN_RANGE_START+" --count "+DN_RANGE_LENGTH)			

#Update DNS Server
print('Updating DNS server')
logger.info("Updating DNS server for ellis")
stdin, stdout, stderr = ssh.exec_command("cat > update.sh")
stdin.write('#!/bin/bash\n')
stdin.flush()
stdin.write('retries=0\n')
stdin.flush()
stdin.write('while ! { nsupdate -y "'+domain+':evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==" -v << EOF\n')
stdin.flush()
stdin.write('server '+dns_ip+'\n')
stdin.flush()
stdin.write('update add ellis-'+ELLIS_INDEX+'.'+domain+'. 30 A '+ellis_ip+'\n')
stdin.flush()
stdin.write('update add ellis.'+domain+'. 30 A '+ellis_ip+'\n')
stdin.flush()
stdin.write('debug yes\n')
stdin.flush()
stdin.write('send\n')
stdin.flush()
stdin.write('EOF\n')
stdin.flush()
stdin.write('} && [ $retries -lt 10 ]\n')
stdin.flush()
stdin.write('do')
stdin.flush()
stdin.write('  retries=$((retries + 1))\n')
stdin.flush()
stdin.write("echo 'nsupdate failed - retrying (retry '$retries')...'\n")
stdin.flush()
stdin.write("sleep 5\n")
stdin.flush()
stdin.write("done\n")
stdin.flush()
stdin.channel.shutdown_write()


stdin, stdout, stderr = ssh.exec_command('chmod 755 update.sh')

stdin, stdout, stderr = ssh.exec_command('./update.sh')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

# Use the DNS server.
stdin, stdout, stderr = ssh.exec_command("echo 'nameserver "+dns_ip+"' > /etc/dnsmasq.resolv.conf")
stdin, stdout, stderr = ssh.exec_command("echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq")
stdin, stdout, stderr = ssh.exec_command("service dnsmasq force-reload")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

ssh.close()		

#################################### Get Ralf IP ############################################

def get_ralf_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='ralf_ip':
        ralf_ip= i['output_value']
   return ralf_ip[0]

################################# Configure Ralf Node #######################################
#Get Ralf IP
logger.info("Configure Ralf Node")
logger.info("Get Ralf IP")
while True:
  try:
    ralf_ip = get_ralf_ip(heatclient , STACK_NAME)
    break
  except:
    print('Getting Ralf IP failed. Retring in 5 seconds...')
    time.sleep(5)

#Connect to Ralf
while True:
  try:
#    k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logger_ssh.info("Connecting To Ralf Node")
    print ("Connecting To Ralf Node with IP " + ralf_ip)
    ssh.connect( hostname = ralf_ip , username = "root", password = "root123" )
    print ("Connected")
    logger_ssh.info("Connected To Ralf Node")
    break
  except:
    error_logger.exception("Could not connect to Ralf.")
    print("Could not connect. Retrying in 5 seconds...")
    time.sleep(5) 

# Log all output to file.
stdin, stdout, stderr = ssh.exec_command("exec > >(tee -a /var/log/clearwater-heat-ellis.log) 2>&1")

# Configure the APT software source.
print("Configuring APT software source")
logger.info("Configuring APT software source")
stdin, stdout, stderr = ssh.exec_command("echo 'deb "+REPO_URL+" binary/' > /etc/apt/sources.list.d/clearwater.list")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
stdin, stdout, stderr = ssh.exec_command("curl -L http://repo.cw-ngv.com/repo_key | apt-key add -")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
stdin, stdout, stderr = ssh.exec_command("apt-get update")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),


#Get Private IP address
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
ralf_host = stdout.read()
ralf_host = str(ralf_host)

# Configure /etc/clearwater/local_config.
print ("Configuring clearwater local settings")
logger.info("Configuring clearwater local settings")
stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/clearwater")
stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
stdin.write('local_ip='+ralf_host+'\n')
stdin.flush()
stdin.write('public_ip='+ralf_ip+'\n')
stdin.flush()
stdin.write('public_hostname=ralf-'+ELLIS_INDEX+'.'+domain+'\n')
stdin.flush()
stdin.write('etcd_cluster="192.168.0.1,192.168.0.3,192.168.0.4,192.168.0.5,192.168.0.6,192.168.0.7,192.168.0.8"')
stdin.channel.shutdown_write()

# Installing the software
# Installing the software
print ("Installing Ralf software packages....")
logger.info("Installing Ralf software packages.")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install ralf --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....'
			time.sleep(30)
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install ralf --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break				
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes") 
print ("Installed Ralf packages")
logger.info("Installed Ralf software packages.")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....'
			time.sleep(30)
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break		
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-chronos --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....',
			time.sleep(30)

while True:	
  if('Err' in stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-chronos --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break     

stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-astaire --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print 'Installing....',
			time.sleep(30)

while True:	
  if('Err' in stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-astaire --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break     
print('Installing SNMP...')
logger.info("Installing SNMP in Ralf")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    

print('Installing SNMPD...')
logger.info("Installing SNMPD in Ralf")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break    
print('Finished Installation..')
logger.info("Finished Installation in Ralf")
		 
print('Installed Ralf packages') 
logger.info("Finished Installation in Ralf")
#Update DNS Server
print('Updating DNS server')
logger.info("Updating DNS server for Ralf")
stdin, stdout, stderr = ssh.exec_command("cat > update.sh")
stdin.write('#!/bin/bash\n')
stdin.flush()
stdin.write('retries=0\n')
stdin.flush()
stdin.write('while ! { nsupdate -y "'+domain+':evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==" -v << EOF\n')
stdin.flush()
stdin.write('server '+dns_ip+'\n')
stdin.flush()
stdin.write('debug yes\n')
stdin.flush()
stdin.write('update add ralf-'+ELLIS_INDEX+'.'+domain+'. 30 A '+ralf_ip+'\n')
stdin.flush()
stdin.write('update add ralf.'+domain+'. 30 A '+ralf_host+'\n')
stdin.flush()
stdin.write('send\n')	
stdin.flush()
stdin.write('EOF\n')
stdin.flush()
stdin.write('} && [ $retries -lt 10 ]\n')
stdin.flush()
stdin.write('do')
stdin.flush()
stdin.write('  retries=$((retries + 1))\n')
stdin.flush()
stdin.write("echo 'nsupdate failed - retrying (retry '$retries')...'\n")
stdin.flush()
stdin.write("sleep 5\n")
stdin.flush()
stdin.write("done\n")
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command('chmod 755 update.sh')
stdin, stdout, stderr = ssh.exec_command('./update.sh')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

# Use the DNS server.
stdin, stdout, stderr = ssh.exec_command("echo 'nameserver "+dns_ip+"' > /etc/dnsmasq.resolv.conf")
stdin, stdout, stderr = ssh.exec_command("echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq")
stdin, stdout, stderr = ssh.exec_command("service dnsmasq force-reload")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

ssh.close()		

################################### Print Cluster Details ######################################

#Get credentials again, Heat creds expire after 1 hour
cred = get_keystone_creds(config)
ks_client = Keystone_Client(**cred)
heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token, username='admin', passwork='admin')
#Get Homestead IP
homestead_ip = get_homestead_ip(heatclient , STACK_NAME)
  


print("*************************")
print ("Domain = " + domain)
print ("Bono IP = " + bono_ip)
print ("Homestead IP = " + homestead_ip)
print ("Homer IP = " + homer_ip)
print("*************************")

print ('Finished deploying IMS')
print ('To see the scaling status see file "scale_progress')
time.sleep(10)
os.system("nohup python monitor.py > scale_progress&")
#system("screen -S 'IMS'")

# ################################## Get Homestead information ###################################
# while True:

#   #Connect to Homestead
#   #k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
#   ssh = paramiko.SSHClient()
#   ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#   print ("Connecting To Homestead Node with IP " + homestead_ip)
#   ssh.connect( hostname = homestead_ip , username = "root", password = "root123" )
#   print ("Connected")
#   stdin, stdout, stderr = ssh.exec_command("sudo -s")  
  
  
#   #print('Checking MIB libraries')
#   #stdin, stdout, stderr = ssh.exec_command("snmpwalk -v2c -c clearwater localhost PROJECT-CLEARWATER-MIB::dataConnection")
#   #while not stdout.channel.exit_status_ready():
#   #	# Only print data if there is data to read in the channel 
#   #	if stdout.channel.recv_ready():
#   #		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
#   #		if len(rl) > 0:
#   #			# Print data from stdout
#   #			print stdout.channel.recv(1024),
      
#   os.system('clear')
      
#   stdin, stdout, stderr = ssh.exec_command("snmpwalk -v2c -c clearwater localhost PROJECT-CLEARWATER-MIB::homesteadIncomingRequestsCount.scopeCurrent5MinutePeriod ")
#   mib_data = stdout.read()
#   mib_data = str(mib_data)
#   data = mib_data.split()
#   no_of_incomming_requests =  data[3]
  
#   stdin, stdout, stderr = ssh.exec_command("snmpwalk -v2c -c clearwater localhost PROJECT-CLEARWATER-MIB::homesteadRejectedOverloadCount.scopeCurrent5MinutePeriod ")
#   mib_data = stdout.read()
#   mib_data = str(mib_data)
#   data = mib_data.split()
#   no_of_rejected_requests =  data[3]
#   print("*************************")
#   print ("Domain = " + domain)
#   print ("Bono IP = " + bono_ip)
#   print ("Homestead IP = " + homestead_ip)
#   print ("Homer IP = " + homer_ip)
#   print("*************************")
#   print ('**************************************************************')
#   print ('Number of incomming requests in the current 5 minute period= '+ no_of_incomming_requests )
#   print ('Number of incomming rejected requests in the current 5 minute period due to overload= '+ no_of_rejected_requests )
#   print ('**************************************************************')
  
#   if (int(no_of_incomming_requests) > int(CALL_THRESHOLD) and SCALE_UP == False):
#   #   #Connect to Local Node
#   #   #k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
#   #   ssh = paramiko.SSHClient()
#   #   ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#   #   print ("Connecting To local Node with IP " + LOCAL_IP)
#   #   ssh.connect( hostname = LOCAL_IP , username = "root", password = "r00tme" )
#   #   print ("Connected")
#   #   logger.info("scaling Up")
#   #   stdin, stdout, stderr = ssh.exec_command("python /root/vIMS/Scale.py")  
#   #   while not stdout.channel.exit_status_ready():
#   # 	# Only print data if there is data to read in the channel 
#   # 	  if stdout.channel.recv_ready():
#   # 		  rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
#   #  		  if len(rl) > 0:
#   # 			# Print data from stdout
#   # 			  print stdout.channel.recv(1024),    
#     SCALE_UP = True    
#   # print(int(no_of_incomming_requests))
#   # print(int(CALL_THRESHOLD))  
#     Scale.scale_up()
  
  
#   if(int(no_of_incomming_requests) < int(CALL_LOWER_THRESHOLD) and SCALE_UP == True):
#    #  #Connect to Local Node
#    #  #k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
#    #  ssh = paramiko.SSHClient()
#    #  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#    #  print ("Connecting To local Node with IP " + LOCAL_IP)
#    #  ssh.connect( hostname = LOCAL_IP , username = "root", password = "r00tme" )
#    #  print ("Connected")
#    #  stdin, stdout, stderr = ssh.exec_command("python /root/vIMS/Scale_down.py")  
#    #  while not stdout.channel.exit_status_ready():
#   	# # Only print data if there is data to read in the channel 
#   	#   if stdout.channel.recv_ready():
#   	# 	  rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
#    # 		  if len(rl) > 0:
#   	# 		# Print data from stdout
#   	# 		  print stdout.channel.recv(1024),
#     SCALE_UP = False
#     Scale_down.scale_down()
    
#   time.sleep(30)

