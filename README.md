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
