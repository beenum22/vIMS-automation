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
filename_activity = PATH+'/logs/Stress_test_' + date_time + '.log'
filename_error = PATH+'/logs/Stress_test_error_' + date_time + '.log'

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
os.environ['IMAGE_PATH'] = PATH+'/IMG'
CONFIG_PATH = PATH+'/configurations.json'
USER_CONFIG_PATH = PATH+'/user_config.json'
STACK_NAME = 'IBCF'
REPO_URL = 'http://repo.cw-ngv.com/stable'
ELLIS_INDEX = '0'
BONO_INDEX = '0'
SPROUT_INDEX = '0'
HOMESTEAD_INDEX = '0'
HOMER_INDEX = '0'
MIB_PATH = "/usr/share/mibs/PROJECT-CLEARWATER-MIB.txt"
MIB_FILE_PATH = PATH+"/PROJECT-CLEARWATER-MIB.txt"
SNMP_CONFIG_PATH = '/etc/snmp/snmpd.conf'
SNMP_FILE_PATH = PATH+'/snmpd.conf'
############################## User Configuration Functions ##############################

def get_user_configurations():
	file = open(USER_CONFIG_PATH)
	configurations = json.load(file)
	file.close()
	return configurations

print('Getting user confiurations...')
logger.info("Getting user confiurations.")
user_config = get_user_configurations()
ext_net = user_config['networks']['external']
ext_net = str(ext_net)
domain = user_config['domain']['zone']
domain = str(domain)
IBCF_ip = user_config['IBCF']['IP']
IBCF_ip = str(IBCF_ip)
IBCF_domain = user_config['IBCF']['domain']
IBCF_domain = str(IBCF_domain)

print('Successfull')
logger.info("Getting user confiurations Successfull.")

############################## Environment Based Credential functions ####################

def keytsone_auth(name, configurations, logger, error_logger):
  keystone = ''
  logger.info("Creating authorized instance of keystone client")
  if name == 'Red Hat':
    # get credentials for keystone
    logger.info("Getting keystone credentials for authorization ...")
    credsks = get_keystone_creds(configurations)
    # get authorized instance of keystone
    logger.info("Getting authorized instance of keystone client")
    try:
      keystone = ksClient.Client(**credsks)
    except:
      error_logger.exception("Unable to create keystone client instance")
      print("[" + time.strftime("%H:%M:%S")+ "] Error creating keystone client, please check logs ...")
      sys.exit()
  elif (name == 'CentOS') or (name == 'Wind River') or (name == 'Ubuntu'):
    try:
      keystone = ksClient.Client(auth_url = configurations['os-creds']['os-authurl'],
                   username = configurations['os-creds']['os-user'],
                   password = configurations['os-creds']['os-pass'],
                   tenant_name = configurations['os-creds']['os-tenant-name'])
      
    except:
      error_logger.exception("Unable to create keyclient instance...")
      print ("[" + time.strftime("%H:%M:%S")+ "] Error creating keystone client, please check logs ...")
      sys.exit()
  logger.info("Authorized keystone instance ....")
  logger.info("Environment is " + name + " ...")
  return keystone

#========================================================#
def nova_auth(name, configurations, logger_nova, error_logger):
  nova_creds = get_nova_creds(configurations)
  nova = ''
  logger_nova.info("Creating authorized instance of nova client instance ...")
  if name == 'Red Hat':
    # get authorized instance of nova client
    logger_nova.info("Getting authorized instance to use Nova client API ...")
    try:
      auth = v2.Password(auth_url = nova_creds['auth_url'],
                username = nova_creds['username'],
                password = nova_creds['password'],
                tenant_name = nova_creds['project_id'])
      sess = session.Session(auth = auth)
      nova = client.Client(nova_creds['version'], session = sess)
    except:
      error_logger.exception("Unable to create nova client instance")
      print("[" + time.strftime("%H:%M:%S")+ "] Error authorizing nova client, please check logs ...")
      sys.exit()
  elif (name == 'CentOS') or (name == 'Wind River') or (name == 'Ubuntu'):
    try:      
      nova = client.Client('1.1', configurations['os-creds']['os-user'], 
                configurations['os-creds']['os-pass'], configurations['os-creds']['os-tenant-name'], 
                configurations['os-creds']['os-authurl'])
      
    except:
      error_logger.exception("Unable to create nova client instance ...")
      print ("[" + time.strftime("%H:%M:%S")+ "] Error authorizing nova client, please check logs ...")
      sys.exit()
  logger_nova.info("Authorized nova instance ....")
  logger_nova.info("Environment is " + name + " ...")
  return nova
