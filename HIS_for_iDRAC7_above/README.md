This program avails the user to extract the Hardware Inventory of a server using iDRAC.
The script is developed for Dell servers with iDRAC version 7 or above.
It takes a range of IP Address(s) along with the user and password, and generates a json file. 

The structure of the main function as follow:

    1. It takes a range of IP Address(s) along with the user and password (multiple IP Addresses can be provided instead/along with a range).
    2. It generates an Excel sheet of user defined IP Addresses, user and password.
    3. Using the generated Excel sheet, it SSH into the servers and runs the "racadm" command to retrieve and store the inventory in an "Idrac.ini" file in the current working directory. 
    4. Using the python "ConfigParser" library, the ini file is processed with much ease as it allows to read/search the sections to retrieve the key and values.
    5. Process each iDRAC ini file using ConfigParser to extract Memory, CPU, Hard disk and Nics using the following functions:
        - extract_mem() for extracting Memory info.
        - extract_cpu() for extracting CPUs info.
        - extract_nics() for extracting NICs info.
        - extract_hard_drives() for extracting Hard disk info.
        - All the functions take an object of ConfigParser.
    6. Store all the information into a JSON format using lists and dictionaries.
    7. The script also allows the user to generate an excel hardware inventory sheet of multiple servers.
    8. It logs the errors into a file with name "log.txt" in the current working directory.

Execution of the program:
    - To generate JSON file only:
        - python ./extract_inventory.py - i 192.168.2.1-192.168.2.5 192.168.2.193 -u root -p calvin
    - To generate JSON and Excel Sheet:
        - python ./extract_inventory.py - i 192.168.2.1-192.168.2.5 192.168.2.193 -u root -p calvin -e yes 