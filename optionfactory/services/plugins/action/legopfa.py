import textwrap
from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action


class ActionModule(Action):
    ARGUMENT_SPEC = {
        'container_name': {
            'type': 'str',
            'required': True
        }
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        container_name = args.get('container_name')
        err, service_changed = self.action_step(ctx, {
            'step': "Provisioning legopfa-renewal.service",
            'name': 'ansible.builtin.copy',
            'args':{
                'dest': '/etc/systemd/system/legopfa-renewal.service',
                'owner': 'root',
                'group': 'root',
                'mode': '0644',
                'content': textwrap.dedent(f"""\
                    [Unit]
                    Description=legopfa certificates renewal service
                    
                    [Service]
                    Type=oneshot
                    ExecStart=/usr/bin/docker exec {container_name} /legopfa-all
                """)
            }
        })
        if err:
            return err
        err, timer_changed = self.action_step(ctx, {
            'step': "Provisioning legopfa-renewal.timer",
            'name':'ansible.builtin.copy',
            'args': {
                'dest': '/etc/systemd/system/legopfa-renewal.timer',
                'owner': 'root',
                'group': 'root',
                'mode': '0644',
                'content': textwrap.dedent("""\
                    [Unit]
                    Description=legopfa certificates renewal timer
                    
                    [Timer]
                    OnBootSec=15min
                    OnUnitActiveSec=1w
                    
                    [Install]
                    WantedBy=timers.target
                """)
            }
        })
        if err:
            return err
        err, start_changed = self.module_step(ctx, {
            'step': "Ensuring legopfa-renewal.timer is started",
            'name': 'ansible.builtin.systemd',
            'args': {
                'name': 'legopfa-renewal.timer',
                'state': 'started',
                'enabled': True,
                'daemon_reload': service_changed or timer_changed 
            },
        })
        if err:
            return err            
        return {
            'msg': "Legopfa configuration provisioned.",
            'failed': False,
            'changed': service_changed or timer_changed or start_changed
        }