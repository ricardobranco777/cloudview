![Build Status](https://github.com/ricardobranco777/cloudview/actions/workflows/ci.yml/badge.svg)

# cloudview

View instance information on EC2, Azure, GCE & OpenStack.

Support for other cloud service providers may be easily added thanks to [Apache Libcloud](https://libcloud.apache.org/)

Docker image available at `ghcr.io/ricardobranco777/cloudview:latest`

## Usage

```
Usage: cloudview [OPTIONS]
Options:
    -c, --config FILE                   path to clouds.yaml
    -l, --log debug|info|warning|error|critical
                                        logging level
    -o, --output none|text|html|json    output type
    -p, --port PORT                     run a web server on port PORT
    -r, --reverse                       reverse sort
    -s, --sort name|time|state          sort type
    -S, --states error|migrating|normal|paused|pending|rebooting|reconfiguring|running|starting|stopped|stopping|suspended|terminated|unknown|updating
                                        filter by instance state
    -T, --time TIME_FORMAT              time format as used by strftime(3)
    -V, --version                       show version and exit
    -v, --verbose                       be verbose
    --insecure                          insecure mode
```

## Requirements

Docker or Podman to run the Docker image or:

- Python 3.8+ to run installed by pip
- [Apache Libcloud](https://libcloud.apache.org/)

## clouds.yaml

Edit [examples/clouds.yaml](clouds.yaml) with the relevant information and run `chmod 600 /path/to/clouds.yaml`.

NOTES:
- The key names are not arbitrary and are the names of the arguments passed to the class factory of each provider in libcloud.
- If this file is not present, **cloudview** will try to get the information from the standard `AWS_*`, `AZURE_*`, `GOOGLE_*` & `OS_` environment variables.

## To run stand-alone:

```
pip3 install --user cloudview
cloudview [OPTIONS]
```

## To run with Docker or Podman:

`docker run --rm [OPTIONS] -v /path/to/clouds.yaml:/clouds.yaml:ro ghcr.io/ricardobranco777/cloudview -c /clouds.yaml`

NOTES:
- Make sure you also mount the path to the JSON file holding the GCE credentials with the same path mentioned in `clouds.yaml`
- For private Openstack you'd also want to mount the CA's certificates and add `-e REQUESTS_CA_BUNDLE=/path/to/certs.pem`

## Run the web server with Docker Compose:

If you have a TLS key pair, put the certificates in `cert.pem`, the private key in `key.pem` and the file containing the passphrase to the private key in `key.txt`.  Then edit the [docker-compose.yml](examples/docker-compose.yml) file to mount the directory to `/etc/nginx/ssl` in the container like this: `- "/path/to/tls:/etc/nginx/ssl:ro"`.  Set and export the `NGINX_HOST` environment variable with the FQDN of your host.

For HTTP Basic Authentication, create a file named `auth.htpasswd` in the same directory with the TLS key pair.

If you don't have a TLS key pair, a self-signed certificate and a random password for logging in will be generated.  You can see the latter with `docker compose logs`.  The user is `test`.

After running `docker compose build` & `docker compose up -d` you can browse to [https://localhost:8443](https://localhost:8443)

## Debugging

- For debugging you can set the `LIBCLOUD_DEBUG` environment variable to a path like `/dev/stderr`

## Additional information

- [EC2](https://libcloud.readthedocs.io/en/stable/compute/drivers/ec2.html)
- [Azure](https://libcloud.readthedocs.io/en/stable/compute/drivers/azure_arm.html)
- [GCE](https://libcloud.readthedocs.io/en/stable/compute/drivers/gce.html)
- [Openstack](https://libcloud.readthedocs.io/en/stable/compute/drivers/openstack.html)

## Similar projects

  - [public cloud watch](https://github.com/SUSE/pcw/)
