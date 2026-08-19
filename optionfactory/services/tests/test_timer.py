import os

import jinja2

from conftest import FakeCtx, make_plugin, recording_step

from ansible_collections.optionfactory.services.plugins.action import timer as timer_mod


TEMPLATES_DIR = os.path.join(
    os.path.dirname(timer_mod.__file__), os.pardir, "templates"
)


def render(template, **vars):
    env = jinja2.Environment(trim_blocks=True, keep_trailing_newline=True)
    with open(os.path.join(TEMPLATES_DIR, template)) as f:
        return env.from_string(f.read()).render(**vars)


def capturing_step(captured):
    def _step(self, ctx, conf):
        captured.append((ctx, conf))
        return None, False

    return _step


def make_timer_plugin(task_args, calls, changes=None):
    plugin = make_plugin(
        timer_mod,
        task_args=task_args,
        step=recording_step(calls, changes),
    )
    plugin.find_template = lambda filename: (None, filename)
    return plugin


def test_timer_command_provisions_units_and_starts_timer():
    calls = []
    plugin = make_timer_plugin(
        {
            "name": "backup",
            "command": {"exec": "/usr/bin/backup", "args": "--all"},
            "on_boot_sec": "15min",
            "on_unit_active_sec": "1w",
        },
        calls,
    )
    res = plugin.run(None, {})
    assert res["failed"] is False
    assert res["msg"] == "Timer provisioned: backup"
    svc, timer, sysd = calls
    assert svc["name"] == "ansible.builtin.template"
    assert svc["args"]["dest"] == "/etc/systemd/system/backup.service"
    assert svc["args"]["src"] == "command_oneshot_service.j2"
    assert timer["args"]["dest"] == "/etc/systemd/system/backup.timer"
    assert timer["args"]["src"] == "timer.j2"
    assert sysd["name"] == "ansible.builtin.systemd"
    assert sysd["args"]["name"] == "backup.timer"
    assert sysd["args"]["state"] == "started"
    assert sysd["args"]["enabled"] is True
    assert sysd["args"]["daemon_reload"] is False


def test_timer_container_defaults_to_engine_template():
    calls = []
    plugin = make_timer_plugin(
        {
            "name": "cert-renewal",
            "container": {"container": "nginx-myproject", "exec": "/legopfa-all"},
            "on_unit_active_sec": "1w",
        },
        calls,
    )
    res = plugin.run(None, {})
    assert res["failed"] is False
    assert calls[0]["args"]["src"] == "docker_oneshot_service.j2"


def test_timer_container_podman_template():
    calls = []
    plugin = make_timer_plugin(
        {
            "name": "cert-renewal",
            "container": {"engine": "podman", "container": "c", "exec": "/renew"},
            "on_unit_active_sec": "1d",
        },
        calls,
    )
    plugin.run(None, {})
    assert calls[0]["args"]["src"] == "podman_oneshot_service.j2"


def test_timer_daemon_reload_on_change():
    calls = []
    plugin = make_timer_plugin(
        {
            "name": "backup",
            "command": {"exec": "/usr/bin/backup"},
            "on_calendar": "daily",
        },
        calls,
        {"Configuring systemd unit: backup.timer": True},
    )
    res = plugin.run(None, {})
    assert res["changed"] is True
    assert calls[2]["args"]["daemon_reload"] is True


def test_timer_service_context_vars():
    captured = []
    plugin = make_plugin(
        timer_mod,
        task_args={
            "name": "cert-renewal",
            "container": {"container": "nginx-myproject", "exec": "/legopfa-all", "args": "--force", "opts": "-ti"},
            "on_unit_active_sec": "1w",
        },
        step=capturing_step(captured),
    )
    plugin.find_template = lambda filename: (None, filename)
    plugin.run(None, {})
    svc_ctx, _ = captured[0]
    assert svc_ctx.task_vars["name"] == "cert-renewal"
    assert svc_ctx.task_vars["container"] == "nginx-myproject"
    assert svc_ctx.task_vars["exec"] == "/legopfa-all"
    assert svc_ctx.task_vars["args"] == "--force"
    assert svc_ctx.task_vars["opts"] == "-ti"


