import os
from ansible.errors import AnsibleActionFail, AnsibleError
from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action, failure


class ActionModule(Action):
    ARGUMENT_SPEC = {
        'service_name': {'type': 'str', 'required': True},
        'service_template': {'type': 'str', 'default': 'docker_service.j2'},
        'service_args': {'type': 'str', 'default': ''},
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        service_name = args.get('service_name')
        service_template = args.get('service_template')
        service_args = args.get('service_args')
        if not service_template:
            raise AnsibleActionFail("The 'service_template' parameter cannot be empty.")
        err, systemd_changed = self.provision_systemd_unit(ctx, service_name, service_args, service_template)
        if err:
            return err

        if systemd_changed: 
            err, reload_changed = self.module_step(ctx, {
                'step': 'Reloading daemons',
                'name': 'ansible.builtin.systemd',
                'args': {
                    'daemon_reload': True,
                }
            })
            if err:
                return err
        return {
            'msg': f"Service provisioned: {service_name}",
            'failed': False,
            'changed': systemd_changed or reload_changed,
        }
    def provision_systemd_unit(self, ctx, service_name, service_args, service_template):
        try:
            actual_template_src = self._find_needle('templates', service_template)
        except AnsibleError:
            plugin_dir = os.path.dirname(__file__)
            plugin_templates_dir = os.path.abspath(os.path.join(plugin_dir, '../templates'))
            actual_template_src = os.path.join(plugin_templates_dir, service_template)
            if not os.path.exists(actual_template_src):
                return failure(f"Template '{service_template}' not found in user paths or plugin defaults."), False

        svc_ctx = ctx.with_updated_vars({
            'service_name': service_name,
            'service_args': service_args
        })

        return self.action_step(svc_ctx, {
            'step': f"Configuring systemd unit: {service_name}.service",
            'name': 'ansible.builtin.template',
            'args': {
                'src': actual_template_src,
                'dest': f"/etc/systemd/system/{service_name}.service",
                'owner': 'root',
                'group': 'root',
                'mode': '0644'
            }
        })
