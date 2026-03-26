#!/usr/bin/python

DOCUMENTATION = r'''
---
module: service_bundle
short_description: Deploy a service and its files in one step.
description:
    - This is an action plugin that ensures directories exist, syncs files/templates, 
      and restarts the systemd service if anything changed.
options:
    service_name:
        type: str
        required: true
        description: "The name of the systemd service"
    service_template:
        type: str
        required: false
        default: "service.j2"
        description: "Path to the Jinja2 template for the systemd .service file."
    service_args:
        type: str
        required: false
        description: "arguments passed to the systemd service template"
    owner: 
        type: str
        description: "Default owner for all managed directories, files, and templates."        
    group: 
        type: str
        description: "Default group for all managed directories, files, and templates."        
    dirs:
        type: list
        elements: dict
        required: false
        description: "List of dirs to provision."
        options:
            dest:
                type: str
                required: true
                description: "Path to be created"
            mode:
                type: str
                default: "0700"
                description: "Permissions for the dir."
            owner:
                description: Owner for this specific directory.
                type: str
            group:
                description: Group for this specific directory.
                type: str
    files:
        type: list
        elements: dict
        required: false
        description: "List of files to sync."
        options:
            src:
                type: str
                description: "Local path to the source file, alternative to content"
            content:
                type: str
                description: "Inline string content, alternative to src"
            dest:
                type: str
                required: true
                description: "Remote destination path"
            mode:
                type: str
                default: "0600"
                description: "Permissions for the file."
            owner:
                description: Owner for this specific file.
                type: str
            group:
                description: Group for this specific file.
                type: str                                        
    templates:
        type: list
        elements: dict
        required: false
        description: "List of templates to sync."
        options:
            src:
                type: str
                required: true                
                description: "Local path to the source template"
            dest:
                type: str
                required: true
                description: "Remote destination path"
            mode:
                type: str
                default: "0600"
                description: "Permissions for the file."
            owner:
                description: Owner for this specific file.
                type: str
            group:
                description: Group for this specific file.
                type: str

'''

### Default dir mode is 0700
### Default file mode is 0600

EXAMPLES = r'''
- optionfactory.service_bundles.service_bundle:
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
      - { dest: "/opt/myapp/keycloak/conf", mode: "", owner: "", group: ""}
    files:
      - { src: "app.jar", dest: "app.jar", mode: "0755" }
      - { content: "DB_PASS={{ vault_password }}", dest: ".env" }
'''