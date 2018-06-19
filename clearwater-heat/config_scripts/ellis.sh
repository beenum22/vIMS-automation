#!/bin/bash

# Log all output to file.
exec > >(tee -a /var/log/clearwater-heat-ellis.log) 2>&1
set -x

# Configure the APT software source.
echo 'deb __repo_url__ binary/' > /etc/apt/sources.list.d/clearwater.list
curl -L http://repo.cw-ngv.com/repo_key | apt-key add -
apt-get update

# Configure /etc/clearwater/local_config.  Add xdms_hostname here to use Homer's management
# hostname instead of signaling.  This will override shared_config.  This works around
# https://github.com/Metaswitch/ellis/issues/153.
mkdir -p /etc/clearwater
etcd_ip=__etcd_ip__
[ -n "$etcd_ip" ] || etcd_ip=__private_mgmt_ip__
cat > /etc/clearwater/local_config << EOF
local_ip=__private_mgmt_ip__
public_ip=__public_mgmt_ip__
public_hostname=ellis-__index__.__zone__
etcd_cluster=$etcd_ip
xdms_hostname=homer-0.__zone__:7888
EOF

# Now install the software.
DEBIAN_FRONTEND=noninteractive apt-get install ellis --yes --force-yes
DEBIAN_FRONTEND=noninteractive apt-get install clearwater-management --yes --force-yes

# Wait until etcd is up and running before uploading the shared_config
/usr/share/clearwater/clearwater-etcd/scripts/wait_for_etcd

# Configure and upload /etc/clearwater/shared_config.
/usr/share/clearwater/clearwater-config-manager/scripts/cw-config download shared_config --autoconfirm --dir /tmp
cat > /tmp/shared_config << EOF
# Deployment definitions
home_domain=__zone__
sprout_hostname=sprout.__zone__
hs_hostname=hs.__zone__:8888
hs_provisioning_hostname=hs-prov.__zone__:8889
ralf_hostname=ralf.__zone__:10888
xdms_hostname=homer.__zone__:7888
sprout_impi_store=vellum.__zone__
sprout_registration_store=vellum.__zone__
homestead_impu_store=vellum.__zone__
cassandra_hostname=vellum.__zone__
chronos_hostname=vellum.__zone__
ralf_session_store=vellum.__zone__

upstream_port=0

# Email server configuration
smtp_smarthost=localhost
smtp_username=username
smtp_password=password
email_recovery_sender=clearwater@example.org

# Keys
signup_key=secret
turn_workaround=secret
ellis_api_key=secret
ellis_cookie_key=secret
EOF
/usr/share/clearwater/clearwater-config-manager/scripts/cw-config upload shared_config --autoconfirm --dir /tmp

# Allocate a pool of numbers to assign to users.  Before we do this,
# restart clearwater-infrastructure to make sure that
# local_settings.py runs to pick up the configuration changes.
service clearwater-infrastructure restart
service ellis stop
/usr/share/clearwater/ellis/env/bin/python /usr/share/clearwater/ellis/src/metaswitch/ellis/tools/create_numbers.py --start __dn_range_start__ --count __dn_range_length__ --realm __zone__

# Function to give DNS record type and IP address for specified IP address
ip2rr() {
  if echo $1 | grep -q -e '[^0-9.]' ; then
    echo AAAA $1
  else
    echo A $1
  fi
}

# Update DNS
retries=0
while ! { nsupdate -y "__zone__:__dnssec_key__" -v << EOF
server __dns_mgmt_ip_1__
update add ellis-__index__.__zone__. 30 $(ip2rr __public_mgmt_ip__)
update add ellis.__zone__. 30 $(ip2rr __public_mgmt_ip__)
send
EOF
} && [ $retries -lt 10 ]
do
  retries=$((retries + 1))
  echo 'nsupdate failed - retrying (retry '$retries')...'
  sleep 5
done

# Update DNS-HA
retries=0
while ! { nsupdate -y "__zone__:__dnssec_key__" -v << EOF
server __dns_mgmt_ip_2__
update add ellis-__index__.__zone__. 30 $(ip2rr __public_mgmt_ip__)
update add ellis.__zone__. 30 $(ip2rr __public_mgmt_ip__)
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
echo 'nameserver __dns_vip_mgmt__' | cat - /etc/resolv.conf > temp && mv temp /etc/resolv.conf
echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq
service dnsmasq force-reload