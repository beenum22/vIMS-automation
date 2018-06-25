#!/bin/bash

# Log all output to file.
exec > >(tee -a /var/log/clearwater-heat-dime.log) 2>&1
set -x

# Set up the signaling network namespace on each boot by creating an init file and
# linking to it from runlevel 2 and 3
cat >/etc/init.d/signaling_namespace <<EOF
#!/bin/bash
# Create the signaling namespace and configure its interfaces.
set -e

# Exit if the namespace is already set up.
ip netns list | grep -q signaling && exit 0

# eth1 is the signaling interface (and eth0 is the management interface).
# We need to set eth1 up manually - only eth0 is automatically configured via DHCP.
ip netns add signaling
ip link set eth1 netns signaling
ip netns exec signaling ip link set dev lo up
ip netns exec signaling ip addr add __private_sig_ip__/$(echo __private_sig_cidr__ | cut -d / -f 2) dev eth1
ip netns exec signaling ip link set dev eth1 up
ip netns exec signaling ip route add default via __private_sig_gateway__
EOF

chmod a+x /etc/init.d/signaling_namespace
ln -s /etc/init.d/signaling_namespace /etc/rc2.d/S01signaling_namespace
ln -s /etc/init.d/signaling_namespace /etc/rc3.d/S01signaling_namespace

# Also set up the signaling namespace now.
/etc/init.d/signaling_namespace

# Configure the APT software source.
echo 'deb __repo_url__ binary/' > /etc/apt/sources.list.d/clearwater.list
curl -L http://repo.cw-ngv.com/repo_key | apt-key add -
apt-get update

# Configure /etc/clearwater/local_config.
mkdir -p /etc/clearwater
etcd_ip=__etcd_ip__
[ -n "$etcd_ip" ] || etcd_ip=__private_mgmt_ip__
cat > /etc/clearwater/local_config << EOF
signaling_namespace=signaling
signaling_dns_server=__dns_vip_sig__
management_local_ip=__private_mgmt_ip__
local_ip=__private_sig_ip__
public_ip=__private_sig_ip__
public_hostname=dime-__index__.__zone__
etcd_cluster=$etcd_ip
EOF

# Now install the software.
DEBIAN_FRONTEND=noninteractive apt-get install dime --yes --force-yes
DEBIAN_FRONTEND=noninteractive apt-get install clearwater-management --yes --force-yes

# Set up SNMP
#apt-get -y install python-pip
#pip install docopt && apt-get install -y smitools git 
apt-get install -y git smitools clearwater-snmpd
#mkdir /root/clearwater-mibs
pip install docopt
git clone https://github.com/Metaswitch/clearwater-snmp-handlers.git $HOME/clearwater-mibs/clearwater-snmp-handlers && python $HOME/clearwater-mibs/clearwater-snmp-handlers/mib-generator/cw_mib_generator.py $HOME/clearwater-mibs
cp $HOME/clearwater-mibs/PROJECT-CLEARWATER-MIB /etc/snmp && cp $HOME/clearwater-mibs/PROJECT-CLEARWATER-MIB /usr/share/snmp/mibs/
echo "mibs +PROJECT-CLEARWATER-MIB" > /etc/snmp/snmp.conf
echo "view clearwater included .1.3.6.1.4.1.2021.10" >> /etc/snmp/snmpd.conf
service snmpd restart

# Function to give DNS record type and IP address for specified IP address
ip2rr() {
  if echo $1 | grep -q -e '[^0-9.]' ; then
    echo AAAA $1
  else
    echo A $1
  fi
}

# Update DNS master
retries=0
while ! { nsupdate -y "__zone__:__dnssec_key__" -v << EOF
server __dns_mgmt_ip_1__
update add dime-__index__.__zone__. 30 $(ip2rr __private_mgmt_ip__)
update add ralf.__zone__. 30 $(ip2rr __private_sig_ip__)
update add hs.__zone__. 30 $(ip2rr __private_sig_ip__)
update add hs-prov.__zone__. 30 $(ip2rr __private_mgmt_ip__)
send
EOF
} && [ $retries -lt 10 ]
do
  retries=$((retries + 1))
  echo 'nsupdate failed - retrying (retry '$retries')...'
  sleep 5
done

# Update DNS backup
retries=0
while ! { nsupdate -y "__zone__:__dnssec_key__" -v << EOF
server __dns_mgmt_ip_2__
update add dime-__index__.__zone__. 30 $(ip2rr __private_mgmt_ip__)
update add ralf.__zone__. 30 $(ip2rr __private_sig_ip__)
update add hs.__zone__. 30 $(ip2rr __private_sig_ip__)
update add hs-prov.__zone__. 30 $(ip2rr __private_mgmt_ip__)
send
EOF
} && [ $retries -lt 10 ]
do
  retries=$((retries + 1))
  echo 'nsupdate failed - retrying (retry '$retries')...'
  sleep 5
done

# Use the DNS server.
echo 'nameserver __dns_vip_mgmt__' > /etc/dnsmasq.resolv.conf
#echo 'nameserver __dns_vip_mgmt__' | cat - /etc/resolv.conf > temp && mv temp /etc/resolv.conf
echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq
mkdir -p /etc/netns/signaling
echo 'nameserver __dns_vip_sig__' > /etc/netns/signaling/resolv.conf
service dnsmasq force-reload
