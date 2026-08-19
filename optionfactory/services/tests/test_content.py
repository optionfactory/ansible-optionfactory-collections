from conftest import make_plugin, recording_step

from ansible_collections.optionfactory.services.plugins.action import journald as journald_mod
from ansible_collections.optionfactory.services.plugins.action import ps1 as ps1_mod


def test_journald_config_content():
    calls = []
    conf = "[Journal]\nStorage=persistent\n"
    plugin = make_plugin(
        journald_mod,
        task_args={"persistent": False, "configuration": conf},
        step=recording_step(calls),
    )
    res = plugin.run(None, {})
    assert res["failed"] is False
    copy_conf = calls[0]
    assert copy_conf["name"] == "ansible.builtin.copy"
    assert copy_conf["args"]["dest"] == "/etc/systemd/journald.conf"
    assert copy_conf["args"]["content"] == conf
    assert calls[1]["args"]["state"] == "started"


def test_journald_restarts_on_change():
    calls = []
    plugin = make_plugin(
        journald_mod,
        task_args={"persistent": True, "configuration": "[Journal]\n"},
        step=recording_step(calls, {"Provisioning journald configuration": True}),
    )
    plugin.run(None, {})
    assert calls[-1]["args"]["state"] == "restarted"


def test_journald_persistent_directory():
    calls = []
    plugin = make_plugin(
        journald_mod,
        task_args={"persistent": True},
        step=recording_step(calls),
    )
    plugin.run(None, {})
    assert calls[0]["name"] == "ansible.builtin.file"
    assert calls[0]["args"]["path"] == "/var/log/journal"
    assert calls[0]["args"]["state"] == "directory"


def test_ps1_profile():
    calls = []
    plugin = make_plugin(ps1_mod, task_args={}, step=recording_step(calls))
    res = plugin.run(None, {})
    assert res["failed"] is False
    assert res["msg"] == "PS1 profile provisioned."
    conf = calls[0]
    assert conf["name"] == "ansible.builtin.copy"
    assert conf["args"]["dest"] == "/etc/profile.d/ps1.sh"
    assert conf["args"]["mode"] == "0644"
    assert "PROMPT_COMMAND" in conf["args"]["content"]
