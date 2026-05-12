#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r'''
---
module: wireguard_mesh
short_description: Deploy a full-mesh WireGuard VPN topology.
description:
    - This is an action plugin that automatically configures a WireGuard mesh network.
    - It installs necessary packages, enables IPv4 forwarding, manages the configuration
      directory, generates the interface configuration with dynamic TCP MSS clamping,
      and manages the systemd service.
options:
    host_ip:
        type: str
        required: true
        description: "The real IP address (underlay) of the current node executing the task."
    interface:
        type: str
        required: false
        default: "wg-mesh"
        description: "The name of the WireGuard interface and systemd service to create."
    config_template:
        type: str
        required: false
        default: "wireguard_mesh_config.j2"
        description: "The configuration template to use."
    peers:
        type: list
        elements: dict
        required: true
        description: "List of all peers in the mesh network, including the current node."
        suboptions:
            host_ip:
                type: str
                required: true
                description: "The real, physical IP address (Endpoint) of the peer."
            tunnel_cidr:
                type: str
                required: true
                description: "The virtual WireGuard IP and subnet mask (e.g., 10.0.0.1/24)."
            docker_subnet:
                type: str
                required: true
                description: "The Docker subnet behind this peer to route traffic to (e.g., 172.18.1.0/24)."
            private_key:
                type: str
                required: true
                description: "The private key for the peer."
            public_key:
                type: str
                required: true
                description: "The public key for the peer."
'''

EXAMPLES = r'''
- name: Deploy WireGuard Mesh
  optionfactory.services.wireguard_mesh:
    host_ip: "10.1.1.1"
    peers:
      - host_ip: "10.1.1.1"
        tunnel_cidr: "10.0.0.1/24"
        docker_subnet: "172.18.1.0/24"
        private_key: "{{ vault_node_a_priv }}"
        public_key: "PubKeyA="
      - host_ip: "10.1.1.2"
        tunnel_cidr: "10.0.0.2/24"
        docker_subnet: "172.18.2.0/24"
        private_key: "{{ vault_node_b_priv }}"
        public_key: "PubKeyB="
      - host_ip: "10.1.1.3"
        tunnel_cidr: "10.0.0.3/24"
        docker_subnet: "172.18.3.0/24"
        private_key: "{{ vault_node_c_priv }}"
        public_key: "PubKeyC="
'''

RETURN = r'''
msg:
    description: A summary of the WireGuard mesh deployment.
    type: str
    returned: always
changed:
    description: True if any underlying module (package, sysctl, file, copy, systemd) modified the system state.
    type: bool
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
