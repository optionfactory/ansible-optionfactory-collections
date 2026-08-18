from ansible.module_utils.basic import AnsibleModule
DOCUMENTATION = r'''
---
module: service
short_description: Deploy a service.
description:
    - This is an action plugin that configures a systemd service.
options:
    name:
        type: str
        required: true
        description: "The name of the systemd service."
    image:
        type: str
        required: true
        description: "The docker image to be prefetched. Also injected into the template context."
    opts:
        type: str
        required: false
        default: ''
        description: "Docker options passed to the systemd service template."
    args:
        type: str
        required: false
        default: ''
        description: "Arguments passed to the systemd service template."
    template:
        type: str
        required: false
        default: "docker_service.j2"
        description: "Path to the Jinja2 template for the systemd .service file."
'''

EXAMPLES = r'''
- name: Deploy keycloak service
  optionfactory.services.service:
    name: keycloak-myapp
    image: optionfactory/debian13-jdk21-keycloak2:999
    opts: >
        --network myapp
        --ip 172.18.0.14
        --mount type=bind,source=/opt/myapp/keycloak/deployments/keycloak-myapp-custom.jar,target=/opt/keycloak/providers/keycloak-myapp-custom.jar
        --mount type=bind,source=/opt/myapp/keycloak/conf/keycloak.conf,target=/opt/keycloak/conf/keycloak.conf
'''

RETURN = r'''
msg:
    description: A summary of the bundle deployment.
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
