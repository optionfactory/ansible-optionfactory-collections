from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action, failure, log_step


class ActionModule(Action):
    ARGUMENT_SPEC = {
        'host_ip': {'type': 'str', 'required': True},
        'interface': {'type': 'str', 'default': 'wg-mesh'},
        "docker_mesh_mtu": {'type': 'int'},
        'config_template': {'type': 'str', 'default': 'wireguard_mesh_config.j2'},
        'peers': {
            'type': 'list',
            'required': True,
            'elements': 'dict',
            'options': {
                'host_ip': {'type': 'str', 'required': True},
                'wg_tunnel_cidr': {'type': 'str', 'required': True},
                'docker_mesh_subnet': {'type': 'str', 'required': True},
                'private_key': {'type': 'str', 'required': True, 'no_log': True},
                'public_key': {'type': 'str', 'required': True},
            }
        }
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        wg_interface = args.get('interface')
        config_template = args.get('config_template')
        err, local, remote_peers = self.partition_peers(args.get('host_ip'), args.get('peers') or [])
        if err:
            return err
        err, wireguard_package_changed = self.install_packages(ctx)
        if err:
            return err
        err, ip_forward_changed = self.enable_ip_forward(ctx)
        if err:
            return err
        err, wireguard_config_changed = self.configure_wireguard(ctx, wg_interface, local, remote_peers, config_template)
        if err:
            return err
        err, docker_network_changed = self.configure_docker_network(ctx, wg_interface, local, args.get('docker_mesh_mtu'))
        if err:
            return err
        
        err, docker_overrides_changed = self.configure_docker(ctx, wg_interface)
        if err:
            return err
        return {
            'msg': "Wireguard mesh setup completed.",
            'failed': False,
            'changed': (wireguard_package_changed or ip_forward_changed or wireguard_config_changed or docker_network_changed or docker_overrides_changed)
        }

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

    def install_packages(self, ctx):
        wireguard_changed = False
        os_family = ctx.task_vars.get('ansible_facts', {}).get('os_family', 'unknown')
        if os_family == 'Debian':
            err, wireguard_changed = self.action_step(ctx, {
                'step': f"Ensuring wireguard is installed",
                'name': 'ansible.builtin.package',
                'args': {
                    'name': ['wireguard'],
                    'state': 'present'
                }
            })
            if err: return err, False
        err, wireguard_tools_changed = self.action_step(ctx, {
            'step': f"Ensuring wireguard and iptables are installed",
            'name': 'ansible.builtin.package',
            'args': {
                'name': ['wireguard-tools', 'iptables'],
                'state': 'present'
            }
        })
        return err, wireguard_changed or wireguard_tools_changed

    def enable_ip_forward(self, ctx):
        return self.module_step(ctx, {
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

    def configure_wireguard(self, ctx, wg_interface, local, remote_peers, config_template):
        err, directory_changed = self.module_step(ctx, {
            'step': "Ensuring /etc/wireguard directory is present",
            'name': 'ansible.builtin.file',
            'args': {
                'path': '/etc/wireguard',
                'state': 'directory',
                'mode': '0700'
            }
        })
        if err:
            return err, False
        err, config_template = self.find_template(config_template)
        if err:
            return err, False
        svc_ctx = ctx.with_updated_vars({
            'wg_interface': wg_interface,
            'local': local,
            'remote_peers': remote_peers,
        })
        err, config_changed = self.action_step(svc_ctx, {
            'step': f"Ensuring {wg_interface} configuration is up to date",
            'name': 'ansible.builtin.template',
            'args': {
                'src': config_template,
                'dest': f'/etc/wireguard/{wg_interface}.conf',
                'owner': 'root',
                'group': 'root',
                'mode': '0600'
            }
        })
        if err:
            return err, False
        err, service_changed = self.module_step(ctx, {
            'step': 'Ensuring service is started and updated',
            'name': 'ansible.builtin.systemd',
            'args': {
                'name': f'wg-quick@{wg_interface}',
                'enabled': True,
                'state': 'restarted' if config_changed else 'started'
            }
        })
        if err:
            return err, False
        return err, directory_changed or config_changed or service_changed
    
    def configure_docker_network(self, ctx, wg_interface, local, maybe_mtu):
        docker_interface = f"{wg_interface}-docker"

        driver_options = {
            "com.docker.network.bridge.trusted_host_interfaces": wg_interface,
            "com.docker.network.bridge.name": docker_interface,
            "com.docker.network.bridge.enable_ip_masquerade": "false"
        }
        if maybe_mtu:
            driver_options["com.docker.network.driver.mtu"] = str(maybe_mtu)        

        return self.module_step(ctx, {
            'step': f'Ensuring docker mesh network {docker_interface} is present',
            'name': 'community.docker.docker_network',
            'args': {
                'name': docker_interface,
                'driver_options': driver_options,
                'ipam_config': [{
                    'subnet': local.get('docker_mesh_subnet'),
                }]
            }
        })


    def configure_docker(self, ctx, wg_interface):
        err, directory_changed = self.module_step(ctx, {
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
            return err, False
        err, overrides_changed = self.action_step(ctx, {
            'step': "Ensuring Docker waits for WireGuard interface",
            'name': 'ansible.builtin.copy',
            'args': {
                'content': "\n".join([
                    "[Unit]",
                    f"After=wg-quick@{wg_interface}.service",
                    f"Wants=wg-quick@{wg_interface}.service"
                ]),
                'dest': f'/etc/systemd/system/docker.service.d/wireguard-{wg_interface}.conf',
                'owner': 'root',
                'group': 'root',
                'mode': '0644',
            }
        })
        if err:
            return err, False
        if overrides_changed:
            err, _ = self.module_step(ctx, {
                'step': "Reloading systemd daemon to apply Docker dependency",
                'name': 'ansible.builtin.systemd',
                'args': {
                    'daemon_reload': True
                }
            })
            if err:
                return err, False
        return None, directory_changed or overrides_changed
