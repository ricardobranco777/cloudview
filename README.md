# cloudview
View instance information on all supported cloud providers

## Usage

```
Usage: cloudview [OPTIONS]
Options:
    -d, --debug                         debug mode
    -h, --help                          show this help message and exit
    -o, --output text|html|json|JSON    output type
    -p, --port PORT                     run a web server on port PORT
    -r, --reverse                       reverse sort
    -s, --sort name|time|status         sort type
    -S, --status stopped|running|all    filter by instance status
    -T, --time TIME_FORMAT              time format as used by strftime(3)
    -V, --version                       show version and exit
Filter options:
    --filter-aws NAME VALUE             may be specified multiple times
    --filter-azure FILTER               Filter for Azure
    --filter-gcp FILTER                 Filter for GCP
```

**NOTES**:
  - Use `--output JSON` to dump _all_ available information received from each provider.
  - Remember to set these environment variables:
    - `GOOGLE_APPLICATION_CREDENTIALS`
    - `AZURE_TENANT_ID`
    - `AZURE_SUBSCRIPTION_ID`
    - `AZURE_CLIENT_SECRET`
    - `AZURE_CLIENT_ID`

This script is best run with Docker to have all dependencies in just one package, but it may be run stand-alone on systems with Python 3.5+

## To run stand-alone:

```
pip install --user cloudview
```

## To run with Docker:

Build image with:
```
docker build -t cloud --pull .
```

Run with:
```
docker run --rm -v ~/.aws:/root/.aws:ro -v "$GOOGLE_APPLICATION_CREDENTIALS:$GOOGLE_APPLICATION_CREDENTIALS:ro" -e AZURE_TENANT_ID -e AZURE_SUBSCRIPTION_ID -e AZURE_CLIENT_SECRET -e AZURE_CLIENT_ID -e GOOGLE_APPLICATION_CREDENTIALS=/root/$(basename $GOOGLE_APPLICATION_CREDENTIALS) cloudview --status all
```

## Run the web server with [Docker Compose](https://docs.docker.com/compose/install/):

If you have a TLS key pair, rename the certificate to `cert.pem`, the private key to `key.pem` and the file containing the password to the private key to `key.txt`.  Then edit the [docker-compose.yml](docker-compose.yml) file to mount them to `/etc/nginx/ssl` in read-only mode like this: `- "/path/to/tls:/etc/nginx/ssl:ro"`.

If you don't have a TLS key pair, a self-signed certificate will be generated.  Be aware of the typical problems with time resolution related to TLS certificates.


```
docker-compose up -d
```

Now browse to [https://localhost:8443](https://localhost:8443)

To stop the web server:
```
docker-compose down
```

To rebuild with latest version:
```
docker-compose build --pull
```

## TODO
  - Search by tag
  - Sort by instance type
  - Use apache-libcloud?
