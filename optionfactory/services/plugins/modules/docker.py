from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r'''
---
module: docker
short_description: Installs and configures Docker, users, proxies, and networks.
description:
    - Installs docker-ce package.
    - Configures HTTP or HTTPS proxy for the Docker systemd daemon if provided.
    - Creates the 'docker-machines' user and group.
    - Appends the target users to 'docker' and 'docker-machines' groups.
    - Creates a Docker network with customizable subnet and gateway.
version_added: "1.0.0"
options:
    package:
        description:
            - Use the official 'docker-ce' or 'docker.io'
        type: str
        default: "docker-ce"
        choices:
         - docker-ce
         - docker.io
    users:
        description:
            - A list of usernames to append to the 'docker' and 'docker-machines' groups.
        required: true
        type: list
        elements: str
    proxy:
        description:
            - Dictionary containing HTTP or HTTPS proxy configuration for the Docker daemon.
            - If defined, you must provide exactly one of C(http) or C(https).
        required: false
        type: dict
        suboptions:
            http:
                description: The HTTP proxy URL.
                type: str
            https:
                description: The HTTPS proxy URL.
                type: str
            noproxy:
                description: A comma-separated list of domains that should bypass the proxy.
                type: str
    network:
        description:
            - Dictionary containing Docker network configuration.
        required: false
        type: dict
        suboptions:
            name:
                description: The name of the Docker network.
                required: true
                type: str
            subnet:
                description: The subnet for the network in CIDR format.
                default: "172.18.0.0/24"
                type: str
            gateway:
                description: The gateway IP for the network.
                default: "172.18.0.1"
                type: str
'''

EXAMPLES = r'''
# Basic usage with a single user
- name: Setup Docker defaults
  optionfactory.services.docker:
    users:
      - myadmin

# Providing explicit parameters with multiple users and a proxy
- name: Setup Docker with proxy and network
  optionfactory.services.docker:
    users:
      - myadmin
      - devuser
    proxy:
      http: "http://proxy.example.com:8080"
    network:
      name: myapp_network
      subnet: "192.168.10.0/24"
      gateway: "192.168.10.1"
'''

RETURN = r'''
msg:
    description: A summary message of the operations performed.
    type: str
    returned: always
    sample: "Docker setup completed. Processed 2 user(s). Proxy configured: True. Network 'myapp_network' configured."
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(),
        bypass_checks=True,
        supports_check_mode=True
    )
    module.exit_json(
        changed=False,
        msg="This module executes via its corresponding Action plugin. If you see this, the action plugin was bypassed."
    )


if __name__ == '__main__':
    main()
