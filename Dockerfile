FROM	python:3.9-alpine

COPY	requirements.txt /tmp

RUN	apk --no-cache --virtual .build-deps add \
		cargo \
		gcc \
		libc-dev \
		libffi-dev \
		make \
		openssl-dev \
		rust && \
	apk --no-cache add tzdata && \
	pip install --compile --no-cache-dir -r /tmp/requirements.txt && \
	apk del .build-deps

COPY	. /cloudview

RUN	pip install /cloudview && \
	python3 -OO -m compileall && \
	python3 -OO -m compileall /cloudview

ENV 	PYTHONPATH	/cloudview


ENTRYPOINT ["/cloudview/cloudview"]

CMD []
