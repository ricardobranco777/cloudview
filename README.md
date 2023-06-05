![Build Status](https://github.com/ricardobranco777/cloudview/actions/workflows/ci.yml/badge.svg)

# cloudview
View instance information on all supported cloud providers: Amazon Web Services, Azure, Google Compute Platform & OpenStack.

Docker image available at `ghcr.io/ricardobranco777/cloudview:latest`

## Usage

```
Usage: cloudview [OPTIONS]
Options:
    -h, --help                          show this help message and exit
    -l, --log debug|info|warning|error|critical
    -o, --output text|html|json|JSON    output type
    -p, --port PORT                     run a web server on port PORT
    -r, --reverse                       reverse sort
    -s, --sort name|time|status         sort type
    -S, --status stopped|running|all    filter by instance status
    -T, --time TIME_FORMAT              time format as used by strftime(3)
    -v, --verbose                       be verbose
    -V, --version                       show version and exit
    --insecure                          do not validate TLS certificates
Filter options:
    --filter-aws NAME VALUE             may be specified multiple times
    --filter-azure FILTER               Filter for Azure
    --filter-gcp FILTER                 Filter for GCP
    --filter-openstack NAME VALUE       may be specified multiple times
```

**NOTES**:
  - Use `--output JSON` to dump _all_ available information received from each provider.

This script is best run with Docker to have all dependencies in just one package, but it may be run stand-alone on systems with Python 3.7+

## Environment variables

    - `AWS_ACCESS_KEY_ID`
    - `AWS_DEFAULT_REGION`
    - `AWS_SECRET_ACCESS_KEY`
    - `AZURE_TENANT_ID`
    - `AZURE_SUBSCRIPTION_ID`
    - `AZURE_CLIENT_SECRET`
    - `AZURE_CLIENT_ID`
    - `GOOGLE_APPLICATION_CREDENTIALS`
    - `OS_USERNAME`
    - `OS_PASSWORD`
    - `OS_PROJECT_ID`
    - `OS_AUTH_URL`
    - `OS_USER_DOMAIN_NAME`
    - `OS_CACERT`

**NOTES**:
  - The `AWS_*` environment variables are optional.  If not set, the AWS SDK will grab the information from `~/.aws/credentials` and `~/.aws/config`.
  - The `GOOGLE_APPLICATION_CREDENTIALS` environment variable must contain the path to the JSON file downloaded from the GCP web console after creating a personal key for the service account of your project.
  - The `AZURE_*` environment variables are mandatory if you want Azure output.  For `AZURE_TENANT_ID` & `AZURE_SUBSCRIPTION_ID` check the output of `az account show --query "{subscriptionId:id, tenantId:tenantId}"`.  For the client id and secret, an Azure AD Service Principal is required and can be created, with the proper permissions, with this command: `az ad sp create-for-rbac --name MY-AD-SP --role=Contributor --scopes=/subscriptions/<SUBSCRIPTION ID>`.  These variables are the same as the `ARM_*` variables used by the Terraform Azure provider.  More information in the [official Microsoft documentation](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/terraform-install-configure)
  - The `OS_*` variables are optional.  You may set them by sourcing the OpenStack RC v2.0 or v3 scripts that you may download from the web UI at [https://OPENSTACK_SERVER/project/access_and_security/api_access/openrc/](https://OPENSTACK_SERVER/project/access_and_security/api_access/openrc/).  Alternatively, you may use the `clouds.yaml` file described at the [OpenstackSDK documentation](https://docs.openstack.org/openstacksdk/latest/user/guides/connect_from_config.html)

## To run stand-alone:

```
pip3 install --user cloudview
```

## To run with Docker (or Podman):

If you want to use Podman instead of Docker:
```
alias docker=podman
```

Build image with:
```
docker build -t cloud --pull .
```

Export the variables listed in the [.dockerenv](.dockerenv) file and run with:

```
docker run --rm -v "$GOOGLE_APPLICATION_CREDENTIALS:$GOOGLE_APPLICATION_CREDENTIALS:ro" -v "$OS_CACERT:$OS_CACERT:ro" -v ~/.config/openstack:/etc/openstack:ro --env-file .dockerenv cloudview --status all
```

NOTES:
  - To use `podman` in rootless mode, make sure to add your user to the /etc/subuid & /etc/subgid files as described in the [manual page](https://github.com/containers/libpod/blob/master/docs/podman.1.md#rootless-mode)

## Run the web server with [Docker Compose](https://docs.docker.com/compose/install/):

If you have a TLS key pair, rename the certificate to `cert.pem`, the private key to `key.pem` and the file containing the passphrase to the private key to `key.txt`.  Then edit the [docker-compose.yml](docker-compose.yml) file to mount them to `/etc/nginx/ssl` in read-only mode like this: `- "/path/to/tls:/etc/nginx/ssl:ro"`.  Set and export the `NGINX_HOST` environment variable with the DNS of your host.

If you don't have a TLS key pair, a self-signed certificate will be generated.  Be aware of the typical problems with time resolution related to TLS certificates.

For HTTP Basic Authentication, create a file named `auth.htpasswd` in the same directory with the TLS certs.  Use the `htpasswd` utility for this.  This file is generated if a self-signed certificate is generated too.  In this case you must look up the generated password with `docker-compose logs`.  The user is `test`.

This command creates 2 read-only containers for security, one with the Python app and another using Nginx as reverse-proxy:

```
docker-compose up -d
```

Now browse to [https://localhost:8443](https://localhost:8443)

To stop the web server:
```
docker-compose down
```

To rebuild the images:
```
docker-compose build --pull
```

### Filter options (AWS)

Usage: `--filter-aws NAME VALUE`

May be specified multiple times.

Complete list of filters:

[https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html)

Example: `--filter-aws tag-key production`

Note: If `instance-state-name` is present in the filter name, the `--status` option is ignored.

### Filter options (Azure)

Usage: `--filter-azure FILTER`

Note: This filtering is done in the client SDK using [JMESPath](http://jmespath.org/) to filter the JSON response.  You can view the JSON output using `--output JSON` or following the instance link in the HTML table.

Complete list of filters:

https://github.com/MicrosoftDocs/azure-docs-cli/blob/master/docs-ref-conceptual/query-azure-cli.md#filter-arrays

Example: `--filter-azure "location == 'westeurope' && !(name == 'admin')"`

Note: If `instance_view.statuses` is present in the filter, the `--status` option is ignored.

### Filter options (GCP)

Usage: `--filter-gcp FILTER`

Note: You may filter the resources listed in the API response.

Complete list of resources:

[https://cloud.google.com/compute/docs/reference/rest/v1/instances/list](https://cloud.google.com/compute/docs/reference/rest/v1/instances/list)

Example: `--filter-gcp 'name: instance-1 AND canIpForward: false'`

Note: If `status` is present in the filter, the `--status` option is ignored.

### Filter options (Openstack)

Usage: `--filter-openstack NAME VALUE`

May be specified multiple times.

Complete list of filters:

https://developer.openstack.org/api-ref/compute/?expanded=list-servers-detail#listServers

Example: `--filter-openstack name admin`

Note: If `status` is present in the filter, the `--status` option is ignored.

## TODO
  - Search by tag (this can be done with the `filter-*` options)
  - Sort by instance type (very tricky to get right ATM for all providers).
  - Use apache-libcloud? (slow for some providers)

## Similar projects

  - [public cloud watch](https://github.com/cfconrad/pcw/)
