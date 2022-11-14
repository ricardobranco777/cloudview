FROM	python:3.11-alpine

COPY	requirements.txt /tmp/

RUN	apk --no-cache --virtual .build-deps add \
		gcc \
		libc-dev \
		libffi-dev \
		make \
		openssl-dev && \
	apk --no-cache add tzdata && \
	pip install --compile --no-cache-dir -r /tmp/requirements.txt && \
	apk del .build-deps

COPY	. /cloudview

RUN	pip install --compile /cloudview && \
	python3 -OO -m compileall

ENTRYPOINT ["/usr/local/bin/cloudview"]

CMD []
