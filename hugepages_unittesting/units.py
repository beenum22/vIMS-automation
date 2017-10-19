import string

def logfile_name(name):
    allowed_logfile_name = set(string.ascii_lowercase +
                               string.ascii_uppercase +
                               string.digits +
                               '.' + '_' + '-' + ',' + '/')
    forbidden_logfile_name = set('.' + '_' + '-' + ',' + '/'+'`')
    status=[]
    if not (set(name) <= forbidden_logfile_name) and set(name) <= allowed_logfile_name:
        status = True
    else:
        status=False
    return status
    
def flavor_name(name):
    allowed_flavor_name = set(string.ascii_lowercase +
                               string.ascii_uppercase +
                               string.digits +
                               '.' + '_' + '-' + ',' + '/')
    forbidden_flavor_name = set('.' + '_' + '-' + ',' + '/'+'`')
    status=[]
    if not (set(name) <= forbidden_flavor_name) and set(name) <= allowed_flavor_name:
        status = True
    else:
        status=False
    return status