from conftest import FakeCtx, make_plugin, recording_step

from ansible_collections.optionfactory.services.plugins.action import docker as docker_mod

DEBIAN_FACTS = {
    "os_family": "Debian",
    "distribution": "Ubuntu",
    "distribution_release": "noble",
    "architecture": "x86_64",
}
REDHAT_FACTS = {
    "os_family": "RedHat",
    "distribution_major_version": "9",
    "architecture": "x86_64",
}


def repo_calls():
    calls = []
    return calls, make_plugin(docker_mod, step=recording_step(calls))


def steps(calls):
    return [f"{c['name'].split('.')[-1]}:{c.get('step')}" for c in calls]


def test_repository_skipped_for_docker_io():
    calls, plugin = repo_calls()
    err, changed = plugin.configure_repository(FakeCtx(DEBIAN_FACTS), "docker.io")
    assert (err, changed, calls) == (None, False, [])


def test_repository_debian():
    calls, plugin = repo_calls()
    err, changed = plugin.configure_repository(FakeCtx(DEBIAN_FACTS), "docker-ce")
    assert err is None
    assert steps(calls) == [
        "package:Ensuring base dependencies are present",
        "deb822_repository:Adding Docker APT repository",
    ]
    assert calls[0]["args"]["name"] == ["ca-certificates"]
    assert calls[-1]["args"] == {
        "name": "docker",
        "types": "deb",
        "uris": "https://download.docker.com/linux/ubuntu",
        "suites": "noble",
        "components": "stable",
        "architectures": "amd64",
        "signed_by": "https://download.docker.com/linux/ubuntu/gpg",
    }


def test_repository_debian_arm64():
    calls, plugin = repo_calls()
    facts = dict(DEBIAN_FACTS, architecture="aarch64")
    plugin.configure_repository(FakeCtx(facts), "docker-ce")
    assert calls[-1]["args"]["architectures"] == "arm64"


def test_repository_redhat():
    calls, plugin = repo_calls()
    err, changed = plugin.configure_repository(FakeCtx(REDHAT_FACTS), "docker-ce")
    assert err is None
    assert steps(calls) == [
        "package:Ensuring base dependencies are present",
        "yum_repository:Adding Docker YUM repository",
    ]
    args = calls[-1]["args"]
    assert args["baseurl"] == "https://download.docker.com/linux/centos/9/$basearch/stable"
    assert args["gpgcheck"] is True
    assert args["gpgkey"] == "https://download.docker.com/linux/centos/gpg"
    assert args["file"] == "docker-ce"


def test_repository_unknown_family_degrades_gracefully():
    calls, plugin = repo_calls()
    err, changed = plugin.configure_repository(FakeCtx({"os_family": "Suse"}), "docker-ce")
    assert err is None
    assert steps(calls) == ["package:Ensuring base dependencies are present"]


def test_proxies_content_and_restart():
    calls = []
    plugin = make_plugin(docker_mod, step=recording_step(calls))
    err, changed = plugin.configure_proxies(FakeCtx(), {"http": "http://p:8080", "noproxy": "a,b"})
    assert err is None
    copy_conf = next(c for c in calls if c["name"] == "ansible.builtin.copy")
    assert copy_conf["args"]["content"] == (
        '[Service]\nEnvironment="HTTP_PROXY=http://p:8080"\nEnvironment="NO_PROXY=a,b"'
    )
    restart = next(c for c in calls if c["name"] == "ansible.builtin.systemd")
    assert restart["args"]["state"] == "restarted"
    assert restart["args"]["daemon_reload"] is True


def test_proxies_skipped_when_empty():
    calls = []
    plugin = make_plugin(docker_mod, step=recording_step(calls))
    err, changed = plugin.configure_proxies(FakeCtx(), {})
    assert (err, changed) == (None, False)
    assert calls == []


def test_run_step_order_and_changed_aggregation():
    calls = []
    plugin = make_plugin(
        docker_mod,
        task_args={},
        step=recording_step(calls, {"Adding Docker APT repository": True}),
    )
    res = plugin.run(None, FakeCtx(DEBIAN_FACTS).task_vars)
    assert res["failed"] is False
    assert res["changed"] is True
    assert [c.get("step") for c in calls] == [
        "Ensuring base dependencies are present",
        "Adding Docker APT repository",
        "Ensuring docker package 'docker-ce' is installed",
        "Provisioning group docker-machines",
        "Provisioning user docker-machines",
        "Ensuring docker is started",
    ]


def test_run_unchanged_when_no_step_changed():
    calls = []
    plugin = make_plugin(docker_mod, task_args={}, step=recording_step(calls))
    res = plugin.run(None, FakeCtx(DEBIAN_FACTS).task_vars)
    assert res["failed"] is False
    assert res["changed"] is False
