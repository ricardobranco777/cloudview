# cloudview
View instance information on all supported cloud providers

## Usage

```
Usage: cloudview [OPTIONS]
Options:
    -a, --all                           show all instances
    -o, --output text|html|json|JSON    output type
    -p, --port PORT                     run a web server on port PORT
    -r, --reverse                       reverse sort
    -s, --sort name|time|status         sort type
    -t, --time TIME_FORMAT              time format as used by strftime(3)
    -h, --help                          show this help message and exit
    -d, --debug                         debug mode
    -V, --version                       show version and exit
```

**NOTE**: Use `--output JSON` to dump _all_ available information received from each provider's SDK.

This script is best run with Docker to have all dependencies in just one packages, but it may be run stand-alone on systems with Python 3.4+

## To run stand-alone:

```
pip install --user cloudview
```

**NOTE**: You may need to upgrade `pip` before with `pip install --user --upgrade pip`.

## To run with Docker:

Build image with:
```
docker build -t cloud --pull .
```

Run with:
```
docker run --rm -v ~/.aws:/root/.aws:ro -v "$GOOGLE_APPLICATION_CREDENTIALS:$GOOGLE_APPLICATION_CREDENTIALS:ro" -e AZURE_TENANT_ID -e AZURE_SUBSCRIPTION_ID -e AZURE_CLIENT_SECRET -e AZURE_CLIENT_ID -e GOOGLE_APPLICATION_CREDENTIALS=/root/$(basename $GOOGLE_APPLICATION_CREDENTIALS) cloudview --all --port 7777
```

To set up a web server showing this information running on port 7777:
```
docker run --rm -d -p 7777:7777 -v ~/.aws:/root/.aws:ro -v "$GOOGLE_APPLICATION_CREDENTIALS:$GOOGLE_APPLICATION_CREDENTIALS:ro" -e AZURE_TENANT_ID -e AZURE_SUBSCRIPTION_ID -e AZURE_CLIENT_SECRET -e AZURE_CLIENT_ID -e GOOGLE_APPLICATION_CREDENTIALS cloudview --all --port 7777
```

## Run the web server with [Docker Compose](https://docs.docker.com/compose/install/):

```
docker-compose up -d
```

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
  - Expose filtering functionality
