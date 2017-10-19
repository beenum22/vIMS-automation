import logging as Logger
from novaclient import client as nvclient
from hpsrc.GlobVar import GlobVar

nfv_logger = Logger.getLogger('dell_nfv_logger')

class FlavorControl:

    
    def __init__(self, glob):
        self.glob = glob
    
    
    def apply_config(self, arguments):
        nova = nvclient.Client(
            2,
            self.glob.OverCloud_USERNAME,
            self.glob.OverCloud_PASSWORD,
            self.glob.OverCloud_PROJECT_ID,
            self.glob.OverCloud_AUTH_URL)

        if arguments.getAction() == 'set':
            
            
            flavor = \
                self.create_flavor(nova, arguments.getFlavorName())
            self.set_flavor_metadata(flavor,
                                              arguments.getFlavorMetadata())

    def create_flavor(self, nova, flavor_name):
        #global revert_counter, flavor_delete
        flavor_list = nova.flavors.list()
        for flavor in flavor_list:
            if flavor.name == flavor_name:
                nfv_logger.info("Flavor %s already exists,"
                                " skipping flavor creation.", flavor_name)
                #flavor_delete = False
                self.glob.flavor_delete = False
                return flavor

        nfv_logger.info("Creating new flavor.")
        new_flavor = nova.flavors.create(flavor_name, 4096, 4, 40)
        #revert_counter += 1
        self.glob.revert_counter += 1
        nfv_logger.info("Flavor " + new_flavor.name + " created and added to "
                        "OpenStack.")

        return new_flavor

    def remove_flavor(self, nova, flavor_name):
        flavor_list = nova.flavors.list()
        flavor_exist = False
        default_flavor_list = ['m1.tiny', 'm1.small', 'm1.medium', 'm1.large',
                               'm1.xlarge']
        if flavor_name in default_flavor_list:
            nfv_logger.info("Flavor will not be removed since '" +
                            flavor_name +
                            "' is one of the default OpenStack "
                            "flavors. Exiting...")
            print "Script execution NOT successful." \
                  " Please check logs for details."
            return False
        else:
            for flavor in flavor_list:
                if flavor.name == flavor_name:
                    keys = flavor.get_keys()
                    flavor_exist = True
                    nova.flavors.delete(flavor)
                    nfv_logger.info("Flavor '" + flavor_name + "' deleted.")
                    return True
            if not flavor_exist:
                nfv_logger.info("Flavor does not exists. Exiting...")
                print ("Script execution failed. "
                       "Please check logs for details.")
                return False
                

    def set_flavor_metadata(self, flavor, flavor_metadata):
        
        if 'hw:mem_page_size' in flavor.get_keys():
            if flavor_metadata['hw:mem_page_size'] == flavor.get_keys()['hw:mem_page_size']: 
            #if hpgsize == #here we need improvement
                nfv_logger.info("Flavor metadata " + flavor.get_keys()[
                    'hw:mem_page_size'] +
                    " is configured already. (To change "
                    "to new value, revert changes first)")
            else: 
                flavor.set_keys(flavor_metadata)
                nfv_logger.info("Flavor metadata successfully set.")
        else:
            flavor.set_keys(flavor_metadata)
            nfv_logger.info("Flavor metadata successfully set.")

        self.glob.revert_counter = self.glob.revert_counter + 1
        self.glob.reset_metadata = True

    def remove_flavor_metadata(self, nova, flavor_name):
        flavor_list = nova.flavors.list()
        flavor_found = False
        metadata_found = False
        keys = ['hw:mem_page_size']
        for flavor in flavor_list:
            if flavor.name == flavor_name:
                flavor_found = True
                break
        if not flavor_found:
            nfv_logger.info("Flavor with flavor name' " +
                            flavor_name +
                            "' does not exists.")
            return False
        elif flavor_found:
            if 'hw:mem_page_size' in flavor.get_keys():
                metadata_found = True
                flavor.unset_keys(keys)
                nfv_logger.info("Flavor metadata unset successfully.")
            if not metadata_found:
                # nfv_logger.info("Flavor with flavor name' " +
                #                flavor_name +
                #                "' does not have the key "+keys[0] +
                #                ", skipping.")
                nfv_logger.debug("Flavor with flavor name' " +
                                 flavor_name +
                                 "' does not have the key " + keys[0] +
                                 ", skipping.")
