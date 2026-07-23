import os
from ansible.errors import AnsibleActionFail, AnsibleError
from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action, failure


class ActionModule(Action):
    ARGUMENT_SPEC = {
        'service_name': {'type': 'str', 'required': True},
        'service_image': {'type': 'str'},
        'service_template': {'type': 'str', 'default': 'docker_service.j2'},
        'service_args': {'type': 'str', 'default': ''},
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        service_name = args.get('service_name')
        service_image = args.get('service_image')
        service_template = args.get('service_template')
        service_args = args.get('service_args')
        if not service_template:
            raise AnsibleActionFail("The 'service_template' parameter cannot be empty.")

        err, image_changed = self.prefetch_image(ctx, service_image)
        if err: 
             return err
        
        err, systemd_changed = self.provision_systemd_unit(ctx, service_name, service_args, service_template, service_image)
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
            'msg': f"Service provisioned: {service_name}",
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
    
    def provision_systemd_unit(self, ctx, service_name, service_args, service_template, service_image):
        err, actual_template_src = self.find_template(service_template)
        if err:
            return err
        svc_ctx = ctx.with_updated_vars({
            'service_name': service_name,
            'service_args': service_args,
            'service_image': service_image,
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
