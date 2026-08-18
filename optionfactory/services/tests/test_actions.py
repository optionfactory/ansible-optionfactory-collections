import pytest

from ansible_collections.optionfactory.services.plugins.module_utils.actions import resolve_engine, service_vars


def test_resolve_engine_container_default_template():
    engine, block = resolve_engine({"container": {"image": "img:1"}})
    assert engine == "container"
    assert block["template"] == "docker_service.j2"


def test_resolve_engine_podman_template():
    engine, block = resolve_engine({"container": {"engine": "podman", "image": "img:1"}})
    assert engine == "container"
    assert block["template"] == "podman_service.j2"


def test_resolve_engine_explicit_template_preserved():
    engine, block = resolve_engine({"container": {"image": "img:1", "template": "custom.j2"}})
    assert block["template"] == "custom.j2"


def test_resolve_engine_command_default_template():
    engine, block = resolve_engine({"command": {"exec": "/bin/x"}})
    assert engine == "command"
    assert block["exec"] == "/bin/x"
    assert "template" not in block


def test_resolve_engine_container_wins_when_both():
    engine, _ = resolve_engine({"container": {"image": "i"}, "command": {"exec": "/bin/x"}})
    assert engine == "container"


def test_resolve_engine_none_raises():
    with pytest.raises(StopIteration):
        resolve_engine({"name": "svc"})


def test_service_vars_container_full():
    vars = service_vars("svc", "container", {
        "image": "img:1",
        "network": "net1",
        "ip": "172.18.0.5",
        "env": {"A": "1", "B": "2"},
        "publish": ["0.0.0.0:80:80", ""],
        "mounts": [
            {"source": "/s", "target": "/t"},
            {"source": "/s2", "target": "/t2", "readonly": True},
            {"source": "/s3", "target": "/t3", "when": False},
        ],
        "volumes": ["v:/data", ""],
        "opts": " --restart unless-stopped ",
    })
    assert vars["name"] == "svc"
    assert vars["image"] == "img:1"
    assert vars["opts"] == (
        "--network net1 --ip 172.18.0.5 "
        "--env A=1 --env B=2 "
        "-p 0.0.0.0:80:80 "
        "--mount type=bind,source=/s,target=/t "
        "--mount type=bind,source=/s2,target=/t2,readonly "
        "--volume v:/data "
        "--restart unless-stopped"
    )


def test_service_vars_container_empty_values_ignored():
    vars = service_vars("svc", "container", {
        "image": "img:1",
        "network": "",
        "ip": "",
        "opts": "",
        "publish": ["", ""],
        "volumes": [""],
    })
    assert vars["opts"] == ""


def test_service_vars_command_passthrough():
    vars = service_vars("agent", "command", {"exec": "/usr/bin/x", "args": "--foo"})
    assert vars == {"name": "agent", "exec": "/usr/bin/x", "args": "--foo"}
