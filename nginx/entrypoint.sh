#!/bin/bash

envsubst '$APP_PORT $NGINX_HOST' < /etc/nginx/conf.d/site.conf.template > /run/site.conf

exec nginx -g 'daemon off;'
