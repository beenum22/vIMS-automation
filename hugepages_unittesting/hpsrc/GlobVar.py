class GlobVar(object):

    revert_counter = 0
    flavor_delete = True
    grub_routine = False
    reset_metadata = False
    disable_update_grub = []
    hugepages_on_node = 0
    OverCloud_USERNAME = OverCloud_PASSWORD = OverCloud_PROJECT_ID = OverCloud_AUTH_URL = ''
    UnderCloud_USERNAME = UnderCloud_PASSWORD = UnderCloud_PROJECT_ID = UnderCloud_AUTH_URL = ''
    Reboot_Flag = False
    SSH_RETRIES = 10
    DEFAULT_2MB = 25600
    DEFAULT_1GB = 50
    Max2MB = Min2MB = Max1GB = Min1GB = default2MB = default1GB = 0
    nodes = {'compute': {}, 'control': {}}