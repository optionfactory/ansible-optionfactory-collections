from ansible.module_utils.basic import AnsibleModule
DOCUMENTATION = r'''
---
module: service
short_description: Deploy a service.
description:
    - This is an action plugin that configures a systemd service.
    - Exactly one engine block (I(container) or I(command)) must be provided.
options:
    name:
        type: str
        required: true
        description: "The name of the systemd service."
    container:
        type: dict
        description: "Runs a containerized service (docker by default, podman optional). Mutually exclusive with 'command'."
        suboptions:
            engine:
                type: str
                required: false
                default: docker
                choices: [docker, podman]
                description: "The container engine to use."
            image:
                type: str
                required: true
                description: "The container image. Prefetched and injected into the template context."
            opts:
                type: str
                required: false
                default: ''
                description: "Extra engine run options, appended after the structured ones (env, publish, mounts, volumes, network, ip). An empty value is ignored."
            args:
                type: str
                required: false
                default: ''
                description: "Container command arguments injected into the template context."
            network:
                type: str
                required: false
                description: "Container network name. Rendered as '--network <network>'. An empty value is ignored."
            ip:
                type: str
                required: false
                description: "Static container IP. Rendered as '--ip <ip>'. An empty value is ignored."
            env:
                type: dict
                required: false
                default: {}
                description: "Environment variables as a KEY: value mapping. Rendered as '--env KEY=value'."
            publish:
                type: list
                elements: str
                required: false
                default: []
                description: "Ports to publish, in docker/podman syntax (e.g. '0.0.0.0:80:80'). Rendered as '-p <port>'. Empty entries are ignored, so Jinja conditionals yielding '' can be used."
            mounts:
                type: list
                elements: dict
                required: false
                default: []
                description: "Bind mounts. Rendered as '--mount type=bind,...'."
                suboptions:
                    source:
                        type: str
                        required: true
                        description: "Path on the host."
                    target:
                        type: str
                        required: true
                        description: "Path inside the container."
                    readonly:
                        type: bool
                        required: false
                        default: false
                        description: "Mount the bind read-only."
                    when:
                        type: bool
                        required: false
                        default: true
                        description: "If this mount should be rendered."
            volumes:
                type: list
                elements: str
                required: false
                default: []
                description: "Volumes in docker/podman syntax (e.g. 'mydata:/data'). Rendered as '--volume <volume>'. Empty entries are ignored. Bind mounts are better expressed via 'mounts'."
            template:
                type: str
                required: false
                description: "Jinja2 template for the systemd .service file. Defaults to '<engine>_service.j2'."
    command:
        type: dict
        description: "Runs a plain (non-container) command as a service, after the network is online. Mutually exclusive with 'container'."
        suboptions:
            exec:
                type: str
                required: true
                description: "The executable to run. Injected into the template context."
            args:
                type: str
                required: false
                default: ''
                description: "Command arguments injected into the template context."
            template:
                type: str
                required: false
                default: "command_service.j2"
                description: "Jinja2 template for the systemd .service file (searches in Ansible paths or plugin defaults)."
'''

EXAMPLES = r'''
- name: Deploy nginx service
  optionfactory.services.service:
    name: nginx-myapp
    container:
      image: "optionfactory/debian13-nginx130:999"
      network: myapp
      ip: 172.18.0.14
      publish:
        - "0.0.0.0:8888:8888"
        - "{{ '0.0.0.0:443:443' if env != 'productiondb' else '' }}"
      mounts:
        - source: /opt/myapp/nginx/nginx.conf
          target: /etc/nginx/nginx.conf
          readonly: true

- name: Deploy a podman-backed service
  optionfactory.services.service:
    name: my-app
    container:
      engine: podman
      image: "registry.example.com/my-app:2"
      volumes:
        - "mydata:/var/lib/myapp"

- name: Deploy a command-based agent service
  optionfactory.services.service:
    name: my-agent
    command:
      exec: /usr/bin/my-agent
      args: "--config /etc/my-agent.conf"
'''

RETURN = r'''
msg:
    description: A summary of the service deployment.
    type: str
    returned: always
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
