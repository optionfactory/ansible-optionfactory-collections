import os
from ansible.errors import AnsibleActionFail, AnsibleError
from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action, failure, resolve_engine, service_vars


class ActionModule(Action):
    ARGUMENT_SPEC = {
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
                        'source': {'type': 'str', 'required': True},
                        'target': {'type': 'str', 'required': True},
                        'readonly': {'type': 'bool', 'default': False},
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
    }
    VALIDATOR_KWARGS = {
        'mutually_exclusive': [('container', 'command')],
        'required_one_of': [('container', 'command')],
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        name = args.get('name')
        engine, block = resolve_engine(args)
        if not block.get('template'):
            raise AnsibleActionFail("The 'template' parameter cannot be empty.")

        image_changed = False
        if engine == 'container':
            err, image_changed = self.prefetch_image(ctx, block['image'])
            if err:
                return err

        err, systemd_changed = self.provision_systemd_unit(ctx, name, engine, block)
        if err:
            return err

        reload_changed = False
        if image_changed or systemd_changed:
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
            'msg': f"Service provisioned: {name}",
            'failed': False,
            'changed': image_changed or systemd_changed or reload_changed,
        }

    def prefetch_image(self, ctx, image):
        if not image:
            return None, False
        return self.module_step(ctx, {
            'step': f"Prefetching docker image: {image}",
            'name': 'community.docker.docker_image',
            'args': {
                'name': image,
                'source': 'pull',
                'force_source': False
            }
        })

    def provision_systemd_unit(self, ctx, name, engine, block):
        err, actual_template_src = self.find_template(block['template'])
        if err:
            return err
        svc_ctx = ctx.with_updated_vars(service_vars(name, engine, block))

        return self.action_step(svc_ctx, {
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
