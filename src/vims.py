import logging
from stack import Stack
from settings import Settings
from utilities import Utilities
import json

logger = logging.getLogger(__name__)


class vIMS(Stack):

    def __init__(self, stack_name, heat_template, env_file, settings_file):
        self.stack_name = stack_name
        self.heat_template = heat_template
        self.env_file = env_file
        self.settings = Settings(settings_file)
        self.settings.parse_settings_file()
        super(vIMS, self).__init__(self.settings.auth[
            'password'], self.settings.auth['auth_url'])
        self.authenticate_clients()
        #self.flavor_name = self.settings.universal['flavor_name']
        #self.public_network = self.settings.universal['public_network']
        #self.keypair_name = self.settings.universal['keypair_name']
        #self.image_name = self.settings.universal['image_name']
        #self.mgmt_net = self.settings.universal['mgmt_net']
        #self.sig_net = self.settings.universal['sig_net']

    def setup_network(self):
        try:
            self.create_router("%s-router" % self.settings.universal[
                'mgmt_net'], ext_gw_net=self.get_net_id(self.settings.universal['public_network']))
            self.create_router("%s-router" % self.settings.universal[
                'sig_net'], ext_gw_net=self.get_net_id(self.settings.universal['public_network']))
            self.create_net(self.settings.universal['mgmt_net'])
            self.create_net(self.settings.universal['sig_net'])
            self.create_subnet(
                self.settings.mgmt_net['subnet_name'],
                self.get_net_id(self.settings.universal['mgmt_net']),
                self.settings.mgmt_net['subnet_cidr'],
                self.settings.mgmt_net['gateway'],
                self.settings.mgmt_net['ip_pool']
            )
            self.create_subnet(
                self.settings.sig_net['subnet_name'],
                self.get_net_id(self.settings.universal['sig_net']),
                self.settings.sig_net['subnet_cidr'],
                self.settings.sig_net['gateway'],
                self.settings.sig_net['ip_pool']
            )
            self.add_router_int(self.get_router_id("%s-router" % self.settings.universal[
                'mgmt_net']), subnet_id=self.get_subnet_id(self.settings.mgmt_net['subnet_name']))
            self.add_router_int(self.get_router_id("%s-router" % self.settings.universal[
                'sig_net']), subnet_id=self.get_subnet_id(self.settings.sig_net['subnet_name']))
        except Exception as err:
            logger.debug(err)
            raise

    def setup_env(self):
        try:
            self.upload_image(self.settings.universal[
                                    'image_name'], url=self.settings.universal['image_url'])
            self.create_keypair(self.settings.universal['keypair_name'])
            self.create_flavor(self.settings.universal['flavor_name'], ram=4096, vcpus=2, disk=40)
            self.check_quotas(security_groups=30)
            public_net_id = self.get_net_id(
                self.settings.universal['public_network'])
            mgmt_net_pool = Utilities.get_ip_range(self.settings.mgmt_net[
                                                   'subnet_cidr'], self.settings.mgmt_net['gateway'], self.settings.mgmt_net['ip_pool'])
            sig_net_pool = Utilities.get_ip_range(self.settings.sig_net[
                                                   'subnet_cidr'], self.settings.sig_net['gateway'], self.settings.sig_net['ip_pool'])
            if not self.settings.universal.get('dnssec_key'):
                self.settings.universal['dnssec_key'] = Utilities.get_dnssec_key()
            params = {
                "public_mgmt_net_id": public_net_id,
                "public_sig_net_id": public_net_id,
                "zone": "xflow.com",
                "flavor":  self.settings.universal['flavor_name'],
                "image":  self.settings.universal['image_name'],
                "dnssec_key": self.settings.universal['dnssec_key'],
                "key_name": self.settings.universal['keypair_name'],
                "private_mgmt_net_cidr": self.settings.mgmt_net['subnet_cidr'],
                "private_mgmt_net_gateway": self.settings.mgmt_net['gateway'],
                "private_mgmt_net_pool_start":  mgmt_net_pool[0],
                "private_mgmt_net_pool_end": mgmt_net_pool[1],
                "private_sig_net_cidr": self.settings.sig_net['subnet_cidr'],
                "private_sig_net_gateway": self.settings.sig_net['gateway'],
                "private_sig_net_pool_start": sig_net_pool[0],
                "private_sig_net_pool_end": sig_net_pool[1],
                "repo_url": self.settings.universal['repo_url'],
                "bono_cluster_size": self.settings.universal['bono_cluster_size'],
                "sprout_cluster_size": self.settings.universal['sprout_cluster_size'],
                "homer_cluster_size": self.settings.universal['homer_cluster_size'],
                "dime_cluster_size": self.settings.universal['dime_cluster_size'],
                "vellum_cluster_size": self.settings.universal['vellum_cluster_size']
            }
            self.create_stack(
                self.stack_name, self.heat_template, params=params, env_file=self.env_file)
        except Exception as err:
            raise

    def check_services(self):
        pass