#=========================================================#
def neutron_auth(name, configurations, logger_neutron, error_logger):
  credsks = get_keystone_creds(configurations)
  neutron = ''
  logger_neutron.info("Creating authorized instance of neutron client instance ...")
  if name == 'Red Hat':
    # get authorized instance of neutron client
    logger_neutron.info("Getting authorized instance of neutron client")
    try:
      neutron = ntrnclient.Client(**credsks)
    except:
      error_logger.exception("Unable to create neutron client instance")
      print("[" + time.strftime("%H:%M:%S")+ "] Error authorizing neutron client API, please check logs ...")
      sys.exit()
  elif (name == 'CentOS') or (name == 'Wind River') or (name == 'Ubuntu'):
    try:
      neutron = ntrnclient.Client(auth_url = configurations['os-creds']['os-authurl'],
                   username = configurations['os-creds']['os-user'],
                   password = configurations['os-creds']['os-pass'],
                   tenant_name = configurations['os-creds']['os-tenant-name'],
                   region_name = configurations['os-creds']['os-region-name'])
    except:
      error_logger.exception("Unable to create neutron client instance")
      print ("[" + time.strftime("%H:%M:%S")+ "] Error creating neutron client, please check logs ...")
      sys.exit()
  logger_neutron.info("Authorized neutron instance ....")
  logger_neutron.info("Environment is " + name + " ...")
  return neutron
#========================================================#
def glance_auth(name, configurations, keystone, logger_glance, error_logger):
  glance = ''
  logger_glance.info("Creating authorized instance of glance client instance ...")
  if name == 'Red Hat':
    #authorizing glance client
    logger_glance.info("Getting authorized instance of glance client")
    try:
      glance_endpoint = keystone.service_catalog.url_for(service_type = 'image', endpoint_type = 'publicURL')
      glance = glanceclient.Client('2', glance_endpoint, token = keystone.auth_token)
    except:
      error_logger.exception("Unable to create glance client instance")
      print("[" + time.strftime("%H:%M:%S")+ "] Error creating glance client, please check logs ...")
      sys.exit()
  elif (name == 'CentOS') or (name == 'Wind River') or (name == 'Ubuntu'):
    try:
      glance_endpoint = keystone.service_catalog.url_for(service_type = 'image', endpoint_type = 'publicURL')
      glance = glclient.Client('2', glance_endpoint, token = keystone.auth_token)
    except:
      error_logger.exception("Unable to create glance client instance")
      print ("[" + time.strftime("%H:%M:%S")+ "] Error creating glance client, please check logs ...")
      sys.exit()
  logger_glance.info("Authorized glance instance ....")
  logger_glance.info("Environment is " + name + " ...")
  return glance

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
logger.info("Credentials Loaded")  
config = get_configurations()
logger.info("Getting keystone credentials")
credsks = get_keystone_creds(config)
logger_nova.info("Getting Nova Credentials")
creds = get_nova_creds(config)

# Get authorized instance of nova client
logger_nova.info("Getting authorized instance of nova client")
nova = nvclient.Client(**creds)   
# Get authorized instance of neutron client
logger_neutron.info("Get authorized instance of neutron client")
neutron = ntrnclient.Client(**credsks)

name = check_env(logger, error_logger)

print ('Environment is ' + name)
#authenticating client APIs
if name != 'unknown-environment':
  
  keystone = keytsone_auth(name, config, logger, error_logger)

  nova = nova_auth(name, config, logger_nova, error_logger)

  neutron = neutron_auth(name, config, logger_neutron, error_logger)

  glance = glance_auth(name, config, keystone, logger_glance, error_logger)
else:
  name = 'CentOS'
  keystone = keytsone_auth(name, config, logger, error_logger)

  nova = nova_auth(name, config, logger_nova, error_logger)

  neutron = neutron_auth(name, config, logger_neutron, error_logger)

  glance = glance_auth(name, config, keystone, logger_glance, error_logger)
##

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
logger.info("Fetch network ID of network netname")

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
logger.info("Fetch network ID of private network")

############################## Heat Stack Create ##########################################
def create_cluster(heat,cluster_name):
  cluster_full_name=STACK_NAME

  file_main= open(PATH+'/test.yaml', 'r')                

  cluster_body={
   "stack_name":cluster_full_name,
   "template":file_main.read(),
   "parameters": {
   "name": "IBCF-1",
   "public_net_id": net_id,
   "zone" : domain,
   "flavor": "m1.medium",
   "image": "IMS",     
	"key_name":"secure",
   "private_net_id": private_id
 #    "availability_zone":"compute1"
     }
    }
  #try:  
  logger.info("Create Heat stack")
  heat.stacks.create(**cluster_body)
  #except:
  #print ("There is an error creating cluster, exiting...")
  #sys.exit()
  print ("Creating stack "+ cluster_full_name )

