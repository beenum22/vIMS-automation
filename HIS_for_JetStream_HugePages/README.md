The project is for integrating the Hardware Inventory System with the Jetstream and HugePages deployment.

We have  modified and added the following files to incorporate the integration of HIS with JS/NFV solution. 

1. Modified:
    1. deployer.py 
    2. config.py 

2. Added:
    1. extract_inventory.py

The functionalities of the mentioned files are described bellow: 

    1. Deployer.py:
        - It calls the deploy() function
        - The deploy() function initilizes the Settings Class by passing the setting files.
            - A file with name JetStream_hw_req.ini is passed into the Settings() function (see sample_JetStream_hw_req.ini).

    2. config.py:
        - It contains the Settings class.
        - The initialization function calls the Hardware Inventory functions to check:
            - Jetstream hardware requirements
            - HugePages requirements for NFV

    3. extract_inventory.py:
        - It contains the functions for extracting Memory, CPU and hard disks etc.
        - The Settings initialzation function uses the extract_inventory functions.

JetStream_hw_req.ini:

    1. The user has to provide the JetStream.ini file (see sample_JetStream_hw_req.ini).
    2. This file contains the hardware requirements for compute and controller nodes only.
    3. It supports the following hardware parameters only:
        - idrac_model
        - cpu
        - cpu_version
        - cpu_speed
        - total_cpu
        - total_memory_size
        - total_memory_slots
        - total_drives_size
        - total_drives
        - raid_model
        - raid_cache_size
        - nic_slots
        - nics
        - drive_bus_type
    4. To add any other parameter, the user has to modify the program.

Perform the following tasks to execute the script:

    1. Replace the file "deployer.py" in "src\deploy\osp_deployer\" directory of JetStream_10 with the above mentioned file. 
    2. Replace the file "config.py" in "src\deploy\osp_deployer\settings\" directory of JetStream_10 with the above mentioned file. 
    3. Add the file "extract_inventory.py" in "src\deploy\osp_deployer\settings\" directory of JetStream_10. 
    4. Create the JetStream_hw_req.ini file as per the guidelines provided above.
    5. Execute the script as follow:
        - python ./Deployer -s <setting_file.ini> -j <sample_JetStream.ini>