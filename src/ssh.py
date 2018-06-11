from paramiko import SSHClient, AutoAddPolicy
from paramiko import SSHException, BadHostKeyException, AuthenticationException
import socket
import logging

logger = logging.getLogger(__name__)


class SSHConnection(SSHClient):
    """Base class for SSH connection"""

    def __init__(self, host_ip, user_name, password=None, key_filename=None):
        SSHClient.__init__(self)
        #super(SshConnection, self).__init__()
        try:
            socket.inet_aton(host_ip)
        except socket.error:
            logger.error("'%s' is not a valid IP address" % host_ip)
            raise
        self.host_ip = host_ip
        self.user_name = user_name
        self.password = password
        self.key_filename = key_filename
        logging.getLogger("paramiko").setLevel(logging.ERROR)

    def open_ssh_connection(self):
        logger.debug("Establishing SSH connection with '%s' on '%s'",
                     str(self.user_name), self.host_ip)
        self.set_missing_host_key_policy(AutoAddPolicy())
        try:
            self.connect(self.host_ip, username=self.user_name,
                         password=self.password, key_filename=self.key_filename)
        except (SSHException, socket.error) as err:
            logger.error(
                "Unable to establish SSH connection with '%s'", self.host_ip)
            raise
        logger.debug("SSH connection successful with '%s' on '%s'",
                     str(self.user_name), self.host_ip)
        logger.info("Successfully connected to '%s'", self.host_ip)
        return True

    def get_connection_status(self):
        if self.get_transport().is_active():
            logger.debug("Connection is still active with '%s'", self.host_ip)
            return True
        else:
            logger.debug("Connection lost with '%s'", self.host_ip)
            return False

    def close_ssh_connection(self):
        logger.debug("SSH connection closed with '%s'", self.host_ip)
        return self.close()

    def send_file(self, source_path, dest_path):
        try:
            logger.info("Sending '%s' to remote '%s'" %
                        (source_path, dest_path))
            sftp_file = self.open_sftp()
            sftp_file.put(source_path, dest_path)
            sftp_file.close()
            return True
        except:
            logger.error("Failed to send the file: '%s'." % (source_path))
            return False

    def execute_cmd(self, cmd, sudo=False):
        if sudo:
            cmd = "sudo " + cmd
        self.get_connection_status()
        logger.debug("Executing command '%s' on '%s'", cmd, self.host_ip)
        ssh_stdin, ssh_stdout, ssh_stderr = self.exec_command(cmd)
        return ssh_stdout.readlines(), ssh_stderr.readlines()

    @classmethod
    def get_host_ssh_status(cls, host, username, password=None):
        try:
            ss = SSHConnection(host, username, password)
            ss.set_missing_host_key_policy(AutoAddPolicy())
            ss.connect(host, username=username, password=password)
            logger.debug("SSH connection possible with '%s'", host)
            ss.close()
            return True
        except (BadHostKeyException, AuthenticationException,
            SSHException, socket.error) as err:
            logger.debug("Unable to establish SSH connection with '%s'", host)
            return False
