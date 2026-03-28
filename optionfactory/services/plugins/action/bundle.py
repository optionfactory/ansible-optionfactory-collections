import os
from ansible.errors import AnsibleActionFail, AnsibleError
from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action, failure


class ActionModule(Action):
    ARGUMENT_SPEC = {
        'owner': {'type': 'str', 'default': 'docker-machines'},
        'group': {'type': 'str', 'default': 'docker-machines'},
        'service_name': {'type': 'str', 'required': True},
        'service_template': {'type': 'str', 'default': 'docker_service.j2'},
        'service_args': {'type': 'str', 'default': ''},
        'dirs': {
            'type': 'list',
            'elements': 'dict',
            'default': [],
            'options': {
                'dest': {'type': 'str', 'required': True},
                'owner': {'type': 'str'},
                'group': {'type': 'str'},
                'mode': {'type': 'raw'},
                'when': {'type': 'bool', 'default': True}
            }
        },
        'files': {
            'type': 'list',
            'elements': 'dict',
            'default': [],
            'options': {
                'dest': {'type': 'str', 'required': True},
                'src': {'type': 'str'},
                'content': {'type': 'str'},
                'owner': {'type': 'str'},
                'group': {'type': 'str'},
                'mode': {'type': 'raw'},
                'when': {'type': 'bool', 'default': True}
            },
            'mutually_exclusive': [['src', 'content']],
            'required_one_of': [['src', 'content']]
        },
        'templates': {
            'type': 'list',
            'elements': 'dict',
            'default': [],
            'options': {
                'dest': {'type': 'str', 'required': True},
                'src': {'type': 'str', 'required': True},
                'owner': {'type': 'str'},
                'group': {'type': 'str'},
                'mode': {'type': 'raw'},
                'when': {'type': 'bool', 'default': True}
            }
        }
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        owner = args.get('owner')
        group = args.get('group')
        service_name = args.get('service_name')
        service_template = args.get('service_template')
        service_args = args.get('service_args')
        dirs = args.get('dirs')
        files = args.get('files')
        templates = args.get('templates')
        if not service_template:
            raise AnsibleActionFail("The 'service_template' parameter cannot be empty.")

        err, dir_changed = self.provision_dirs(ctx, dirs, owner, group)
        if err:
            return err
        err, file_changed = self.provision_files(ctx, files, owner, group)
        if err:
            return err
        err, template_changed = self.provision_templates(ctx, templates, owner, group)
        if err:
            return err

        err, systemd_changed = self.provision_systemd_unit(ctx, service_name, service_args, service_template)
        if err:
            return err

        changed = (dir_changed or file_changed or template_changed or systemd_changed)

        err, restart_changed = self.module_step(ctx, { 
            'step': f"Ensuring latest systemd unit is loaded and (re)started: {service_name}",
            'name': 'ansible.builtin.systemd',
            'args': {
                'name': service_name,
                'state': 'restarted' if changed else 'started',
                'daemon_reload': changed,
                'enabled': True
            }
        })
        if err:
            return err
        return {
            'msg': f"Service bundle provisioned: {service_name}",
            'failed': False,
            'changed': changed or restart_changed
        }

    def provision_dirs(self, ctx, dirs, owner, group):
        any_changed = False
        for d in dirs:
            dest = d.get('dest')
            err, changed = self.module_step(ctx, {
                'step': f"Directory provisioning: {dest}",
                'when': d.get('when'),
                'name': 'ansible.builtin.file',
                'args': {
                    'state': 'directory',
                    'dest': d.get('dest'),
                    'owner': d.get('owner', owner),
                    'group': d.get('group', group),
                    'mode': d.get('mode') or '0750'
                }
            })
            if err:
                return err, any_changed
            if changed:
                any_changed = True
        return None, any_changed

    def provision_files(self, ctx, files, owner, group):
        any_changed = False
        for f in files:
            is_inline = bool(f.get('content'))
            args = {
                'dest': f.get('dest'),
                'owner': f.get('owner', owner),
                'group': f.get('group', group),
                'mode': f.get('mode') or '0640'
            }
            if is_inline:
                args['content'] = f.get('content')
            else:
                args['src'] = self._find_needle('files', f.get('src'))

            dest = f.get('dest')
            err, changed = self.action_step(ctx, {
                'step': f"File synchronization: {dest}",
                'when': f.get('when'),
                'name':"ansible.builtin.copy",
                'args': args
            })
            if err:
                return err, any_changed
            if changed:
                any_changed = True
        return None, any_changed

    def provision_templates(self, ctx, templates, owner, group):
        any_changed = False
        for t in templates:
            dest = t.get('dest')
            err, changed = self.action_step(ctx, {
                'step': f"Template synchronization: {dest}",
                'when': t.get('when'),
                'name': "ansible.builtin.template",
                'args': {
                    'src': t.get('src'),
                    'dest': t.get('dest'),
                    'owner': t.get('owner', owner),
                    'group': t.get('group', group),
                    'mode': t.get('mode') or '0640'
                }
            })
            if err:
                return err, any_changed
            if changed:
                any_changed = True
        return None, any_changed

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

