import os
from ansible.errors import AnsibleActionFail, AnsibleError
from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action, failure


class ActionModule(Action):
    ARGUMENT_SPEC = {
        'name': {'type': 'str', 'required': True},
        'image': {'type': 'str', 'required': True},
        'opts': {'type': 'str', 'default': ''},
        'args': {'type': 'str', 'default': ''},
        'template': {'type': 'str', 'default': 'docker_service.j2'},
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        name = args.get('name')
        image = args.get('image')
        opts = args.get('opts')
        sargs = args.get('args')
        template = args.get('template')
        if not template:
            raise AnsibleActionFail("The 'template' parameter cannot be empty.")

        err, image_changed = self.prefetch_image(ctx, image)
        if err: 
             return err
        
        err, systemd_changed = self.provision_systemd_unit(ctx, name, image, opts, sargs, template)
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
    def prefetch_image(self, ctx, service_image):
        if not service_image:
            return None, False
        return self.module_step(ctx, {
            'step': f"Prefetching docker image: {service_image}",
            'name': 'community.docker.docker_image',
            'args': {
                'name': service_image,
                'source': 'pull',
                'force_source': False                
            }
        })
    
    def provision_systemd_unit(self, ctx, name, image, opts, args, service_template):
        err, actual_template_src = self.find_template(service_template)
        if err:
            return err
        svc_ctx = ctx.with_updated_vars({
            'name': name,
            'opts': opts,
            'image': image,
            'args': args,
        })

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
