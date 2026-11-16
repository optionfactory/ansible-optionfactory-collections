from ansible.module_utils.basic import AnsibleModule
DOCUMENTATION = r'''
---
module: wireguard_mesh
short_description: Configures a full-mesh WireGuard VPN topology.
description:
    - This is an action plugin that automatically configures a WireGuard mesh network.
    - It installs necessary packages, enables IPv4 forwarding, generates the wg interface
      configuration, the docker mesh network, manages the systemd service, configures docker daemon to start
      after the configured wg-quick service.
    - "The docker mesh network is routed, not masqueraded, so it carries traffic between the nodes only. A container that also needs the internet or hosts outside the mesh must be attached to a second, masqueraded network."
    - "That second network must have a higher gateway priority than the mesh network, so that it provides the default gateway (e.g. '--network name=project --network name=wg-mesh-docker,gw-priority=-1,ip=172.19.10.11'). With the mesh network as default gateway, traffic leaving the mesh is not masqueraded and gets no reply."
    - "The other nodes are then reached with the 'routes' option of the 'container' block of M(optionfactory.services.bundle) and M(optionfactory.services.service), one route per remote 'docker_mesh_subnet' via the gateway of the local one."

options:
    host_ip:
        type: str
        required: true
        description: "The real IP address of the current node executing the task."
    interface:
        type: str
        required: false
        default: "wg-mesh"
        description: "The name of the WireGuard interface and systemd service to create."
    docker_mesh_mtu:
        type: int
        required: false
        description:
            - "The Docker mesh interface mtu (e.g., 1420)"
            - "Changing it on an existing mesh recreates the Docker network: attached containers are
               reconnected with newly assigned addresses, so containers with a fixed ip must be recreated."
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
                description: "The real IP address of the peer."
            wg_tunnel_cidr:
                type: str
                required: true
                description: "The virtual WireGuard IP and subnet mask (e.g., 10.0.0.1/24)."
            docker_mesh_subnet:
                type: str
                required: true
                description: "The Docker subnet behind this peer to route traffic to (e.g., 172.19.10.0/24)."
            private_key:
                type: str
                required: true
                description: "The private key for the peer. (you can use 'wg genkey | tee /dev/tty | wg pubkey')"
            public_key:
                type: str
                required: true
                description: "The public key for the peer. (you can use 'wg genkey | tee /dev/tty | wg pubkey')"
'''

EXAMPLES = r'''
- name: Deploy WireGuard Mesh
  optionfactory.services.wireguard_mesh:
    host_ip: "172.31.47.254"
    peers:
      - host_ip: 172.31.47.254
        wg_tunnel_cidr: 10.0.0.1/24
        docker_mesh_subnet: 172.19.10.0/24
        private_key: "{{ keys.testwg1.private }}"
        public_key: "{{ keys.testwg1.public }}"
      - host_ip: 172.31.35.12
        wg_tunnel_cidr: 10.0.0.2/24
        docker_mesh_subnet: 172.19.20.0/24
        private_key: "{{ keys.testwg2.private }}"
        public_key: "{{ keys.testwg2.public }}"
      - host_ip: 172.31.44.136
        wg_tunnel_cidr: 10.0.0.3/24
        docker_mesh_subnet: 172.19.30.0/24
        private_key: "{{ keys.testwg3.private }}"
        public_key: "{{ keys.testwg3.public }}"
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
