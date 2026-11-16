from conftest import make_plugin

from ansible_collections.optionfactory.services.plugins.action import wireguard_mesh as wg_mod


def peer(ip):
    return {
        "host_ip": ip,
        "wg_tunnel_cidr": "10.0.0.1/24",
        "docker_mesh_subnet": "172.19.0.0/24",
        "private_key": "k",
        "public_key": "p",
    }


def test_partition_no_local_match():
    plugin = make_plugin(wg_mod)
    err, local, remotes = plugin.partition_peers("10.9.9.9", [peer("10.1.1.1")])
    assert err["failed"] is True
    assert "no match" in err["msg"]


def test_partition_no_remote_peers():
    plugin = make_plugin(wg_mod)
    err, local, remotes = plugin.partition_peers("10.1.1.1", [peer("10.1.1.1")])
    assert err["failed"] is True
    assert "remote peers" in err["msg"]


def test_partition_happy_path():
    plugin = make_plugin(wg_mod)
    peers = [peer("10.1.1.1"), peer("10.1.1.2"), peer("10.1.1.3")]
    err, local, remotes = plugin.partition_peers("10.1.1.1", peers)
    assert err is None
    assert local is peers[0]
    assert remotes == peers[1:]
