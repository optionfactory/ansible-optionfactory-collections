from conftest import FakeConnection, FakeTask

from ansible_collections.optionfactory.services.plugins.module_utils.actions import Action


class FakeModuleContext:
    def __init__(self, resolved, action_plugin):
        self.resolved = resolved
        self.action_plugin = action_plugin


class FakeModuleLoader:
    def __init__(self, routing):
        self.routing = routing

    def find_plugin_with_context(self, name, collection_list=None, **kwargs):
        resolved, action_plugin = self.routing.get(name, (True, None))
        return FakeModuleContext(resolved, action_plugin)


class FakeActionLoader:
    def __init__(self, plugins):
        self.plugins = plugins

    def has_plugin(self, name, collection_list=None):
        return name in self.plugins


class FakeSharedLoader:
    def __init__(self, module_routing, action_plugins):
        self.module_loader = FakeModuleLoader(module_routing)
        self.action_loader = FakeActionLoader(action_plugins)


def dispatch(module_routing, action_plugins, name):
    called = []
    action = Action(
        task=FakeTask(),
        connection=FakeConnection(),
        play_context=None,
        loader=None,
        templar=None,
        shared_loader_obj=None,
    )
    action._shared_loader_obj = FakeSharedLoader(module_routing, action_plugins)
    action.action_step = lambda ctx, conf: (called.append("action"), (None, False))[1]
    action.module_step = lambda ctx, conf: (called.append("module"), (None, False))[1]
    action.step(None, {"name": name})
    return called[0]


def test_module_routing_action_plugin_wins():
    name = "ansible.builtin.copy"
    assert dispatch({name: (True, name)}, [], name) == "action"


def test_action_loader_fallback():
    name = "ansible.builtin.copy"
    assert dispatch({}, [name], name) == "action"


def test_package_without_action_plugin_goes_module_path():
    name = "ansible.builtin.package"
    assert dispatch({}, [], name) == "module"


def test_package_with_action_plugin_goes_action_path():
    name = "ansible.builtin.package"
    assert dispatch({name: (True, name)}, [], name) == "action"


def test_unresolved_module_with_action_plugin_still_action_path():
    name = "ansible.builtin.template"
    assert dispatch({name: (False, None)}, [name], name) == "action"
