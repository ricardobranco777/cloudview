FROM	python:3.10-alpine

COPY	requirements.txt /tmp/

RUN	apk --no-cache --virtual .build-deps add \
		gcc \
		g++ \
		libc-dev \
		libffi-dev \
		libstdc++ \
		make \
		openssl-dev && \
	apk add libstdc++ && \
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
