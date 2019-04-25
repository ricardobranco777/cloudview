FROM	python:3.7-alpine

COPY	requirements.txt /tmp

RUN	apk --no-cache --virtual .build-deps add \
		gcc \
		libc-dev \
		libffi-dev \
		make \
		openssl-dev && \
	pip install --no-cache-dir -r /tmp/requirements.txt && \
	ln -s /usr/local/bin/python3 /usr/bin/python3 && \
	apk del .build-deps

COPY	cloudview /cloudview
COPY	scripts/cloudview /usr/local/bin/

RUN	python3 -OO -m compileall && \
	python3 -OO -m compileall /cloudview/

ENV	PYTHONPATH	.

ENTRYPOINT ["/usr/local/bin/cloudview"]

CMD []
