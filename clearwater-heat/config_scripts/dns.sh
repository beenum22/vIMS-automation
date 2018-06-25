#!/bin/bash

# Log all output to file.
exec > >(tee -a /var/log/clearwater-heat-dns.log) 2>&1
set -x

# Set up the signaling network interface
ip addr add __private_sig_ip__/$(echo __private_sig_cidr__ | cut -d / -f 2) dev eth1
ip link set dev eth1 up

# Install BIND.
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install bind9 --yes

apt install -y keepalived
cat > /etc/keepalived/keepalived.conf << EOF
vrrp_instance dns_ha_mgmt {
    state __state__
    interface eth0
    virtual_router_id 51
    __priority__
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass supersecretpassword
    }
    virtual_ipaddress {
        __vip_mgmt__
    }
}

vrrp_instance dns_ha_sig {
    state __state__
    interface eth1
    virtual_router_id 52
    priority __priority__
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass supersecretpassword
    }
    virtual_ipaddress {
        __vip_sig__
    }
}
EOF

service keepalived restart

# Update BIND configuration with the specified zone and key.
cat >> /etc/bind/named.conf.local << EOF
key __zone__. {
  algorithm "HMAC-MD5";
  secret "__dnssec_key__";
};

zone "__zone__" IN {
  type master;
  file "/var/lib/bind/db.__zone__";
  allow-update {
    key __zone__.;
  };
};
EOF

# Function to give DNS record type and IP address for specified IP address
ip2rr() {
  if echo $1 | grep -q -e '[^0-9.]' ; then
    echo AAAA $1
  else
    echo A $1
  fi
}


# Create basic zone configuration.
cat > /var/lib/bind/db.__zone__ << EOF
\$ORIGIN __zone__.
\$TTL 1h
@ IN SOA ns admin\@__zone__. ( $(date +%Y%m%d%H) 1d 2h 1w 30s )
@ NS ns
ns $(ip2rr __public_ip__)
EOF
chown root:bind /var/lib/bind/db.__zone__

# Now that BIND configuration is correct, kick it to reload.
service bind9 reload
