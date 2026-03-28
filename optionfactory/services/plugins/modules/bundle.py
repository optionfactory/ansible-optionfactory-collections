from ansible.module_utils.basic import AnsibleModule
DOCUMENTATION = r'''
---
module: bundle
short_description: Deploy a service and its files in one step.
description:
    - This is an action plugin that ensures directories exist, syncs files/templates, 
      and restarts the systemd service if anything changed.
options:
    service_name:
        type: str
        required: true
        description: "The name of the systemd service."
    service_template:
        type: str
        required: false
        default: "docker_service.j2"
        description: "Path to the Jinja2 template for the systemd .service file."
    service_args:
        type: str
        required: false
        description: "Arguments passed to the systemd service template."
    owner: 
        type: str
        required: false
        default: "docker-machines"
        description: "Default owner for all managed directories, files, and templates."        
    group: 
        type: str
        required: false
        default: "docker-machines"
        description: "Default group for all managed directories, files, and templates."        
    dirs:
        type: list
        elements: dict
        required: false
        description: "List of directories to provision."
        suboptions:
            dest:
                type: str
                required: true
                description: "Path to the directory to be created."
            mode:
                type: str
                default: "0750"
                description: "Permissions for the directory."
            owner:
                type: str
                description: "Owner for this specific directory. Overrides the default owner."
            group:
                type: str
                description: "Group for this specific directory. Overrides the default group."
            when:
                type: bool
                descriptiom: "If this rule should be applied."
                default: True
    files:
        type: list
        elements: dict
        required: false
        description: "List of files to sync."
        suboptions:
            src:
                type: str
                description: "Local path to the source file. Mutually exclusive with 'content'."
            content:
                type: str
                description: "Inline string content. Mutually exclusive with 'src'."
            dest:
                type: str
                required: true
                description: "Remote destination path."
            mode:
                type: str
                default: "0640"
                description: "Permissions for the file."
            owner:
                type: str
                description: "Owner for this specific file. Overrides the default owner."
            group:
                type: str
                description: "Group for this specific file. Overrides the default group."
            when:
                type: bool
                descriptiom: "If this rule should be applied."
                default: True
    templates:
        type: list
        elements: dict
        required: false
        description: "List of templates to sync."
        suboptions:
            src:
                type: str
                required: true                
                description: "Local path to the source template."
            dest:
                type: str
                required: true
                description: "Remote destination path."
            mode:
                type: str
                default: "0600"
                description: "Permissions for the template file."
            owner:
                type: str
                description: "Owner for this specific template. Overrides the default owner."
            group:
                type: str
                description: "Group for this specific template. Overrides the default group."
            when:
                type: bool
                descriptiom: "If this rule should be applied."
                default: True
'''

EXAMPLES = r'''
- name: Deploy keycloak service bundle
  optionfactory.services.bundle:
    owner: docker-machines
    group: docker-machines
    service_name: keycloak-myapp
    service_args: >
        --network myapp
        --ip 172.18.0.14
        --mount type=bind,source=/opt/myapp/keycloak/deployments/keycloak-myapp-custom.jar,target=/opt/keycloak/providers/keycloak-myapp-custom.jar
        --mount type=bind,source=/opt/myapp/keycloak/conf/keycloak.conf,target=/opt/keycloak/conf/keycloak.conf
        optionfactory/debian13-jdk21-keycloak2:999
    dirs:
      - dest: "/opt/myapp/keycloak/conf"
        mode: "0755"
        owner: "root"
        group: "root"      
    files:
      - dest: "app.jar"
        src: "app.jar"
      - dest: ".env"
        content: "DB_PASS={{ vault_password }}"
      - { content: , dest: ".env" }
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
