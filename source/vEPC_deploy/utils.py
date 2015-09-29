def print_values(val, type):
    if type == 'ports':
        val_list = val['ports']
    if type == 'networks':
        val_list = val['networks']
    if type == 'routers':
        val_list = val['routers']
    for p in val_list:
        for k, v in p.items():
            print("%s : %s" % (k, v))
        print('\n')
 
 
def print_values_server(val, server_id, type):
    if type == 'ports':
        val_list = val['ports']
 
    if type == 'networks':
        val_list = val['networks']
    for p in val_list:
        bool = False
        for k, v in p.items():
            if k == 'device_id' and v == server_id:
                bool = True
        if bool:
            for k, v in p.items():
                print("%s : %s" % (k, v))
            print('\n')

def print_server(server):
    print("-"*35)
    print("server id: %s" % server.id)
    print("server name: %s" % server.name)
    print("server image: %s" % server.image)
    print("server flavor: %s" % server.flavor)
    print("server key name: %s" % server.key_name)
    print("user_id: %s" % server.user_id)
    print("-"*35)

def print_values_ip(ip_list):
    ip_dict_lisl = []
    for ip in ip_list:
        print("-"*35)
        print("fixed_ip : %s" % ip.fixed_ip)
        print("id : %s" % ip.id)
        print("instance_id : %s" % ip.instance_id)
        print("ip : %s" % ip.ip)
        print("pool : %s" % ip.pool)
		
