import logging
import time
from keystoneauth1 import identity
from keystoneauth1 import session
from keystoneauth1 import loading
from keystoneauth1.exceptions import *
from neutronclient.v2_0 import client as ntclient
from novaclient import client as nvclient
from novaclient.exceptions import *
from glanceclient import Client as gclient
from openstack import connection
from openstack.exceptions import HttpException, ResourceNotFound, SDKException
from utilities import Utilities
from heatclient.common import template_utils
from keystoneauth1.identity import v2
from heatclient import client as hclient
#from keystoneclient.v3 import Client as kclient

logger = logging.getLogger(__name__)


class Stack(object):

    def __init__(self,
                password,
                auth_url,
                username='admin',
                project_name='admin',
                project_id=None,
                project_domain_name='Default',
                user_domain_name='Default',
                compute_api = '2.1',
                heat_api = '1',
                glance_api = '2'
                ):
        self.username = username
        self.password = password
        self.auth_url = auth_url
        self.project_name = project_name
        self.project_id = project_id
        self.user_domain_name = user_domain_name
        self.project_domain_name = project_domain_name
        self.compute_api = compute_api
        self.heat_api = heat_api
        self.glance_api = glance_api
        self.authenticate_clients()

    def authenticate_clients(self):
        try:
            self._get_auth_sess()
            self.nova = self._get_novaclient(self.sess)
            self.neutron = self._get_neutronclient(self.sess)
            self.glance = self._get_glanceclient(self.sess)
            self.heat = self._get_heatclient(
                self.auth_url, self.sess, self.auth, 'orchestration')
            self.openstack = self._get_openstacksdk_client()
            self.openstack.authorize()
        except HttpException as err:
            logger.debug(err)
            raise Exception("OpenStack Authorization failed. Verify credentials.")
        except Exception as err:
            raise

    def exception_handling(func):
        def auth_exceptions(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except ConnectFailure as err:
                logger.debug(err)
                raise Exception(
                    "Failed to establish connection with auth_url: '%s'" % (
                        self.auth_url
                        ))
            except http.Unauthorized as err:
                logger.debug(err)
                raise Exception("OpenStack Authorization failed. Verify the " \
                            "credentials.")
            except ResourceNotFound:
                raise
            except NotFound:
                raise
            except:
                raise
        #decorated._original = func
        return auth_exceptions

    def _get_auth_sess(self):
        self.auth = identity.Password(auth_url=self.auth_url,
                                      username=self.username,
                                      password=self.password,
                                      project_name=self.project_name,
                                      user_domain_name=self.user_domain_name,
                                      project_domain_name=self.project_domain_name)
        self.sess = self._get_session(self.auth)
        return self.auth, self.sess

    def _get_session(self, auth):
        return session.Session(auth=auth)

    def _get_openstacksdk_client(self):
        conn = connection.Connection(auth_url=self.auth_url,
                                     project_name=self.project_name,
                                     username=self.username,
                                     password=self.password,
                                     user_domain_name=self.user_domain_name,
                                     project_domain_name=self.project_domain_name)
        return conn

    def _get_heatclient(self, auth_url, sess, auth, service_type, version='1'):
        return hclient.Client(version,
                              auth_url=auth_url,
                              session=sess,
                              auth=auth,
                              service_type=service_type)

    def _get_novaclient(self):
        try:
            if not self.sess:
                self._get_auth_sess()
            return nvclient.Client(self.compute_api, session=self.sess,)
        except UnsupportedVersion as err:
            logger.debug(err)
            raise UnsupportedVersion(
                "Invalid Nova client version '%s'" % self.compute_api)
        except Exception as err:
            logger.debug(err)
            raise Exception("Nova client authentication failed")

    def _get_neutronclient(self, sess):
        return ntclient.Client(session=sess)

    def _get_glanceclient(self, sess, version='2'):
        return gclient(version, session=sess)

    @exception_handling
    def _get_network(self, name):
        #try:
        if not self.neutron:
            auth, sess = self._get_auth_sess()
            self.neutron = self._get_neutronclient(sess)
        networks = self.neutron.list_networks(name=name)
        return networks

    @exception_handling
    def _get_subnet(self, name):
        if not self.neutron:
            auth, sess = self._get_auth_sess()
            self.neutron = self._get_neutronclient(sess)
        return self.neutron.list_subnets(name=name)

    @exception_handling
    def _get_router(self, name):
        if not self.neutron:
            auth, sess = self._get_auth_sess()
            self.neutron = self._get_neutronclient(sess)
        return self.neutron.list_routers(name=name)

    def get_net_id(self, name):
        """Generic function to get any network id"""
        net = self._get_network(name)
        if net['networks']:
            return net['networks'][0]['id']
        return None

    def get_subnet_id(self, name):
        """Generic function to get any network id"""
        subnet = self._get_subnet(name)
        if subnet['subnets']:
            return subnet['subnets'][0]['id']
        return None

    def get_router_id(self, name):
        """Generic function to get any network id"""
        router = self._get_router(name)
        if router['routers']:
            return router['routers'][0]['id']
        return None

    def create_net(self, name):
        net_params = {'name': name, 'admin_state_up': True}
        if not self._get_network(name)['networks']:
            logger.debug("Creating '%s' network", name)
            self.neutron.create_network({'network': net_params})
            logger.info("Network '%s' succesfully created", name)
            return True
        else:
            logger.debug("Network '%s' already exists", name)
            return False

    def create_subnet(self,
                    name,
                    net_id,
                    cidr,
                    gw,
                    pool_size=-1,
                    dns_list=['8.8.8.8']):
        try:
            subnet_body = {'name': name,
                        'network_id': net_id,
                        'ip_version': 4,
                        'enable_dhcp': True,
                        'dns_nameservers': dns_list,
                        'allocation_pools': [{'start': None, 'end': None}],
                        'gateway_ip': gw,
                        'cidr': cidr}
            subnet_body['allocation_pools'][0]['start'], \
                subnet_body['allocation_pools'][0]['end'] = \
                Utilities.get_ip_range(cidr, gw, pool_size)
            if not self._get_subnet(name)['subnets']:
                logger.debug("Creating '%s' subnet", name)
                subnet = self.neutron.create_subnet({'subnet': subnet_body})
                logger.info("Subnet '%s' succesfully created", name)
                return subnet['subnet']['id']
            else:
                logger.debug("Subnet '%s' already exists", name)
                return None
        except:
            raise

    def create_router(self, name, ext_gw_net=None):
        router = {'admin_state_up': True, 'name': name}
        if ext_gw_net:
            router['external_gateway_info'] = {'network_id': ext_gw_net}
        if not self._get_router(name)['routers']:
            logger.debug("Creating '%s' router", name)
            self.neutron.create_router({'router': router})
            logger.info("Router '%s' succesfully created", name)
            return True

    def add_router_int(self, router_id, subnet_id=None, port_id=None):
        try:
            add_int = {}
            if subnet_id:
                add_int['subnet_id'] = subnet_id
            elif port_id:
                add_int['port_id'] = port_id
            else:
                logger.error("Provide a port id or subnet id")
                return None
            logger.info("Adding interface to Router '%s'", router_id)
            return self.neutron.add_interface_router(router_id, add_int)
        except Exception as err:
            logger.debug(err)
            raise

    @exception_handling
    def create_keypair(self, keypair_name):
        """ Create Keypair file"""
        key = self.nova.keypairs.findall(name=keypair_name)
        if not key:
            logger.info("Creating Key Pair '%s'", keypair_name)
            keypair = self.nova.keypairs.create(name=keypair_name)
            path = Utilities.join_paths(
                Utilities.get_home_directory(), '.ssh', keypair_name)
            with open(path + '.pem', "w+") as f:
                f.write(keypair.private_key)
            with open(path + '.pub', "w+") as f:
                f.write(keypair.public_key)
            logger.info("Key Pair created!")
            return keypair
        return None

    def create_flavor(self, flavor_name, ram, vcpus, disk, metadata={}):
        try:
            if not self.nova.flavors.findall(name=flavor_name):
                logger.info("Creating flavor '%s'", flavor_name)
                flavor = self.nova.flavors.create(
                    flavor_name, ram=ram, vcpus=vcpus, disk=disk)
                logger.info("Flavor '%s' successfully created", flavor_name)
                flavor.set_keys(metadata)
                return flavor
            logger.info("Flavor '%s' already exists", flavor_name)
            return None
        except http.Unauthorized as err:
            logger.debug(err)
            raise Exception("OpenStack Authorization failed. Verify credentials.")
        except:
            raise

    @exception_handling
    def get_flavor(self, flavor_name):
        try:
            flavor = self.openstack.compute.find_flavor(flavor_name)
            assert flavor, "Flavor: '%s' not found"
            return self.openstack.compute.get_flavor(flavor.id)
        except AssertionError:
            raise

    def upload_image(self, image_name, url=None):
        """ Load image if not present download it."""
        try:
            logger.info("Uploading Image")
            if not self.openstack.image.find_image(image_name):
                assert url != None, "Image not found. Provide image URL"
                Utilities.get_file(url, 'images', image_name)
                path = Utilities.join_paths(
                    Utilities.get_current_directory(), 'images', image_name)
                path = Utilities.get_current_directory()
                path = path + '/images/' + image_name
                # Build the image attributes and upload the image.
                with open(path) as f:
                    image_attrs = {
                        'name': image_name,
                        'data': f,
                        'disk_format': 'qcow2',
                        'container_format': 'bare',
                        'visibility': 'public',
                    }
                    response = self.openstack.image.upload_image(**image_attrs)
                logger.info("Image uploaded")
                return True
            logger.info("Image already uploaded")
            return False
        except AssertionError as err:
            raise
        except Exception as err:
            logger.debug(err)
            raise

    def create_security_group(self, name):
        try:
            if not self.openstack.network.find_security_group(name):
                logger.info("Creating security group '%s'", name)
                self.openstack.network.create_security_group(name=name)
                logger.info("Security group successfully created '%s'", name)
                return True
            logger.info("Security group '%s' already exists", name)
            return False
        except SDKException as err:
            logger.debug(err)
            raise Exception("Failed to establish connection with auth_url: %s" \
                            % self.auth_url)
        except HttpException as err:
            logger.debug(err)
            raise Exception("OpenStack Authorization failed. Verify credentials.")
        except:
            raise

    def add_security_rule(self, sec_group, rule):
        try:
            sec_id = self.openstack.network.find_security_group(sec_group).id
            logger.info("Adding security rule '%s'" % rule)
            self.openstack.network.create_security_group_rule(
                security_group_id=sec_id,
                direction=rule['dir'],
                remote_ip_prefix=rule['cidr'],
                protocol=rule['proto'],
                port_max=rule['port_max'],
                port_min=rule['port_min'],
                ethertype=rule['type']
            )
            return True
        except SDKException as err:
            logger.debug(err)
            raise Exception("Failed to establish connection with auth_url: %s" \
                            % self.auth_url)
        except HttpException as err:
            logger.debug(err)
            raise Exception("OpenStack Authorization failed. Verify credentials.")
        except:
            raise

    def allow_ping(self, sec_group):
        try:
            logger.info("Allowing Ping in '%s' security group", sec_group)
            sec_id = self.openstack.network.find_security_group(sec_group).id
            return self.openstack.network.security_group_allow_ping(sec_id)
        except SDKException as err:
            logger.debug(err)
            raise Exception("Failed to establish connection with auth_url: %s" \
                            % self.auth_url)
        except HttpException as err:
            logger.debug(err)
            raise Exception("OpenStack Authorization failed. Verify credentials.")
        except:
            raise

    def open_port(self, sec_group, port, proto):
        try:
            logger.info("Opening port '%s' in '%s' security group",
                        port, sec_group)
            sec_id = self.openstack.network.find_security_group(sec_group).id
            return self.openstack.network.security_group_open_port(sec_id, port, proto)
        except SDKException as err:
            logger.debug(err)
            raise Exception("Failed to establish connection with auth_url: %s" \
                            % self.auth_url)
        except HttpException as err:
            logger.debug(err)
            raise Exception(
                "OpenStack Authorization failed. Verify credentials.")
        except:
            logger.debug(err)
            raise

    def create_server(
                    self,
                    name,
                    keypair,
                    flavor,
                    image,
                    nets,
                    sec_groups,
                    a_zone=None
                    ):
        try:
            logger.info("Creating Server '%s'", name)
            image = self.openstack.compute.find_image(image)
            flavor = self.openstack.compute.find_flavor(flavor)
            keypair = self.openstack.compute.find_keypair(keypair)
            networks = []
            for n in nets:
                net = self.openstack.network.find_network(n)
                networks.append({'uuid': net.id})
            security_groups = []
            for s in sec_groups:
                sec = self.openstack.network.find_security_group(s)
                security_groups.append({'name': sec.name})
            server = self.openstack.compute.create_server(
                                                    name=name,
                                                    image_id=image.id,
                                                    flavor_id=flavor.id,
                                                    key_name=keypair.name,
                                                    networks=networks,
                                                    security_groups=security_groups
                                                    )
            logger.info("Waiting for server '%s' to get active", name)
            server = self.openstack.compute.wait_for_server(server)
            logger.info("Server '%s' successfully created", name)
            return True
        except Exception as err:
            logger.debug(err)
            raise

    def find_heat_enpoint(self, service_name):
        try:
            service_id = self.openstack.identity.find_service(service_name).id
            self.project_id = self.openstack.identity.find_project(
                self.project_name).id
            for ep in self.openstack.identity.endpoints():
                if ep.service_id == service_id:
                    return ep.url.split('%')[0] + self.project_id
        except Exception as err:
            logger.debug(err)
            raise

    def get_heat_temp_files(self, template, env_file=None):
        try:
            env = None
            files = None
            temp = None
            files, temp = template_utils.process_template_path(template)
            if env_file:
                files, env = template_utils.process_environment_and_files(
                    env_file, template)
            return files, temp, env
        except Exception as err:
            logger.debug(err)
            raise

    def create_stack(self, name, template, params=None, env_file=None):
        try:
            logger.info("Creating stack '%s'", name)
            files, template, env = self.get_heat_temp_files(
                template, env_file=env_file)
            # with open(template) as t:
            if params:
                self.heat.stacks.create(stack_name=name,
                                        template=template,
                                        files=files,
                                        parameters=params,
                                        environment=env)
            else:
                self.heat.stacks.create(stack_name=name,
                                        template=template,
                                        files=files,
                                        environment_files=env)

            # Verification of stack creation
            stack_detail = self.heat.stacks.get(name)
            while (stack_detail.stack_status != "CREATE_COMPLETE"):
                time.sleep(20)
                if (stack_detail.stack_status == "CREATE_IN_PROGRESS"):
                    logger.info("Stack creation in progress....")
                elif stack_detail.stack_status == "CREATE_FAILED":
                    logger.info("Stack creation failed....")
                    raise Exception("Failed to create '%s' stack" % name)
                stack_detail = self.heat.stacks.get(name)
            logger.info("Stack creation successful")

        except Exception as err:
            # logger.debug(err)
            raise

    # TODO: DEPRECATED, remove
    def check_quotas(self, cores=50, floating_ips=30, security_groups=30, port=100):
        try:
            # check flavor vcpus
            # Update Quota
            self.project_id = self.openstack.identity.find_project(
                self.project_name).id
            logger.info("Updating OpenStack quota for '%s' project",
                        self.project_name)
            quota_nova = self.nova.quotas.update(self.project_id, cores=cores)
            quota_neutron = self.neutron.update_quota(
                self.project_id, {'quota': {
                                'security_group': security_groups, 
                                'port': port, 
                                'floatingip': floating_ips}}
                                )
            return True
        except http.Unauthorized as err:
            logger.debug(err)
            raise Exception("OpenStack Authorization failed. Verify credentials.")
        except:
            raise

    def verify_free_quota(self, used, total, required):
        if (int(total) - int(used)) > int(required):
            return True
        else:
            return False

    def verify_quotas(self,
                        cores=50,
                        memory=19456,
                        floating_ips=30,
                        security_groups=30,
                        instances=19,
                        port=100):
        try:
            if not self.project_id:
                self.project_id = self.openstack.identity.find_project(self.project_name).id
            nova_limits = self.nova.limits.get().absolute
            limits = dict(map(lambda x: (x.name, x.value), list(nova_limits)))
            if not self.verify_free_quota(limits['totalCoresUsed'], limits['maxTotalCores'], cores):
                self.nova.quotas.update(self.project_id, cores=cores)
            if not self.verify_free_quota(limits['totalRAMUsed'], limits['maxTotalRAMSize'], memory):
                self.nova.quotas.update(self.project_id, ram=memory)
            if not self.verify_free_quota(limits['totalFloatingIpsUsed'], limits['maxTotalFloatingIps'], floating_ips):
                self.nova.quotas.update(self.project_id, floating_ips=floating_ips)
            if not self.verify_free_quota(limits['totalSecurityGroupsUsed'], limits['maxSecurityGroups'], security_groups):
                self.nova.quotas.update(self.project_id, security_groups=security_groups)
            if not self.verify_free_quota(limits['totalInstancesUsed'], limits['maxTotalInstances'], security_groups):
                self.nova.quotas.update(self.project_id, instances=instances)
        except AssertionError:
            raise

    @exception_handling
    def _hypervisors(self):
        return self.nova.hypervisors.list()

    @exception_handling
    def _get_host(self, hostname):
        try:
            hyp = self.nova.hypervisors.find(hypervisor_hostname=hostname)
            return hyp
        except NotFound as err:
            logger.error(err)
            raise Exception("Host '%s' not found" % hostname)

    def _get_hypervisor_resources(self, hostname):
        resources = {'total': {}, 'used': {}}
        hypervisor = self._get_host(hostname)
        resources['total']['vcpus'] = hypervisor.vcpus
        resources['total']['memory'] = hypervisor.memory_mb
        resources['total']['storage'] = hypervisor.local_gb
        resources['used']['vcpus'] = hypervisor.vcpus_used
        resources['used']['memory'] = hypervisor.memory_mb_used
        resources['used']['storage'] = hypervisor.local_gb_used
        return resources

    def get_hypervisors(self):
        hypervisors = []
        for h in self._hypervisors():
            hypervisors.append(h.hypervisor_hostname)
        return hypervisors

    def get_total_available_resources(self):
        total_avail = {'vcpus': 0, 'memory': 0, 'storage': 0}
        hypervisors = self.get_hypervisors()
        for hyp in hypervisors:
            r = self._get_hypervisor_resources(hyp)
            total_avail['vcpus'] += r['total']['vcpus'] - r['used']['vcpus']
            total_avail['memory'] += r['total']['memory'] - r['used']['memory']
            total_avail['storage'] += r['total']['storage'] - r['used']['storage']
        return total_avail

    def _get_network_info(self, name):
        try:
            net_id = self.get_net_id(name)
            return self.openstack.network.get_network_ip_availability(net_id)
        except KeyError as err:
            logger.debug(err)
            raise Exception("Network:'%s' doesn't exist" % name)
        except ResourceNotFound as err:
            logger.debug(err)
            raise ResourceNotFound("Network ID:%s doesn't exist" % net_id)

    def total_net_ips(self, name):
        try:
            return self._get_network_info(name)['total_ips']
        except:
            raise

    def available_net_ips(self, name):
        try:
            avail_ips = self._get_network_info(name)['total_ips'] - \
                        self._get_network_info(name)['used_ips']
            return avail_ips
        except:
            raise
