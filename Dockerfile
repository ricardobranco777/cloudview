FROM	python:3.11-alpine

COPY	requirements.txt /

RUN	apk --no-cache add tzdata && \
	pip install --compile --no-cache-dir -r /requirements.txt && \
	python3 -OO -m compileall

COPY	scripts /scripts
COPY	setup.py README.md LICENSE /
COPY	cloudview/ /cloudview

RUN	pip install --compile .

ENTRYPOINT ["/usr/local/bin/cloudview"]

CMD []
