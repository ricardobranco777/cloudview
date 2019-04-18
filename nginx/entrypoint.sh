#!/bin/bash

set -e
umask 077

envsubst '$APP_PORT $NGINX_HOST' < /etc/nginx/conf.d/site.conf.template > /run/site.conf

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

	# Generate a random salt of 16 characters
	SALT=$(openssl rand -base64 12)
	# The salt character set is [a-zA-Z0-9./]
	SALT=${SALT//+/.}
	if [ -z "$PASS" ] ; then
		# Generate a random password
		PASS=$(openssl rand -base64 48)
		echo "Password for HTTP Basic Authentication is $PASS"
	fi
	# Hash password with 100000 rounds of salted SHA-512
	#PASS=$(mkpasswd -m sha-512 -S "$SALT" -R 100000 "$PASS")
	PASS=$(perl -e "print crypt('$PASS', '\$6\$rounds=100000\$$PASS')")
	echo "test:$PASS" >> $SSL/auth.htpasswd
	unset PASS
	chmod 644 $SSL/auth.htpasswd
elif [ ! -f $SSL/auth.htpasswd ] ; then
	sed -i '/auth_basic/d' /run/site.conf
fi

exec nginx -g 'daemon off;'
