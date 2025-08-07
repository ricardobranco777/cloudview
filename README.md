![Build Status](https://github.com/ricardobranco777/cloudview/actions/workflows/ci.yml/badge.svg)

[![codecov](https://codecov.io/gh/ricardobranco777/cloudview/branch/master/graph/badge.svg)](https://codecov.io/gh/ricardobranco777/cloudview)

# cloudview

View instance information on EC2, Azure, GCE & OpenStack.

Support for other cloud service providers may be easily added thanks to [Apache Libcloud](https://libcloud.apache.org/)

Docker image available at `ghcr.io/ricardobranco777/cloudview:latest`

## Usage

```
usage: cloudview.py [-h] [-c CONFIG] [-f FIELDS] [-l {none,debug,info,warning,error,critical}] [-p {ec2,gce,azure_arm,openstack}] [-r] [-s {name,state,time}]
                    [-S {error,migrating,normal,paused,pending,rebooting,reconfiguring,running,starting,stopped,stopping,suspended,terminated,unknown,updating}] [-t TIME_FORMAT] [-v]
                    [--version]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        path to clouds.yaml (default: None)
  -f FIELDS, --fields FIELDS
                        output fields (default: provider,name,size,state,time,location)
  -l {none,debug,info,warning,error,critical}, --log {none,debug,info,warning,error,critical}
                        logging level (default: error)
  -p {ec2,gce,azure_arm,openstack}, --providers {ec2,gce,azure_arm,openstack}
                        list only specified providers (default: None)
  -r, --reverse         reverse sort (default: False)
  -s {name,state,time}, --sort {name,state,time}
                        sort type (default: None)
  -S {error,migrating,normal,paused,pending,rebooting,reconfiguring,running,starting,stopped,stopping,suspended,terminated,unknown,updating}, --states {error,migrating,normal,paused,pending,rebooting,reconfiguring,running,starting,stopped,stopping,suspended,terminated,unknown,updating}
                        filter by instance state (default: None)
  -t TIME_FORMAT, --time TIME_FORMAT
                        strftime format or age|timeago (default: %a %b %d %H:%M:%S %Z %Y)
  -v, --verbose         be verbose (default: None)
  --version             show program's version number and exit

output fields for --fields: provider,name,id,size,state,time,location
```

## Requirements

Docker or Podman to run the Docker image

## clouds.yaml

Edit [examples/clouds.yaml](clouds.yaml) with the relevant information and run `chmod 600 /path/to/clouds.yaml`.

NOTES:
- The key names are not arbitrary and are the names of the arguments passed to the class factory of each provider in libcloud.
- If this file is not present, **cloudview** will try to get the information from the standard `AWS_*`, `AZURE_*`, `GOOGLE_*` & `OS_` environment variables.

## cloudview script

The [cloudview](scripts/cloudview) script scans `clouds.yaml` and environment variables to execute the proper `docker` command.

## Debugging

- For debugging you can set the `LIBCLOUD_DEBUG` environment variable to a path like `/dev/stderr`

## Additional information

- [EC2](https://libcloud.readthedocs.io/en/stable/compute/drivers/ec2.html)
- [Azure](https://libcloud.readthedocs.io/en/stable/compute/drivers/azure_arm.html)
- [GCE](https://libcloud.readthedocs.io/en/stable/compute/drivers/gce.html)
- [Openstack](https://libcloud.readthedocs.io/en/stable/compute/drivers/openstack.html)
