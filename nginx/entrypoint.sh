#!/bin/bash

envsubst '$APP_PORT $NGINX_HOST' < /etc/nginx/conf.d/site.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
