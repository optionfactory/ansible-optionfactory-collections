import os
from ansible.errors import AnsibleActionFail
from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action, resolve_engine


class ActionModule(Action):
    ARGUMENT_SPEC = {
        'name': {'type': 'str', 'required': True},
        'container': {
            'type': 'dict',
            'options': {
                'engine': {'type': 'str', 'default': 'docker', 'choices': ['docker', 'podman']},
                'container': {'type': 'str', 'required': True},
                'exec': {'type': 'str', 'required': True},
                'args': {'type': 'str', 'default': ''},
                'opts': {'type': 'str', 'default': ''},
                'template': {'type': 'str'},
            },
        },
        'command': {
            'type': 'dict',
            'options': {
                'exec': {'type': 'str', 'required': True},
                'args': {'type': 'str', 'default': ''},
                'template': {'type': 'str', 'default': 'command_oneshot_service.j2'},
            },
        },
        'on_boot_sec': {'type': 'str'},
        'on_unit_active_sec': {'type': 'str'},
        'on_calendar': {'type': 'str'},
        'persistent': {'type': 'bool', 'default': False},
        'accuracy_sec': {'type': 'str'},
        'randomized_delay_sec': {'type': 'str'},
        'unit': {'type': 'str'},
        'timer_template': {'type': 'str', 'default': 'timer.j2'},
    }
    VALIDATOR_KWARGS = {
        'mutually_exclusive': [('container', 'command')],
        'required_one_of': [('container', 'command'), ('on_calendar', 'on_boot_sec', 'on_unit_active_sec')],
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        name = args.get('name')
        engine, block = resolve_engine(args, 'oneshot_service')
        if not block.get('template'):
            raise AnsibleActionFail("The 'template' parameter cannot be empty.")

        err, service_changed = self.provision_systemd_unit(ctx, name, engine, block)
        if err:
            return err
        err, timer_changed = self.provision_timer_unit(ctx, name, args)
        if err:
            return err
        err, start_changed = self.step(ctx, {
            'step': f"Ensuring {name}.timer is started and enabled",
            'name': 'ansible.builtin.systemd',
            'args': {
                'name': f"{name}.timer",
                'state': 'started',
                'enabled': True,
                'daemon_reload': service_changed or timer_changed
            }
        })
        if err:
            return err
        return {
            'msg': f"Timer provisioned: {name}",
            'failed': False,
            'changed': service_changed or timer_changed or start_changed
        }

    def provision_systemd_unit(self, ctx, name, engine, block):
        err, actual_template_src = self.find_template(block['template'])
        if err:
            return err
        svc_ctx = ctx.with_updated_vars({'name': name, **block})

        return self.step(svc_ctx, {
            'step': f"Configuring systemd unit: {name}.service",
            'name': 'ansible.builtin.template',
            'args': {
                'src': actual_template_src,
                'dest': f"/etc/systemd/system/{name}.service",
                'owner': 'root',
                'group': 'root',
                'mode': '0644'
            }
        })

    def provision_timer_unit(self, ctx, name, args):
        err, actual_template_src = self.find_template(args.get('timer_template'))
        if err:
            return err
        timer_ctx = ctx.with_updated_vars({
            'name': name,
            'on_boot_sec': args.get('on_boot_sec'),
            'on_unit_active_sec': args.get('on_unit_active_sec'),
            'on_calendar': args.get('on_calendar'),
            'persistent': args.get('persistent'),
            'accuracy_sec': args.get('accuracy_sec'),
            'randomized_delay_sec': args.get('randomized_delay_sec'),
            'unit': args.get('unit'),
        })

        return self.step(timer_ctx, {
            'step': f"Configuring systemd unit: {name}.timer",
            'name': 'ansible.builtin.template',
            'args': {
                'src': actual_template_src,
                'dest': f"/etc/systemd/system/{name}.timer",
                'owner': 'root',
                'group': 'root',
                'mode': '0644'
            }
        })
