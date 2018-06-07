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
apt-get install -y snmp smitools git python-pip snmp-mibs-downloader
pip install docopt
git clone https://github.com/Metaswitch/clearwater-snmp-handlers.git $HOME/clearwater-mibs/clearwater-snmp-handlers && python $HOME/clearwater-mibs/clearwater-snmp-handlers/mib-generator/cw_mib_generator.py $HOME/clearwater-mibs
cp $HOME/clearwater-mibs/PROJECT-CLEARWATER-MIB /etc/snmp && cp $HOME/clearwater-mibs/PROJECT-CLEARWATER-MIB /usr/share/snmp/mibs/
echo "mibs +PROJECT-CLEARWATER-MIB" > /etc/snmp/snmp.conf
service snmpd restart

apt-get install -y influxdb grafana telegraf
service influxdb start
service influxdb start
service telegraf start
service grafana-server start

service influxdb enable
service telegraf enable
service grafana-server enable
