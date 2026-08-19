import os
import sys
import types

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
COLLECTION_SRC = os.path.join(REPO_ROOT, "optionfactory", "services")
LINK_ROOT = os.path.join(REPO_ROOT, ".ansible", "collections-test")


def _link_collection():
    """
    Expose the in-repo collection under an 'ansible_collections' namespace
    tree so FQCN imports ('ansible_collections.optionfactory.services...')
    resolve. Must run at conftest import time: test modules perform those
    imports at collection time, before any fixture can run.

    The tree lives inside the checkout (no shared /tmp state) and points at
    the collection via a RELATIVE symlink, so it survives repo moves and
    always tests live code. This mirrors Ansible's documented dev workflow
    of linking a collection into a collections path.
    """
    ns = os.path.join(LINK_ROOT, "ansible_collections", "optionfactory")
    os.makedirs(ns, exist_ok=True)
    dst = os.path.join(ns, "services")
    rel = os.path.relpath(COLLECTION_SRC, ns)
    if os.path.islink(dst):
        if os.readlink(dst) != rel:
            os.remove(dst)
    elif os.path.exists(dst):
        raise RuntimeError(f"unexpected real path at {dst}; remove it to run tests")
    if not os.path.islink(dst):
        os.symlink(rel, dst)
    return LINK_ROOT


sys.path.insert(0, _link_collection())


class FakeTask:
    async_val = 0
    check_mode = False
    diff = False
    no_log = False
    args = {}
    collections = None


class FakeShell:
    tmpdir = "/tmp/ofc-unit"


class FakeConnection:
    _shell = FakeShell()
    has_pipelining = False


class FakeCtx:
    def __init__(self, facts=None, task_vars=None):
        self.task_vars = task_vars if task_vars is not None else {"ansible_facts": facts or {}}

    def with_updated_vars(self, updated):
        new = FakeCtx(task_vars=self.task_vars.copy())
        new.task_vars.update(updated)
        return new


def make_plugin(module, step=None, task_args=None, shared_loader_obj=None):
    task = FakeTask()
    if task_args is not None:
        task.args = dict(task_args)
    plugin = module.ActionModule(
        task=task,
        connection=FakeConnection(),
        play_context=None,
        loader=None,
        templar=None,
        shared_loader_obj=None,
    )
    if shared_loader_obj is not None:
        plugin._shared_loader_obj = shared_loader_obj
    if step is not None:
        plugin.step = types.MethodType(step, plugin)
    return plugin


def recording_step(calls, changes=None):
    changes = changes or {}

    def _step(self, ctx, conf):
        calls.append(conf)
        return None, changes.get(conf.get("step"), False)

    return _step
