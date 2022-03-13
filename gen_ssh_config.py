#!/usr/bin/env python3
"""
# gen_ssh_config

## What is it?
SSH config generator.
The script creates a ssh config based on data from netbox.

## Requirements
pip3 install -r requirements.txt

## How-to
1. Rename `settings.yaml.example` to `settings.yaml` and fill it with your data.
    * Come up with a tag, for example: **gen_ssh_config**. Add it to `settings.yaml`.
    * The most important step, add a tag to devices and virtual machines in netbox to create SSH config for them.
3. SSH supports Include option.
    * Add option `Include config.d/*` to main SSH config `~/.ssh/config`.
    * And create that dir: `mkdir ~/.ssh/config/config.d`
4. Add script to cron and run it every day:
    ```
    $ crontab -e
    30 08 * * * /usr/bin/python3.9 /home/user/git/gen_ssh_config.py -u admin -p /home/user/.ssh/config.d/netbox >/dev/null 2>&
    ```

## Examples
```
$ ./gen_ssh_config.py --help
usage: gen_ssh_config.py [-h] -u USERNAME -p PATH

SSH config generator.

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        set your username
  -p PATH, --path PATH  path to ssh config file
```

```
$ ./gen_ssh_config.py -u admin -p /home/user/.ssh/config.d/netbox
2022-03-13 18:42:11,438 | PID: 558804 | INFO~: Query for devices is valid
2022-03-13 18:42:11,815 | PID: 558804 | INFO~: Query for virtual-machines is valid
2022-03-13 18:42:11,815 | PID: 558804 | INFO~: Collecting devices from netbox
2022-03-13 18:42:11,863 | PID: 558804 | WARNING~: [x] has no IP-address. Pass
2022-03-13 18:42:11,867 | PID: 558804 | WARNING~: [x] has no IP-address. Pass
2022-03-13 18:42:11,869 | PID: 558804 | WARNING~: [x] has no IP-address. Pass
2022-03-13 18:42:11,870 | PID: 558804 | WARNING~: [x] has no IP-address. Pass
2022-03-13 18:42:11,880 | PID: 558804 | INFO~: Collecting virtual_machines from netbox
2022-03-13 18:42:11,885 | PID: 558804 | WARNING~: [x] has no IP-address. Pass
2022-03-13 18:42:11,886 | PID: 558804 | WARNING~: [x] has no IP-address. Pass
2022-03-13 18:42:11,886 | PID: 558804 | WARNING~: [x] has no IP-address. Pass
2022-03-13 18:42:11,886 | PID: 558804 | WARNING~: [x] has no IP-address. Pass
2022-03-13 18:42:11,891 | PID: 558804 | WARNING~: [x] has no IP-address. Pass
2022-03-13 18:42:11,892 | PID: 558804 | INFO~: Collected from netbox - [192] devices and virtual machines
2022-03-13 18:42:12,776 | PID: 558804 | INFO~: Query for services is valid
2022-03-13 18:42:12,832 | PID: 558804 | INFO~: Collecting services from netbox for devices
2022-03-13 18:42:12,834 | PID: 558804 | INFO~: Services are collected
2022-03-13 18:42:12,834 | PID: 558804 | INFO~: SSH config successfully created
```

```
$ head -n 12 /home/user/.ssh/config.d/netbox
# This file is managed by script:gen_ssh_config.py. Do not edit.

host x1
    hostname 10.226.251.17
    user user
    port 22

host x2
    hostname 10.226.251.18
    user user
    port 22

```
"""

import argparse
import logging
import os
import sys

try:
    import pynetbox
    import yaml
except ModuleNotFoundError:
    print("ERROR: requirements not installed.\n"
        "Install it with:\n\n"
        "pip3 install -r requirements.txt\n"
        )
    sys.exit()

CONFIG_TEMPLATE = """
host {host}
    hostname {hostname}
    user {user}
    port {port}
"""


