FROM	registry.opensuse.org/opensuse/bci/python:3.11

RUN	zypper addrepo https://download.opensuse.org/repositories/SUSE:/CA/openSUSE_Tumbleweed/SUSE:CA.repo && \
	zypper --gpg-auto-import-keys -n install ca-certificates-suse && \
	zypper -n install \
		python3-apache-libcloud \
		python3-cachetools \
		python3-cryptography \
		python3-Jinja2 \
		python3-pyramid \
		python3-python-dateutil \
		python3-pytz \
		python311-PyYAML && \
	zypper clean -a

ENV	REQUESTS_CA_BUNDLE=/etc/ssl/ca-bundle.pem

COPY	cloudview/ /cloudview

ENTRYPOINT ["/usr/bin/python3", "-m", "cloudview.cloudview"]