########################### Create Heat Stack from credentials of keystone #####################
logger.info("creating heat endpoint")
heat_endpoint = keystone.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
logger.info("creating heat client")
heatclient = Heat_Client('1', heat_endpoint, token=keystone.auth_token, username='admin', password='admin')
logger.info("creating heatstack Cluster")
create_cluster(heatclient,STACK_NAME)
#stack = heatclient.stacks.list()
#print stack.next()
logger.info("deploying heat stack")
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

dns_ip = get_dns_ip(heatclient , "IMS")

print "DNS IP = "+dns_ip 

#################################### Get Sprout IP ############################################
def get_sprout_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='sprout_ip':
        sprout_ip= i['output_value']
   return sprout_ip[0]
sprout_ip = get_sprout_ip(heatclient , 'IMS')
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
logger.info("Getting bono IP")
bono_ip = get_bono_ip(heatclient , 'IMS')
##################################### Get Node IP ################################################

def get_node_ip(heat, cluster_name):
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='public_ip':
        public_ip= i['output_value']
   return public_ip

################################# Configure Test Node #########################################
#Get Node IP
logger.info("configure test node")
logger.info("getting node IP")
node_ip = get_node_ip(heatclient , STACK_NAME)
print('Waiting for the test node to spawn...')
time.sleep(60) # wait for VM to spawn
#Connect to Node
while True:
  try:
#    k = paramiko.RSAKey.from_private_key_file("/root/.ssh/test.pem")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logger_ssh.info("Connecting To Test Node")
    print ("Connecting To Test Node with IP " + node_ip)
    ssh.connect( hostname = node_ip , username = "root", password = "root123" )
    logger_ssh.info("Connected To Test Node")
    print ("Connected")
    break
  except:
    error_logger.exception("Unable to connect to test node")
    print("Could not connect. Retrying in 5 seconds...")
    time.sleep(5)    

stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
node_host = stdout.read()
node_host = str(node_host)


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
print('BONO Private IP = '+node_host)
#stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
stdin.write('local_ip='+node_host+'\n')
stdin.flush()
stdin.write('public_ip='+node_ip+'\n')
stdin.flush()
stdin.write('public_hostname=IBCF-'+BONO_INDEX+'.'+domain+'\n')
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
stdin.write('update add IBCF-'+BONO_INDEX+'.'+domain+'. 30 A '+node_ip+'\n')
stdin.flush()
stdin.write('update add '+domain+'. 30 A '+dns_ip+'\n')
stdin.flush()
stdin.write('update add '+domain+'. 30 NAPTR 0 0 "s" "SIP+D2T" "" _sip._tcp.'+domain+'.\n')
stdin.flush()
stdin.write('update add '+domain+'. 30 NAPTR 0 0 "s" "SIP+D2U" "" _sip._udp.'+domain+'.\n')
stdin.flush()
stdin.write('update add _sip._tcp.'+domain+'. 30 SRV 0 0 5060 IBCF-'+BONO_INDEX+'.'+domain+'.\n')
stdin.flush()
stdin.write('update add _sip._udp.'+domain+'. 30 SRV 0 0 5060 IBCF-'+BONO_INDEX+'.'+domain+'.\n')
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

#Configure trusted peer list
print ("Configuring trusted peer list")
stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/user_settings")
stdin.write('trusted_peers='+IBCF_ip+'\n') # IP OF OTHER IBCF
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command("service bono stop")
ssh.close()

################################# Configure Sprout Node #######################################

#Connect to Sprout
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

stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/bgcf.json")
stdin.write('{\n')
stdin.flush()
stdin.write('\n')
stdin.flush()
stdin.write('    "routes" : [\n')
stdin.flush()
stdin.write('\n')
stdin.flush()
stdin.write('            { "name" : "Routing to '+IBCF_domain+'",\n')
stdin.flush()
stdin.write('\n')
stdin.write('              "domain" : "'+IBCF_domain+'",\n')
stdin.flush()
stdin.write('\n')
stdin.flush()
stdin.write('              "route"  :\n')
stdin.flush()
stdin.write('["sip:'+node_host+'","sip:'+IBCF_ip+':5060"]\n')
stdin.flush()
stdin.write('\n')
stdin.flush()
stdin.write('            }\n')
stdin.flush()
stdin.write('\n')
stdin.flush()
stdin.write('    ]\n')
stdin.flush()
stdin.write('\n')
stdin.flush()
stdin.write('}\n')  
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/upload_bgcf_json")

ssh.close()
