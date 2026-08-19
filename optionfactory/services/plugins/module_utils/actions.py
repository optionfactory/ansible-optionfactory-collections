import os
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


def log_step(msg):
    display.display(f"  🔸 {msg}", color='bright purple')


def log_skipped():
    display.display(f"     🔼 ⏩ (skipped)", color='bright purple')


def log_changed():
    display.display(f"     🔼 🔁 (changed)", color='bright purple')


def prefixed(result, prefix):
    if not result.get('failed', False):
        return None
    source = result.get('msg', 'Unknown error occurred')
    result["msg"] = f"{prefix}: {source}"
    return result


def failure(msg):
    return {
        'changed': False,
        'failed': True,
        'msg': msg
    }


class Context:
    def __init__(self, tmp, task_vars):
        self.tmp = tmp
        self.task_vars = task_vars
    def with_updated_vars(self, dict):
        new_task_vars = self.task_vars.copy()
        new_task_vars.update(dict)
        return Context(self.tmp, new_task_vars)

class Action(ActionBase):
    ARGUMENT_SPEC = {}
    VALIDATOR_KWARGS = {}

    def step(self, ctx, conf):
        """
        Runs conf['name'] through the right execution path, chosen
        automatically by mirroring TaskExecutor's own resolution:

        1. if the target has a dedicated action plugin (ansible.builtin.copy,
           ansible.builtin.template, ...) the controller-side action runs
           (action_step) — required for controller-side template rendering
           with ctx.task_vars and for 'src' lookup via _find_needle;
        2. otherwise the module is executed on the managed node
           (module_step).

        Call sites must use this instead of picking a helper by hand: the
        availability of an action plugin can vary across ansible-core
        versions, and this dispatch adapts to the running one.

        C(conf) keys: step (log label), name (target FQCN), args, when
        (skips the step when falsy).
        """
        name = conf.get('name')
        mctx = self._shared_loader_obj.module_loader.find_plugin_with_context(
            name, collection_list=self._task.collections
        )
        has_action = (
            (mctx.resolved and mctx.action_plugin)
            or self._shared_loader_obj.action_loader.has_plugin(name, collection_list=self._task.collections)
        )
        if has_action:
            return self.action_step(ctx, conf)
        return self.module_step(ctx, conf)

    def module_step(self, ctx, conf):
        """
        Execution primitive: runs a plain module on the managed node via
        C(_execute_module). Do not call directly from plugins — use step(),
        which dispatches here when the target has no action plugin.

        C(conf) keys: step (log label), name (module FQCN), args (module
        args), when (skips the step when falsy).
        """
        if conf.get('step'):
            log_step(conf.get('step'))
        if not boolean(conf.get('when', True)):
            log_skipped()
            return None, False
        res = self._execute_module(
            module_name=conf.get('name'),
            task_vars=ctx.task_vars,
            tmp=ctx.tmp,
            module_args=conf.get('args') or {}
        )
        changed = res.get('changed', False)
        prefix = f"{conf.get('step')} failed"
        if changed:
            log_changed()
        return prefixed(res, prefix), changed

    def action_step(self, ctx, conf):
        """
        Execution primitive: runs the target's action plugin on the
        CONTROLLER, replacing the current task's action and args. Do not
        call directly from plugins — use step(), which dispatches here when
        the target has an action plugin (e.g. copy, template).

        C(conf) keys: step (log label), name (action FQCN), args (action
        args), when (skips the step when falsy).
        """
        new_task = self._task.copy()
        new_task.action = conf.get('name')
        new_task.args = conf.get('args')
        if conf.get('step'):
            log_step(conf.get('step'))
        if not boolean(conf.get('when', True)):
            log_skipped()
            return None, False
        action = self._shared_loader_obj.action_loader.get(
            conf.get('name'),
            task=new_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj
        )
        res = action.run(tmp=ctx.tmp, task_vars=ctx.task_vars)
        changed = res.get('changed', False)
        prefix = f"{conf.get('step')} failed"
        if changed:
            log_changed()
        return prefixed(res, prefix), res.get('changed', False)

    def find_resource(self, what, filename):
        try:
            found = self._find_needle(what, filename)
            return None, found
        except AnsibleError:
            plugin_dir = os.path.dirname(__file__)
            plugin_sub_dir = os.path.abspath(os.path.join(plugin_dir, f'../{ what }'))
            found = os.path.join(plugin_sub_dir, filename)
            if not os.path.exists(found):
                return failure(f"In '{ what }': '{filename}' not found in user paths or plugin defaults."), None
            return None, found

    def find_template(self, filename):
        return self.find_resource('templates', filename)
    def find_file(self, filename):
        return self.find_resource('files', filename)

    def run(self, tmp=None, task_vars=None):
        super(Action, self).run(tmp, task_vars)
        validation_result, valid_args = self.validate_argument_spec(self.ARGUMENT_SPEC, **self.VALIDATOR_KWARGS)
        return valid_args, Context(tmp, task_vars)


SERVICE_ENGINES = ('container', 'command')


def resolve_engine(args, template_kind='service'):
    engine = next(e for e in SERVICE_ENGINES if args.get(e))
    block = dict(args.get(engine))
    if engine == 'container' and not block.get('template'):
        block['template'] = f"{block.get('engine', 'docker')}_{template_kind}.j2"
    return engine, block


def service_vars(name, engine, block):
    vars = {'name': name, **block}
    if engine == 'container':
        flags = []
        for opt in ('network', 'ip'):
            if block.get(opt):
                flags.append(f"--{opt} {block[opt]}")
        for k, val in (block.get('env') or {}).items():
            flags.append(f"--env {k}={val}")
        for p in block.get('publish') or []:
            p = (p or '').strip()
            if p:
                flags.append(f"-p {p}")
        for m in block.get('mounts') or []:
            if not boolean(m.get('when', True)):
                continue
            flag = f"--mount type=bind,source={m['source']},target={m['target']}"
            if m.get('readonly'):
                flag += ',readonly'
            flags.append(flag)
        for v in block.get('volumes') or []:
            v = (v or '').strip()
            if v:
                flags.append(f"--volume {v}")
        vars['opts'] = ' '.join(filter(None, [' '.join(flags), (block.get('opts') or '').strip()]))
    return vars