def get_hosts(netbox_api, tag, status_list):
    """
    The function will query the netbox API for all devices and virtual machines with the tag "tag" and
    status "status_list"
    
    Args:
      netbox_api: The NetBox API object that we created earlier.
      tag: The tag that you want to filter by.
      status_list: A list of statuses that you want to filter on.
    
    Returns:
      A list of dictionaries. Each dictionary contains the name and IP-address of a host.
    """
    host_list = []
    response_dict = {}

    try:
        response = netbox_api.dcim.devices.filter(tag=tag, status=status_list)
        if response:
            logging.info("Query for devices is valid")
            response_dict["devices"] = response

        response = netbox_api.virtualization.virtual_machines.filter(tag=tag, status=status_list)
        if response:
            logging.info("Query for virtual-machines is valid")
            response_dict["virtual_machines"] = response

    except Exception as error:
        logging.error(f"Query is not valid. Reason: ({error})")
        return False, []

    for response in response_dict:
        logging.info(f"Collecting {response} from netbox")
        for host in response_dict[response]:
            if not host.primary_ip:
                logging.warning(f"Host [{host.name}] has no IP-address. Pass")
                continue
            if not host.status.value in status_list:
                logging.warning(f"Host [{host.name}] doesn't have the desired status. Pass")
                continue

            host_list.append(
                {
                    "name": host.name.split('.')[0],
                    "ip": host.primary_ip.address.split("/")[0]
                }
            )
    logging.info(f"Collected from netbox - [{str(len(host_list))}] devices and virtual machines")
    return True, host_list


def get_services(netbox_api, host_list):
    """
    Get all services from netbox and find ssh service for each host
    
    Args:
      netbox_api: The NetBox API object that we created earlier.
      host_list: A list of dictionaries, where each dictionary contains the information for a single
    host.
    
    Returns:
      A list of dictionaries. Each dictionary is a host.
    """
    service_list = []

    try:
        response = netbox_api.ipam.services.all()
        if response:
            logging.info("Query for services is valid")

    except Exception as error:
        logging.error(f"Query is not valid. Reason: ({error})")
        return False, []

    for service in response:
        if service["name"] == "ssh" or service["name"] == "sshd":
            service_list.append(dict(service))

    logging.info("Collecting services from netbox for devices")
    for host in host_list:
        for service in service_list:
            if service["device"]:
                if host["name"] == service["device"]["name"]:
                    host["ssh_port"] = service["ports"][0]
                    break
            if service["virtual_machine"]:
                if host["name"] == service["virtual_machine"]["name"]:
                    host["ssh_port"] = service["ports"][0]
                    break
            # If service not found, use default port
            host["ssh_port"] = "22"

    logging.info("Services are collected")
    return True, host_list


def validate_path(path):
    """
    Validate the path of the config file
    
    Args:
      path: The path to the file that you want to write to.
    
    Returns:
      String: absolute path to the config file.
    """
    try:
        # Absolute path exist?
        if os.path.exists(path):
            return path
        else:
            # Check if directory of the file exist
            if os.path.dirname(path):
                return path

    except Exception:
        raise ("Path is not valid")


def create_ssh_config(host_list, path, username):
    """
    Create a file with a SSH config format
    
    Args:
      host_list: The list of hosts to create the config for.
      path: The path to the SSH config file.
      username: The username to use when logging into the device.
    """
    with open(path, "w") as file:
        file.write("# This file is managed by script:gen_ssh_config.py. Do not edit.\n")
        for host in host_list:
            file.write(CONFIG_TEMPLATE.format(
                       host=host["name"],
                       hostname=host["ip"],
                       user=username,
                       port=host["ssh_port"],
                       )
            )
    logging.info("SSH config successfully created")


def main():
    # Argument parser
    parser = argparse.ArgumentParser(
        description="SSH config generator."
    )
    parser.add_argument(
        "-u",
        "--username",
        required=True,
        help="set your username",
    )
    parser.add_argument(
        "-p",
        "--path",
        type=validate_path,
        required=True,
        help="path to ssh config file",
    )
    args = parser.parse_args()

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | PID: %(process)d | %(levelname)s~: %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    # Load settings
    path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(path, 'settings.yaml')) as file:
        settings = yaml.safe_load(file) 

    # Connect to netbox
    netbox_api = pynetbox.api(
        settings["url"],
        token=settings["token"]
    )
    # Get name and IP of devices
    status, host_list = get_hosts(netbox_api, settings["tag"], settings["statuses"])
    if not status:
        return None

    # Get ssh port number
    status, host_list = get_services(netbox_api, host_list)
    if not status:
        return None

    status = create_ssh_config(host_list, args.path, args.username)
    if not status:
        return None


if __name__ == "__main__":
    main()
