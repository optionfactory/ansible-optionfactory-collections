

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

    def module_step(self, ctx, conf):
        if conf.get('step'):
            log_step(conf.get('step'))
        if not conf.get('when', True):
            log_skipped()
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
        new_task = self._task.copy()
        new_task.action = conf.get('name')
        new_task.args = conf.get('args')
        if conf.get('step'):
            log_step(conf.get('step'))
        if not conf.get('when', True):
            log_skipped()
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

    def run(self, tmp=None, task_vars=None):
        super(Action, self).run(tmp, task_vars)
        validation_result, valid_args = self.validate_argument_spec(self.ARGUMENT_SPEC)
        return valid_args, Context(tmp, task_vars)
