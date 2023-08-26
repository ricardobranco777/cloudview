#!/bin/bash

IMAGE="${IMAGE:-ghcr.io/ricardobranco777/cloudview:latest}"
ARGS=("$@")

check_certificates=(
	/etc/ssl/certs/ca-certificates.crt
	/etc/pki/tls/certs/ca-bundle.crt
	/etc/ssl/ca-bundle.pem
	/etc/ssl/cert.pem
)

if [ -z "$REQUESTS_CA_BUNDLE" ] ; then
	for file in "${check_certificates[@]}" ; do
		if [ -f "$file" ] ; then
			export REQUESTS_CA_BUNDLE="$file"
		fi
	done
fi

# Get -c option
get_config () {
	args=("$@")

	index=-1
	for i in "${!args[@]}"; do
		if [[ ${args[i]} =~ ^-c|--config$ ]] ; then
			index="$i"
			break
		fi
	done
	if [[ $index -ge 0 ]] ; then
		echo "${args[$((++i))]}"
	fi
}

# Add "-c ~/clouds.yaml" if it exists
clouds_yaml="$(get_config "$@")"
if [[ -z $clouds_yaml ]] ; then
	clouds_yaml="${clouds_yaml:-$HOME/clouds.yaml}"
	if [ -f "$clouds_yaml" ] ; then
		ARGS+=(--config "$clouds_yaml")
	fi
fi

# Mount as volumes all variables in clouds.yaml
volumes=()
if [ -f "$clouds_yaml" ] ; then
	volumes+=(-v "$clouds_yaml:$clouds_yaml:ro")
	mapfile -t files < <(grep -v ' *#' < "$clouds_yaml" | awk '$NF ~ /^\// { print $NF }' | sed -e 's/"\(.*\)"/\1/' -e "s/'\(.*\)'/\1/")
	for file in "${files[@]}" ; do
		if [ -f "$file" ] ; then
			volumes+=(-v "$file:$file:ro")
		fi
	done
fi

# Add variables

# Openstack
mapfile -t check_variables < <(env | grep ^OS_ | awk -F= '{ print $1 }')
check_variables+=(
	# System certificates
	REQUESTS_CA_BUNDLE
	# EC2
	AWS_ACCESS_KEY_ID
	AWS_SECRET_ACCESS_KEY
	# Azure
	AZURE_CLIENT_ID
	AZURE_CLIENT_SECRET
	AZURE_TENANT_ID
	AZURE_SUBSCRIPTION_ID
	# Azure (Terraform)
	ARM_CLIENT_ID
	ARM_CLIENT_SECRET
	ARM_TENANT_ID
	ARM_SUBSCRIPTION_ID
	# GCE
	GOOGLE_APPLICATION_CREDENTIALS
)

variables=()
for var in "${check_variables[@]}" ; do
	if [[ -v $var ]] ; then
		variables+=(-e "$var")
	fi
	# Mount as volume if variable is a file
	if [[ -f ${!var} ]] ; then
		volumes+=(-v "${!var}:${!var}:ro")
	fi
done

name="cloudview$$"
echo docker run --rm -it --net=host --name "$name" -e LIBCLOUD_DEBUG="$LIBCLOUD_DEBUG" "${variables[@]}" "${volumes[@]}" "$IMAGE" "${ARGS[@]}"
exec docker run --rm -it --net=host --name "$name" -e LIBCLOUD_DEBUG="$LIBCLOUD_DEBUG" "${variables[@]}" "${volumes[@]}" "$IMAGE" "${ARGS[@]}"
