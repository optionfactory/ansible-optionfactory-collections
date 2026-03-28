from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action


class ActionModule(Action):

    ARGUMENT_SPEC = {
        'package': {
            'type':  'str',
            'default': 'docker-ce',
            'choices': ['docker-ce', 'docker.io']
        },
        'users': {
            'type': 'list',
            'elements': 'str',
            'default': []
        },
        'proxy': {
            'type': 'dict',
            'options': {
                'http': {'type': 'str'},
                'https': {'type': 'str'},
                'noproxy': {'type': 'str'}
            },
            'required_one_of': [['http', 'https', 'noproxy']],
        },
        'network': {
            'type': 'dict',
            'options': {
                'name': {'type': 'str', 'required': True},
                'subnet': {'type': 'str', 'default': '172.18.0.0/24'},
                'gateway': {'type': 'str', 'default': '172.18.0.1'}
            }
        }
    }

    def run(self, tmp=None, task_vars=None):
        args, ctx = super(ActionModule, self).run(tmp, task_vars)
        err, install_changed = self.configure_package(ctx, args.get('package'))
        if err: 
            return err
        err, proxy_changed = self.configure_proxies(ctx, args.get('proxy') or {})
        if err:
            return err
        err, ug_changed = self.configure_user_and_group(ctx)
        if err:
            return err
        err, users_changed = self.configure_users(ctx, args.get('users'))
        if err:
            return err
        err, network_changed = self.ensure_docker_running(ctx)
        if err:
            return err
        err, network_changed = self.provision_network(ctx, args.get('network') or {})
        if err:
            return err
        return {
            'msg': "Docker setup completed.",
            'failed': False,
            'changed': (
                install_changed or
                proxy_changed or
                ug_changed or
                users_changed or
                network_changed
            )
        }
    def configure_package(self, ctx, package):
        return self.action_step(ctx, {
            'step': f"Ensuring docker package '{package}' is installed",
            'name': 'ansible.builtin.package',
            'args': {
                'name': package,
                'state': 'present'
            }
        })

    def configure_proxies(self, ctx, proxy_config):
        http_proxy = proxy_config.get('http')
        https_proxy = proxy_config.get('https')
        no_proxy = proxy_config.get('noproxy')
        if not http_proxy and not https_proxy and not no_proxy:
            return None, False
        err, proxy_dir_changed = self.module_step(ctx, {
            'step': 'Provisioning docker.service.d directory',
            'name': 'ansible.builtin.file',
            'args': {
                'state': 'directory',
                'path': '/etc/systemd/system/docker.service.d',
                'owner': 'root',
                'mode': '0755'
            }
        })
        if err:
            return err, False

        proxies = {
            "HTTP_PROXY": http_proxy,
            "HTTPS_PROXY": https_proxy,
            "NO_PROXY": no_proxy
        }
        env_lines = [f'Environment="{k}={v}"' for k, v in proxies.items() if v]
        err, proxy_file_changed = self.module_step(ctx, {
            'step': 'Provisioning http-proxy.conf',
            'name': 'ansible.builtin.copy',
            'args': {
                'dest': '/etc/systemd/system/docker.service.d/http-proxy.conf',
                'owner': 'root',
                'mode': '0644',
                'content': "[Service]\n" + "\n".join(env_lines)
            }
        })
        if err:
            return err, proxy_dir_changed
        err, service_changed = self.module_step(ctx, {
            'step': 'Ensuring docker.service is loaded and started',
            'name':'ansible.builtin.systemd',
            'args':{
                'name': 'docker.service',
                'daemon_reload': True,
                'state': 'restarted'
            }
        })
        if err:
            return err, proxy_dir_changed or proxy_file_changed
        return None, proxy_dir_changed or proxy_file_changed or service_changed

    def ensure_docker_running(self, ctx):
        return self.module_step(ctx, {
            'step': f"Ensuring docker is started",
            'name': 'ansible.builtin.systemd',
            'args': {
                'name': 'docker.service',
                'state': 'started',
                'enabled': True
            }
        })

    def provision_network(self, ctx, network_config):
        network_name = network_config.get('name')
        network_subnet = network_config.get('subnet')
        network_gateway = network_config.get('gateway')
        if not network_name:
            return None, False
        
        return self.module_step(ctx, {
            'step': f"Provisioning network: {network_name}. Subnet: {network_subnet}, Gateway: {network_gateway}",
            'name': 'community.docker.docker_network',
            'args': {
                'name': network_name,
                'driver_options': {
                    'com.docker.network.bridge.name': network_name
                },
                'ipam_config': [
                    {
                        'subnet': network_subnet,
                        'gateway': network_gateway
                    }
                ]
            }
        })

    def configure_user_and_group(self, ctx):
        err, group_changed = self.module_step(ctx, {
            'step': f"Provisioning group docker-machines",
            'name': 'ansible.builtin.group',
            'args': {
                'state': 'present',
                'name': 'docker-machines',
                'gid': 950
            }
        })
        if err:
            return err, False        
        err, user_changed = self.module_step(ctx, {
            'step': f"Provisioning user docker-machines",
            'name': 'ansible.builtin.user',
            'args': {
                'state': 'present',
                'name': 'docker-machines',
                'system': True,
                'create_home': False,
                'home': '/',
                'shell': '/usr/sbin/nologin',
                'uid': 950,
                'group': 'docker-machines'
            }
        })
        if err:
            return err, False
        return None, group_changed or user_changed

    def configure_users(self, ctx, users):
        any_changed = False
        for u in users:
            err, changed = self.module_step(ctx, {
                'step': f"Adding user to group docker-machines: {u}",
                'name': 'ansible.builtin.user',
                'args': {
                    'name': u,
                    'groups': 'docker,docker-machines',
                    'append': True
                }
            })
            if err:
                return err, False
            if changed:
                any_changed = True
        return None, any_changed