def test_timer_unit_context_vars():
    captured = []
    plugin = make_plugin(timer_mod, step=capturing_step(captured))
    plugin.find_template = lambda filename: (None, filename)
    plugin.provision_timer_unit(
        FakeCtx(),
        "backup",
        {
            "on_boot_sec": "15min",
            "on_unit_active_sec": "1w",
            "on_calendar": None,
            "persistent": True,
        },
    )
    ctx, conf = captured[0]
    assert conf["args"]["dest"] == "/etc/systemd/system/backup.timer"
    assert ctx.task_vars["name"] == "backup"
    assert ctx.task_vars["on_boot_sec"] == "15min"
    assert ctx.task_vars["on_unit_active_sec"] == "1w"
    assert ctx.task_vars["on_calendar"] is None
    assert ctx.task_vars["persistent"] is True
    assert ctx.task_vars["accuracy_sec"] is None
    assert ctx.task_vars["randomized_delay_sec"] is None
    assert ctx.task_vars["unit"] is None


def test_timer_template_renders_legopfa_equivalent():
    out = render("timer.j2", name="cert-renewal", on_boot_sec="15min",
                 on_unit_active_sec="1w", on_calendar=None, persistent=False)
    assert out == (
        "[Unit]\n"
        "Description=cert-renewal timer\n"
        "\n"
        "[Timer]\n"
        "OnBootSec=15min\n"
        "OnUnitActiveSec=1w\n"
        "\n"
        "[Install]\n"
        "WantedBy=timers.target\n"
    )


def test_timer_template_renders_calendar_and_persistent():
    out = render("timer.j2", name="backup", on_boot_sec=None,
                 on_unit_active_sec=None, on_calendar="daily", persistent=True)
    assert "OnCalendar=daily" in out
    assert "Persistent=true" in out
    assert "OnBootSec" not in out
    assert "OnUnitActiveSec" not in out


def test_timer_template_renders_extra_options():
    out = render("timer.j2", name="backup", on_boot_sec=None,
                 on_unit_active_sec=None, on_calendar=None, persistent=False,
                 accuracy_sec="1min", randomized_delay_sec="30min",
                 unit="backup-job.service")
    assert "AccuracySec=1min" in out
    assert "RandomizedDelaySec=30min" in out
    assert "Unit=backup-job.service" in out


def test_timer_template_omits_extra_options_when_unset():
    out = render("timer.j2", name="backup", on_boot_sec=None,
                 on_unit_active_sec=None, on_calendar=None, persistent=False,
                 accuracy_sec=None, randomized_delay_sec=None, unit=None)
    assert "AccuracySec" not in out
    assert "RandomizedDelaySec" not in out
    assert "Unit=" not in out


def test_command_oneshot_service_template():
    out = render("command_oneshot_service.j2", name="backup", exec="/usr/bin/backup", args="--all")
    assert "Type=oneshot" in out
    assert "ExecStart=/usr/bin/backup --all" in out


def test_docker_oneshot_service_template():
    out = render("docker_oneshot_service.j2", name="cert-renewal", opts="",
                 container="nginx-myproject", exec="/legopfa-all", args="")
    assert " ".join(out.split()) .endswith(
        "ExecStart=/usr/bin/docker exec nginx-myproject /legopfa-all"
    )


def test_docker_oneshot_service_template_with_opts():
    out = render("docker_oneshot_service.j2", name="cert-renewal", opts="-ti",
                 container="nginx-myproject", exec="/renew", args="--force")
    assert "ExecStart=/usr/bin/docker exec -ti nginx-myproject /renew --force" in out


def test_podman_oneshot_service_template_with_opts():
    out = render("podman_oneshot_service.j2", name="cert-renewal", opts="--user root",
                 container="c", exec="/renew", args="")
    assert "ExecStart=/usr/bin/podman exec --user root c /renew" in out
