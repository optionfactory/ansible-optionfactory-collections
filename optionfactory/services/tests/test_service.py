import os

import jinja2

from conftest import COLLECTION_SRC


def test_docker_unit_adds_routes_to_the_container_after_start():
    with open(os.path.join(COLLECTION_SRC, "plugins", "templates", "docker_service.j2")) as f:
        template = jinja2.Environment(trim_blocks=True, keep_trailing_newline=True).from_string(f.read())
    unit = template.render(
        name="app",
        opts="",
        image="img:1",
        args="",
        routes=[
            {"to": "172.19.20.0/24", "via": "172.19.10.1"},
            {"to": "172.19.30.0/24", "via": "172.19.10.1"},
        ],
    )
    route = 'nsenter --net="$$ns" ip route replace'
    assert f"{route} 172.19.20.0/24 via 172.19.10.1 \\\n" in unit
    assert f"{route} 172.19.30.0/24 via 172.19.10.1; \\\n" in unit
