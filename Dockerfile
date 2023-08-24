FROM	python:3.11-alpine

COPY	requirements.txt /

RUN	apk --no-cache add tzdata && \
	pip install --no-cache-dir -r /requirements.txt

COPY	cloudview/ /cloudview

ENTRYPOINT ["/usr/local/bin/python3", "-m", "cloudview.cloudview"]

CMD []
