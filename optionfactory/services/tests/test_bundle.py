from conftest import FakeCtx, make_plugin, recording_step

from ansible_collections.optionfactory.services.plugins.action import bundle as bundle_mod


def test_provision_dirs_when_skip_and_overrides():
    calls = []
    plugin = make_plugin(bundle_mod, step=recording_step(calls))
    dirs = [
        {"dest": "/opt/a", "when": False},
        {"dest": "/opt/b", "when": True},
        {"dest": "/opt/c", "when": True, "owner": "root", "mode": "0755"},
    ]
    err, changed = plugin.provision_dirs(FakeCtx(), dirs, "docker-machines", "docker-machines")
    assert (err, changed) == (None, False)
    assert [c["args"]["dest"] for c in calls] == ["/opt/b", "/opt/c"]
    assert calls[0]["args"]["owner"] == "docker-machines"
    assert calls[0]["args"]["mode"] == "0750"
    assert calls[1]["args"]["owner"] == "root"
    assert calls[1]["args"]["mode"] == "0755"


def test_provision_files_inline_content():
    calls = []
    plugin = make_plugin(bundle_mod, step=recording_step(calls))
    files = [{"dest": "/opt/x/y.conf", "content": "k=v", "when": True}]
    err, changed = plugin.provision_files(FakeCtx(), files, "svcuser", "svcgroup")
    assert (err, changed) == (None, False)
    args = calls[0]["args"]
    assert args["content"] == "k=v"
    assert args["owner"] == "svcuser"
    assert args["group"] == "svcgroup"
    assert args["mode"] == "0640"


def test_provision_files_src_lookup():
    calls = []
    plugin = make_plugin(bundle_mod, step=recording_step(calls))
    plugin._find_needle = lambda what, name: f"/needle/{what}/{name}"
    files = [{"dest": "/opt/x/app.jar", "src": "app.jar", "when": True}]
    err, changed = plugin.provision_files(FakeCtx(), files, "o", "g")
    assert err is None
    assert calls[0]["args"]["src"] == "/needle/files/app.jar"
    assert calls[0]["args"]["remote_src"] is False
