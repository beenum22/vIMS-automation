#!/bin/bash

# Log all output to file.
exec > >(tee -a /var/log/clearwater-heat-monit.log) 2>&1
set -x

# Install Cacti
#apt install -y apache2 mariadb-server mariadb-client php5-mysql libapache2-mod-php5
#apt-get -y install php5-ldap php5-gd php5-gmp
#apt-get -y install snmp php5-snmp rrdtool librrds-perl

echo 'deb __repo_url__ binary/' > /etc/apt/sources.list.d/clearwater.list
#echo 'deb http://repo.cw-ngv.com/stable binary/' > /etc/apt/sources.list.d/clearwater.list

curl -L http://repo.cw-ngv.com/repo_key | apt-key add -

curl https://packagecloud.io/gpg.key | apt-key add -
add-apt-repository "deb https://packagecloud.io/grafana/stable/debian/ stretch main"
curl -sL https://repos.influxdata.com/influxdb.key | apt-key add -
source /etc/lsb-release
echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | tee /etc/apt/sources.list.d/influxdb.list

# Install Grafana, InfluxDB, and Telegraph

apt-get update
apt-get install -y snmp smitools git python-pip snmp-mibs-downloader gcc python-dev libsnmp-dev
pip install docopt easysnmp ipaddress influxdb
git clone https://github.com/jplana/python-etcd $HOME/python-etcd && cd $HOME/python-etcd && python setup.py install && cd $HOME
git clone https://github.com/Metaswitch/clearwater-snmp-handlers.git $HOME/clearwater-mibs/clearwater-snmp-handlers && python $HOME/clearwater-mibs/clearwater-snmp-handlers/mib-generator/cw_mib_generator.py $HOME/clearwater-mibs
cp $HOME/clearwater-mibs/PROJECT-CLEARWATER-MIB /etc/snmp && cp $HOME/clearwater-mibs/PROJECT-CLEARWATER-MIB /usr/share/snmp/mibs/
echo "mibs +PROJECT-CLEARWATER-MIB" > /etc/snmp/snmp.conf
service snmpd restart

apt-get install -y influxdb grafana telegraf
service influxdb start
service influxdb start
service telegraf start
service grafana-server start
grafana-server web
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 3000

service influxdb enable
service telegraf enable
service grafana-server enable

#mkdir /root/monitoring_data
#mkdir /root/monitoring_data/service
cat > /root/monitoring_data/bono_sample_snmp.conf << EOF
[[inputs.snmp]]
  agents = [ "<agent_ip:agent_port>" ]
  version = 2
  community = "clearwater"
  name = "<agent_hostname>"

  [[inputs.snmp.field]]
    name = "bonoConnectedClients"
    oid = ".1.2.826.0.1.1578918.9.2.1.0"

  [[inputs.snmp.field]]
    name = "bonoLatencyCount"
    oid = ".1.2.826.0.1.1578918.9.2.2.1.7.2.4.110.111.100.101"

  [[inputs.snmp.field]]
    name = "bonoIncomingRequestsCount"
    oid = ".1.2.826.0.1.1578918.9.2.4.1.3.2.4.110.111.100.101"

  [[inputs.snmp.field]]
    name = "bonoRejectedOverloadCount"
    oid = ".1.2.826.0.1.1578918.9.2.5.1.3.2.4.110.111.100.101"

  [[inputs.snmp.field]]
    name = "bonoQueueSizeAverage"
    oid = ".1.2.826.0.1.1578918.9.2.6.1.3.2.4.110.111.100.101"
  [[inputs.snmp.field]]
    name = "cpuLoad"
    oid = ".1.3.6.1.4.1.2021.10.1.3.2"
EOF

cat > /root/monitoring_data/sprout_sample_snmp.conf << EOF
[[inputs.snmp]]
  agents = [ "<agent_ip:agent_port>" ]
  version = 2
  community = "clearwater"
  name = "<agent_hostname>"

  [[inputs.snmp.field]]
    name = "sproutLatencyAverage"
    oid = ".1.2.826.0.1.1578918.9.3.1.1.3.2.4.110.111.100.101"

  [[inputs.snmp.field]]
    name = "sproutIncomingRequestsCount"
    oid = ".1.2.826.0.1.1578918.9.3.6.1.3.2.4.110.111.100.101"

  [[inputs.snmp.field]]
    name = "sproutRejectedOverloadCount"
    oid = ".1.2.826.0.1.1578918.9.3.7.1.3.2.4.110.111.100.101"

  [[inputs.snmp.field]]
    name = "sproutQueueSizeAverage"
    oid = ".1.2.826.0.1.1578918.9.3.8.1.3.2.4.110.111.100.101"
  [[inputs.snmp.field]]
    name = "cpuLoad"
    oid = ".1.3.6.1.4.1.2021.10.1.3.2"
EOF

cat > /root/monitoring_data/sample_snmp.conf << EOF
[[inputs.snmp]]
  agents = [ "<agent_ip:agent_port>" ]
  version = 2
  community = "clearwater"
  name = "<agent_hostname>"

  [[inputs.snmp.field]]
    name = "cpuLoad"
    oid = ".1.3.6.1.4.1.2021.10.1.3.2"
EOF

cat > /root/monitoring_data/service/test.py << EOF
from monitor import Monitor
from utilities import Utilities

m = Monitor('10.10.10.14', None)
m.update_nodes()
#print m.nodes
print m.telegraf_config()
#print m.poll_oid('10.10.10.17', '.1.3.6.1.2.1.1.1.0')
EOF
