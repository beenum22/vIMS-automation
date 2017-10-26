import logging as Logger
import paramiko
import time
import re
import string
from hpsrc.GlobVar import GlobVar

nfv_logger = Logger.getLogger('dell_nfv_logger')


class ComputeConfig:
    '''
    Class responsible for ssh
    and application of hugepage
    config in the compute nodes
    '''
 
    
    def __init__(self, id, remote_machine, host_name, glob):
        self.id = id
        self.remote_machine = remote_machine
        self.host_name = host_name
        self.glob = glob

    def set_memory(self, memory):
        self.memory = memory
        self.list = list

    def get_memory(self):
        return self.memory

    '''Method to establish ssh connection with the compute
    node and save the connection in 'ssh_connection'
    class variable'''

    def ssh_connect(self):
        # nfv_logger.info("Establishing ssh connection with " + str(
        #    self.host_name) + " " + self.remote_machine)
        nfv_logger.debug("Establishing ssh connection with " + str(
            self.host_name) + " " + self.remote_machine)
        # initializing paramiko
        ssh_conn = paramiko.SSHClient()
        ssh_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_conn.connect(self.remote_machine, username='heat-admin')
        except BaseException:
            #nfv_logger.info("Cannot ssh into " + self.host_name)
            nfv_logger.debug("Cannot ssh into " + self.host_name)
            return False
        # save 'ssh_conn' in 'ssh_connection' class variable
        self.ssh_connection = ssh_conn
        nfv_logger.info("SSH connection successful")
        nfv_logger.debug("SSH connection successful with " +
                         str(self.host_name) + " " + self.remote_machine)
        return True

    def close_ssh_connection(self):
        self.ssh_connection.close()
    
    # NOTE: Added this temporarily from the main code. Used in both control and compute classes

    def remove_key_value_pair(self, input_string, key):
        nfv_logger.debug("Removing '%s' from the parameters" % (key))
        return re.sub(key + '=[^\s"]+', '', input_string)
    
    def apply_config(self, arguments):
        self.config_compute_params(arguments)
    

    def config_compute_params(self, arguments):
        #global revert_counter, disable_update_grub, grub_routine, Reboot_Flag
        update_grub_params = "default_hugepagesz"

        install_grub = "/usr/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg"
        if not self.validate_grub_params(update_grub_params):

            grub_cmd_line = self.get_grub_params_line()
            grub_cmd_line = grub_cmd_line.rstrip()
            grub_cmd_line = re.sub(' +', ' ', grub_cmd_line)
            grub_cmd_line = self.remove_key_value_pair(grub_cmd_line, 'default_hugepagesz')
            grub_cmd_line = self.remove_key_value_pair(grub_cmd_line, 'hugepagesz')
            grub_cmd_line = self.remove_key_value_pair(grub_cmd_line, 'hugepages')
            if not grub_cmd_line:
                nfv_logger.error("Grub CMD Line parameters not found.")
                exit(1)

            update_grub = '/usr/bin/sed ' + "'" + '/GRUB_CMDLINE_LINUX/c' \
                          + grub_cmd_line[:-1] + ' default_hugepagesz=' + \
                          str(arguments.get_hpg_size()) + \
                          'K hugepagesz=' + str(arguments.get_hpg_size()) + \
                          'K hugepages=' + str(arguments.get_hpg_num()) + '"' + "'" + \
                          ' -i /etc/default/grub'

            self.glob.disable_update_grub.append('/usr/bin/sed ' +"'" +
                                      '/GRUB_CMDLINE_LINUX/c' +
                                      grub_cmd_line + "'" +
                                      ' -i /etc/default/grub')
            ssh_stderr, ssh_stdout = self.execute_command(update_grub)
            self.glob.grub_routine = True
            self.glob.revert_counter += 1

            if ssh_stderr:
                nfv_logger.error('Command execution failed with error \"' +
                                 str(ssh_stderr) + '\" on ' + self.host_name)
                revert_changes = RevertChanges()
                revert_changes.apply_revert(arguments)
                exit()

            ssh_stderr, ssh_stdout = self.execute_command(install_grub)
            self.glob.revert_counter += 1

            if ssh_stderr:
                done = str(ssh_stderr[len(ssh_stderr) - 1].rstrip().lower())
                if done is str(done):
                    nfv_logger.info('Grub configuration file generation' +' on ' +
                                    self.host_name + ' successful ')
                    nfv_logger.debug('stderr: ' + str(ssh_stderr) +
                                    ' on ' + self.host_name)
        else:
            nfv_logger.info("'" + update_grub_params +
                            "' already exists in grub of " + self.host_name +
                            ", so skipping grub update.\n"
                            "NOTE: If you want to change the hugepage size,"
                            " please first run the 'enable_hugepages.py' "
                            "script with parameter --action=remove, "
                            "and then re-run the command with --action= set")
            print "Script execution NOT successful." \
                  " Please refer to the logs for further details."
            exit(0)

        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh_connection.exec_command(
            'sudo grep "HugePages_Total" /proc/meminfo')
        readline = ssh_stdout.readlines()
        self.glob.hugepages_on_node = int(readline[0].split()[1])
        if self.glob.hugepages_on_node == 0:
            time.sleep(10)
            nfv_logger.info("Rebooting the node for the changes"
                            " to take effect.")
            nfv_logger.debug("NO hugepages exist on " + self.host_name +
                             ". Therefore, rebooting the node for the changes"
                             " to take effect.")
            ssh_stderr_list, ssh_stdout = self.execute_command(
                "/sbin/shutdown -r now")
            self.glob.reboot_flag = True
        else:
            nfv_logger.info("Hugepages already exists on " + self.host_name +
                            ", no need to reboot. (To change this value, "
                            "revert the changes first)")
        self.close_ssh_connection()
        return update_grub, install_grub

    def execute_command(self, command):
        command = 'sudo ' + command
        nfv_logger.debug('Executing command \"' +
                         command + '\" on ' + str(self.host_name) + ' ' +
                         self.remote_machine)
        ssh_stdin, ssh_stdout, ssh_stderr = \
            self.ssh_connection.exec_command(command)
        ssh_stderr_read = ssh_stderr.readlines()
        ssh_stdout_read = ssh_stdout.readlines()
        return (ssh_stderr_read, ssh_stdout_read)
    


    def validate_grub_params(self, grub_params):
        "check if the grub parameters are already set"

        path = '/boot/grub2/grub.cfg'
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh_connection.exec_command(
            'sudo cat ' + path)

        for line in ssh_stdout.readlines():
            if grub_params in line:
                return True

        return False

    def get_grub_params_line(self):
        "Get the GRUB_CMDLINE_LINUX parameters from /etc/default/grub file"

        path = '/etc/default/grub'
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh_connection.exec_command(
            'sudo cat ' + path)

        grub_params = "GRUB_CMDLINE_LINUX"
        for line in ssh_stdout.readlines():
            if grub_params in line:
                return line

        return None