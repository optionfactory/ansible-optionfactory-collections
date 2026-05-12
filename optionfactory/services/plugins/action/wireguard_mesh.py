from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action, failure


class ActionModule(Action):

    ARGUMENT_SPEC = dict(
        interface=dict(type='str', required=True, default='wg-mesh'),
        host_ip=dict(type='str', required=True),
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

        config_lines = [
            "[Interface]",
            f"Address = { local.get('tunnel_cidr') }",
            "ListenPort = 51820",
            f"PrivateKey = { local.get('private_key') }",
            f"PostUp = iptables -I FORWARD -i { wg_interface } -j ACCEPT",
            f"PostUp = iptables -I FORWARD -o { wg_interface } -j ACCEPT",
            f"PostUp = iptables -t mangle -A FORWARD -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu",
            f"PostDown = iptables -D FORWARD -i { wg_interface } -j ACCEPT",
            f"PostDown = iptables -D FORWARD -o { wg_interface } -j ACCEPT",
            "PostDown = iptables -t mangle -D FORWARD -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu",
        ]

        for remote_peer in remote_peers:
            remote_peer_tunnel_ip = remote_peer.get('tunnel_cidr').split('/')[0]                
            config_lines.extend([
                "[Peer]",
                f"PublicKey = { remote_peer.get('public_key') }",
                f"Endpoint = { remote_peer.get('host_ip') }:51820",
                f"AllowedIPs = { remote_peer_tunnel_ip }/32, { remote_peer.get('docker_subnet') }",
                "PersistentKeepalive = 25",
                ""
            ])
        config_content = "\n".join(config_lines)

        err, wireguard_config_changed = self.module_step(ctx, {
            'step': f"Ensuring { wg_interface } configuration is up to date",
            'name': 'ansible.builtin.copy',
            'args': {
                'dest': f'/etc/wireguard/{ wg_interface }.conf',
                'content': config_content,
                'mode': '0600'
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
        
        return {
            'msg': "Wireguard mesh setup completed.",
            'failed': False,
            'changed': (
                wireguard_package_changed or
                ip_forward_changed or
                wireguard_dir_changed or
                wireguard_config_changed or
                service_changed
            )
        }
