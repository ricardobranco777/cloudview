#!/bin/bash

set -e
umask 077

openssl_config() {
	cat /etc/ssl/openssl.cnf
	cat <<- EOF
	[custom]
	basicConstraints        = critical,CA:false
	nsCertType              = server
	subjectKeyIdentifier    = hash
	authorityKeyIdentifier  = keyid,issuer:always
	keyUsage                = critical,digitalSignature,keyEncipherment
	extendedKeyUsage        = serverAuth
	subjectAltName		= DNS:${NGINX_HOST:-localhost}
	EOF
}

# On read-only containers, openssl won't be able to write to ~/.rnd
export RANDFILE=/dev/null

SSL=/etc/nginx/ssl
if [ ! -f $SSL/key.pem ] ; then
	# Generate a random Base64 password
	openssl rand -base64 48 > $SSL/key.txt
	# Generate a self-signed certificate
	openssl req -x509 -sha512 -newkey rsa:4096 -keyout $SSL/key.pem -out $SSL/cert.pem -days 365 -subj "/CN=${NGINX_HOST:-localhost}" -passout file:$SSL/key.txt -extensions custom -config <(openssl_config)
fi

envsubst '$APP_PORT $NGINX_HOST' < /etc/nginx/conf.d/site.conf.template > /run/site.conf

exec nginx -g 'daemon off;'
