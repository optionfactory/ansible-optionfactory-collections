from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action, failure


class ActionModule(Action):

    ARGUMENT_SPEC = dict(
        host_ip=dict(type='str', required=True),
        interface=dict(type='str', required=False, default='wg-mesh'),
        config_template=dict(type='str', required=False, default='wireguard_mesh_config.j2'),
        peers=dict(
            type='list',
            required=True,
            elements='dict',
            options=dict(
                host_ip=dict(type='str', required=True),
                tunnel_cidr=dict(type='str', required=True),
                docker_subnet=dict(type='str', required=True),
                private_key=dict(type='str', required=True, no_log=True),
                public_key=dict(type='str', required=True),
            )
        )
    )

    def partition_peers(self, host_ip, peers):
        local = None
        remote_peers = []
        for peer in peers:
            if peer.get('host_ip') == host_ip:
                local = peer
            else:
                remote_peers.append(peer)
        if not local:
            return failure("host_ip has no match in peers"), None, []
        if not remote_peers:
            return failure("there are no configured remote peers"), None, []
        return None, local, remote_peers

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)

        wg_interface = args.get('interface')

        err, local, remote_peers = self.partition_peers(args.get('host_ip'), args.get('peers') or []) 
        if err:
            return err

        err, wireguard_package_changed = self.action_step(ctx, {
            'step': f"Ensuring wireguard is installed",
            'name': 'ansible.builtin.package',
            'args': {
                'name': 'wireguard',
                'state': 'present'
            }
        })
        if err:
            return err

        err, ip_forward_changed = self.module_step(ctx, {
            'step': "Ensuring net.ipv4.ip_forward is enabled",
            'name': 'ansible.posix.sysctl',
            'args': {
                'name': 'net.ipv4.ip_forward',
                'value': '1',
                'sysctl_set': True,
                'state': 'present',
                'reload': True                
            }
        })
        if err: 
            return err

        err, wireguard_dir_changed = self.module_step(ctx, {
            'step': "Ensuring /etc/wireguard directory is present",
            'name': 'ansible.builtin.file',
            'args': {
                'path': '/etc/wireguard',
                'state': 'directory',
                'mode': '0700'
            }
        })
        if err: 
            return err

        err, config_template = self.find_template(args.get('config_template'))
        if err:
            return err
        svc_ctx = ctx.with_updated_vars({
            'wg_interface': wg_interface,
            'local': local,
            'remote_peers': remote_peers,
        })
        err, wireguard_config_changed = self.action_step(svc_ctx, {
            'step': f"Ensuring { wg_interface } configuration is up to date",
            'name': 'ansible.builtin.template',
            'args': {
                'src': config_template,
                'dest': f'/etc/wireguard/{ wg_interface }.conf',
                'owner': 'root',
                'group': 'root',
                'mode': '0600'
            }
        })
        if err:
            return err
        
        err, docker_override_dir_changed = self.module_step(ctx, {
            'step': "Ensuring Docker systemd override directory exists",
            'name': 'ansible.builtin.file',
            'args': {
                'path': '/etc/systemd/system/docker.service.d',
                'state': 'directory',
                'owner': 'root',
                'group': 'root',
                'mode': '0755'
            }
        })
        if err: 
            return err
        
        err, docker_override_changed = self.module_step(ctx, {
            'step': "Ensuring Docker waits for WireGuard interface",
            'name': 'ansible.builtin.copy',
            'args': {
                'content': "\n".join([
                    "[Unit]",
                    f"After=wg-quick@{ wg_interface }.service",
                    f"Wants=wg-quick@{ wg_interface }.service"
                ]),
                'dest': f'/etc/systemd/system/docker.service.d/wireguard-{ wg_interface }.conf',
                'owner': 'root',
                'group': 'root',
                'mode': '0644',
            }
        })
        if err: 
            return err

        if docker_override_changed:
            err, _ = self.module_step(ctx, {
                'step': "Reloading systemd daemon to apply Docker dependency",
                'name': 'ansible.builtin.systemd',
                'args': {
                    'daemon_reload': True
                }
            })
            if err: 
                return err
            
        err, service_changed = self.module_step(ctx, {
            'step': 'Ensuring service is started and updated',
            'name': 'ansible.builtin.systemd',
            'args': {
                'name': f'wg-quick@{ wg_interface }',
                'enabled': True,
                'state': 'restarted' if wireguard_config_changed else 'started'
            }
        })
        if err:
            return err        
        return {
            'msg': "Wireguard mesh setup completed.",
            'failed': False,
            'changed': (
                wireguard_package_changed or
                ip_forward_changed or
                wireguard_dir_changed or
                wireguard_config_changed or
                docker_override_dir_changed or
                docker_override_changed or
                service_changed
            )
        }
