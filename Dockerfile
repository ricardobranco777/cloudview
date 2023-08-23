FROM	python:3.11-alpine

COPY	requirements.txt /

RUN	apk --no-cache add tzdata && \
	pip install --no-cache-dir -r /requirements.txt

COPY	scripts /scripts
COPY	setup.py README.md LICENSE /
COPY	cloudview/ /cloudview

RUN	pip install .

ENTRYPOINT ["/usr/local/bin/cloudview"]

CMD []
