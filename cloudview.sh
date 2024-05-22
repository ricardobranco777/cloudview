#!/bin/bash

# Allow use of DOCKER=podman
DOCKER="${DOCKER:-docker}"
IMAGE="${IMAGE:-ghcr.io/ricardobranco777/cloudview:latest}"
ARGS=("$@")

CHECK_CERTIFICATES=(
	/etc/ssl/certs/ca-certificates.crt
	/etc/pki/tls/certs/ca-bundle.crt
	/etc/ssl/ca-bundle.pem
	/etc/ssl/cert.pem
)

CHECK_VARIABLES=(
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
# Openstack
mapfile -t openstack_variables < <(env | grep ^OS_ | awk -F= '{ print $1 }')
CHECK_VARIABLES+=("${openstack_variables[@]}")

name="cloudview$$"
container_options=(
	--security-opt label=disable
	--rm		# Remove container after running
	-it		# Allow user to interrupt execution
	--net=host	# Use host's DNS
	--name "$name"
	-e LIBCLOUD_DEBUG="$LIBCLOUD_DEBUG"
)

check_certificates() {
	if [ -z "$REQUESTS_CA_BUNDLE" ] ; then
		for file in "${CHECK_CERTIFICATES[@]}" ; do
			if [ -f "$file" ] ; then
				export REQUESTS_CA_BUNDLE="$file"
			fi
		done
	fi
}

check_certificates

# Get clouds.yaml
get_config () {
	index=-1
	for ((i=0; i<${#ARGS[@]}; i++)) ; do
		if [[ ${ARGS[i]} =~ ^-c|--config$ ]] ; then
			index="$i"
			break
		fi
	done
	if [[ $index -ge 0 ]] ; then
		clouds_yaml="${ARGS[$((index+1))]}"
		if [ -z "$clouds_yaml" ] ; then
			echo "ERROR: the ${ARGS[$index]} option needs an argument" >&2
			exit 1
		elif [ ! -f "$clouds_yaml" ] ; then
			echo "ERROR: No such file: $clouds_yaml" >&2
			exit 1
		fi
	else
		clouds_yaml="${clouds_yaml:-$HOME/clouds.yaml}"
		if [ -f "$clouds_yaml" ] ; then
			ARGS+=(--config "$clouds_yaml")
		fi
	fi
}

get_config

# Mount as volumes all values in clouds.yaml that are pathnames
volumes=()
if [ -f "$clouds_yaml" ] ; then
	volumes+=(-v "$clouds_yaml:$clouds_yaml:ro")
	mapfile -t values < <(sed -re 's/#.*//' -e 's/"(.*)"/\1/' -e "s/'(.*)'/\1/" < "$clouds_yaml" | awk '$NF ~ /^\// { print $NF }')
	for value in "${values[@]}" ; do
		if [ -f "$value" ] ; then
			volumes+=(-v "$value:$value:ro")
		fi
	done
fi

# Add variables
variables=()
for var in "${CHECK_VARIABLES[@]}" ; do
	if [[ -v $var ]] ; then
		variables+=(-e "$var")
	fi
	# Mount as volume if variable is a file
	if [[ -f ${!var} ]] ; then
		volumes+=(-v "${!var}:${!var}:ro")
	fi
done

echo "$DOCKER" run "${container_options[@]}" "${variables[@]}" "${volumes[@]}" "$IMAGE" "${ARGS[@]}"
exec "$DOCKER" run "${container_options[@]}" "${variables[@]}" "${volumes[@]}" "$IMAGE" "${ARGS[@]}"
