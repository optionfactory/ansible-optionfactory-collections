
from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action


class ActionModule(Action):
    ARGUMENT_SPEC = {
        'persistent': {
            'type': 'bool',
            'default': True
        },
        'configuration': {
            'type': 'str',
        }
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        err, pers_changed = self.ensure_persistent(ctx, args.get('persistent'))
        if err:
            return err
        err, conf_changed = self.provision_config(ctx, args.get('configuration'))
        if err:
            return err
        err, start_changed = self.module_step(ctx, {
            'step': 'Ensuring journald is started/restarted',
            'name': 'ansible.builtin.systemd',
            'args': {
                'name': 'systemd-journald.service',
                'state': 'restarted' if pers_changed or conf_changed else 'started'
            }
        })
        if err:
            return err
        return {
            'msg': "Journald configuration provisioned.",
            'failed': False,
            'changed': pers_changed or conf_changed or start_changed
        }

    def ensure_persistent(self, ctx, persistent):
        if not persistent:
            return None, False
        return self.module_step(ctx, {
            'step': "Ensuring journal is persistent",
            'name': 'ansible.builtin.file',
            'args': {
                'path': '/var/log/journal',
                'state': 'directory',
                'owner': 'root',
                'mode': '0755'
            }
        })

    def provision_config(self, ctx, configuration):
        if not configuration:
            return None, False
        return self.action_step(ctx, {
            'step': "Provisioning journald configuration",
            'name': 'ansible.builtin.copy',
            'args': {
                'dest': '/etc/systemd/journald.conf',
                'owner': 'root',
                'mode': '0644',
                'content': configuration
            }
        })
