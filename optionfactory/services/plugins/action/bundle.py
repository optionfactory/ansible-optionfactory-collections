import os
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.errors import AnsibleActionFail, AnsibleError
from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action, failure, resolve_engine, service_vars


class ActionModule(Action):
    ARGUMENT_SPEC = {
        'owner': {'type': 'str', 'default': 'docker-machines'},
        'group': {'type': 'str', 'default': 'docker-machines'},
        'name': {'type': 'str', 'required': True},
        'container': {
            'type': 'dict',
            'options': {
                'engine': {'type': 'str', 'default': 'docker', 'choices': ['docker', 'podman']},
                'image': {'type': 'str', 'required': True},
                'opts': {'type': 'str', 'default': ''},
                'args': {'type': 'str', 'default': ''},
                'network': {'type': 'str'},
                'ip': {'type': 'str'},
                'env': {'type': 'dict', 'default': {}},
                'publish': {'type': 'list', 'elements': 'str', 'default': []},
                'mounts': {
                    'type': 'list',
                    'elements': 'dict',
                    'default': [],
                    'options': {
                        'type': {'type': 'str', 'default': 'bind'},
                        'source': {'type': 'str', 'required': True},
                        'target': {'type': 'str'},
                        'readonly': {'type': 'bool', 'default': True},
                        'opts': {'type': 'str', 'default': ''},
                        'when': {'type': 'bool', 'default': True}
                    }
                },
                'volumes': {'type': 'list', 'elements': 'str', 'default': []},
                'template': {'type': 'str'},
            },
        },
        'command': {
            'type': 'dict',
            'options': {
                'exec': {'type': 'str', 'required': True},
                'args': {'type': 'str', 'default': ''},
                'template': {'type': 'str', 'default': 'command_service.j2'},
            },
        },
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
                'remote_src': {'type': 'bool'},
                'owner': {'type': 'str'},
                'group': {'type': 'str'},
                'mode': {'type': 'raw'},
                'when': {'type': 'bool', 'default': True}
            },
            'required_if': [['remote_src', True, ['src']]],
            'mutually_exclusive': [['src', 'content'], ['remote_src', 'content']],
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
    VALIDATOR_KWARGS = {
        'mutually_exclusive': [('container', 'command')],
        'required_one_of': [('container', 'command')],
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        owner = args.get('owner')
        group = args.get('group')

        name = args.get('name')
        engine, block = resolve_engine(args)
        if not block.get('template'):
            raise AnsibleActionFail("The 'template' parameter cannot be empty.")

        dirs = args.get('dirs')
        files = args.get('files')
        templates = args.get('templates')

        image_changed = False
        if engine == 'container':
            err, image_changed = self.prefetch_image(ctx, block['image'])
            if err:
                return err
        err, dir_changed = self.provision_dirs(ctx, dirs, owner, group)
        if err:
            return err

        err, file_changed = self.provision_files(ctx, files, owner, group)
        if err:
            return err

        err, template_changed = self.provision_templates(ctx, templates, owner, group)
        if err:
            return err

        err, systemd_changed = self.provision_systemd_unit(ctx, name, engine, block)
        if err:
            return err
        changed = (image_changed or dir_changed or file_changed or template_changed or systemd_changed)
        err, restart_changed = self.step(ctx, {
             'step': f"Ensuring latest systemd unit is loaded and (re)started: {name}",
            'name': 'ansible.builtin.systemd',
            'args': {
                'name': name,
                'state': 'restarted' if changed else 'started',
                'daemon_reload': changed,
                'enabled': True
            }
        })
        if err:
            return err
        return {
            'msg': f"Service bundle provisioned: {name}",
            'failed': False,
            'changed': changed or restart_changed
        }

    def prefetch_image(self, ctx, image):
        if not image:
            return None, False
        return self.step(ctx, {
            'step': f"Prefetching docker image: {image}",
            'name': 'community.docker.docker_image',
            'args': {
                'name': image,
                'source': 'pull',
                'force_source': False
            }
        })

    def provision_dirs(self, ctx, dirs, owner, group):
        any_changed = False
        for d in dirs:
            if not boolean(d.get('when')):
                continue
            dest = d.get('dest')
            err, changed = self.step(ctx, {
                'step': f"Directory provisioning: {dest}",
                'name': 'ansible.builtin.file',
                'args': {
                    'state': 'directory',
                    'dest': d.get('dest'),
                    'owner': d.get('owner') or owner,
                    'group': d.get('group') or group,
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
            if not boolean(f.get('when')):
                continue
            is_inline = bool(f.get('content'))
            args = {
                'dest': f.get('dest'),
                'owner': f.get('owner') or owner,
                'group': f.get('group') or group,
                'mode': f.get('mode') or '0640'
            }
            if is_inline:
                args['content'] = f.get('content')
            else:
                remote_src = f.get('remote_src') == True
                args['src'] = f.get('src') if remote_src else self._find_needle('files', f.get('src'))
                args['remote_src'] = remote_src

            dest = f.get('dest')
            err, changed = self.step(ctx, {
                'step': f"File synchronization: {dest}",
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
            if not boolean(t.get('when')):
                continue
            dest = t.get('dest')
            err, changed = self.step(ctx, {
                'step': f"Template synchronization: {dest}",
                'name': "ansible.builtin.template",
                'args': {
                    'src': t.get('src'),
                    'dest': t.get('dest'),
                    'owner': t.get('owner') or owner,
                    'group': t.get('group') or group,
                    'mode': t.get('mode') or '0640'
                }
            })
            if err:
                return err, any_changed
            if changed:
                any_changed = True
        return None, any_changed

    def provision_systemd_unit(self, ctx, name, engine, block):
        err, actual_template_src = self.find_template(block['template'])
        if err:
            return err
        svc_ctx = ctx.with_updated_vars(service_vars(name, engine, block))

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

