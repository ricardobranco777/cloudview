# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,no-member,unused-argument

import contextlib
import json
import logging
import random
import os
import shlex
import shutil
import sys
from subprocess import DEVNULL

import pytest
import docker
from docker.errors import DockerException
from requests.exceptions import RequestException
from podman import PodmanClient
from podman.errors import APIError, PodmanError
from selenium.webdriver import firefox
from selenium.common.exceptions import WebDriverException


@pytest.fixture(scope="session")
def client():
    if os.getenv("SKIP_SELENIUM"):
        pytest.skip("Skipping because SKIP_SELENIUM is set")

    if not shutil.which("geckodriver"):
        pytest.skip("Please install geckodriver in your PATH. Skipping...")

    try:
        client = docker.from_env()
    except (DockerException, RequestException) as exc:
        logging.warning("%s", exc)
        try:
            client = PodmanClient()
        except (APIError, PodmanError) as exc:
            pytest.skip(f"Broken Podman environment: {exc}")
        if not client.info()["host"]["remoteSocket"]["exists"]:
            pytest.skip("Please run systemctl --user enable --now podman.socket")

    yield client

    client.close()


@pytest.fixture(scope="session")
def random_port():
    # Get random number for ephemeral port, container and image name
    # Typical values from /proc/sys/net/ipv4/ip_local_port_range
    return random.randint(32768, 60999)


@pytest.fixture(scope="session")
def image(random_port, client):
    image_name = f"cloudview-test{random_port}"

    # Build image
    try:
        client.images.build(
            path=".",
            dockerfile="Dockerfile",
            tag=image_name,
        )
    except APIError as exc:
        pytest.skip(f"Broken Podman environment: {exc}")
    except RequestException as exc:
        pytest.skip(f"Broken Docker environment: {exc}")
    except (DockerException, PodmanError) as exc:
        for log in exc.build_log:
            line = json.loads(log.decode("utf-8"))
            if line:
                print(line.get("stream"), file=sys.stderr, end="")
        pytest.fail(f"{exc}")

    yield image_name

    # Cleanup
    with contextlib.suppress(APIError, PodmanError, DockerException, RequestException):
        client.images.remove(image_name)


@pytest.fixture(scope="session")
def container(random_port, image, client):
    try:
        # Run container
        container = client.containers.run(
            image=image,
            name=image,
            detach=True,
            command=shlex.split(f"--port {7777}"),
            ports={f"{7777}/tcp": random_port},
        )
    except (APIError, PodmanError, DockerException, RequestException) as exc:
        pytest.fail(f"{exc}")

    yield container

    # Cleanup
    with contextlib.suppress(APIError, PodmanError, DockerException, RequestException):
        print(container.logs(), file=sys.stderr)
    with contextlib.suppress(APIError, PodmanError, DockerException, RequestException):
        container.stop()
    with contextlib.suppress(APIError, PodmanError, DockerException, RequestException):
        container.remove()


@pytest.fixture
def browser(container):
    service = firefox.service.Service(
        log_output=sys.stderr if os.getenv("DEBUG") else DEVNULL
    )
    options = firefox.options.Options()
    options.add_argument("--headless")
    try:
        driver = firefox.webdriver.WebDriver(options=options, service=service)
    except WebDriverException as exc:
        pytest.fail(f"{exc}")
    driver.set_page_load_timeout(30)
    yield driver
    driver.quit()


def test_web(random_port, browser):
    try:
        browser.get(f"http://127.0.0.1:{random_port}")
    except WebDriverException as exc:
        pytest.fail(f"{exc}")
    assert "Instances" in browser.title
