from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
from ansible.errors import AnsibleActionFail
display = Display()


class ActionModule(ActionBase):
    def run_action(self, action_name, task_vars, tmp, args):
        new_task = self._task.copy()
        new_task.action = action_name
        new_task.args = args
        action = self._shared_loader_obj.action_loader.get(
            action_name,
            task=new_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj
        )
        return action.run(tmp=tmp, task_vars=task_vars)

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        owner = self._task.args.get('owner', None)
        group = self._task.args.get('group', None)
        service_name = self._task.args.get('service_name')
        service_template = self._task.args.get('service_template', 'service.j2')
        service_args = self._task.args.get('service_args', '')
        dirs = self._task.args.get('dirs', [])
        files = self._task.args.get('files', [])
        templates = self._task.args.get('templates', [])
        changed = False
        reasons = []
        if not service_name:
            raise AnsibleActionFail("The 'service_name' parameter is strictly required.")
        if not service_template:
            raise AnsibleActionFail("The 'service_template' parameter cannot be empty or null.")        
        if not isinstance(dirs, list):
            raise AnsibleActionFail("'dirs' must be a list of dictionaries.")
        for idx, d in enumerate(dirs):
            if not d.get('dest'):
                raise AnsibleActionFail(f"Directory item at index {idx} requires a valid 'dest'.")
        if not isinstance(files, list):
            raise AnsibleActionFail("'files' must be a list of dictionaries.")
        for idx, f in enumerate(files):
            if not f.get('dest'):
                raise AnsibleActionFail(f"File item at index {idx} requires a valid 'dest'.")
            has_src = bool(f.get('src'))
            has_content = 'content' in f
            if not has_src and not has_content:
                raise AnsibleActionFail(f"File '{f['dest']}' must specify a valid 'src' or 'content'.")
            if has_src and has_content:
                raise AnsibleActionFail(f"File '{f['dest']}' cannot specify BOTH 'src' and 'content'.")
        if not isinstance(templates, list):
            raise AnsibleActionFail("'templates' must be a list of dictionaries.")
        for idx, f in enumerate(templates):
            if not f.get('dest'):
                raise AnsibleActionFail(f"Template item at index {idx} requires a valid 'dest'.")
            if not f.get('src'):
                raise AnsibleActionFail(f"Template '{f.get('dest')}' requires a valid 'src'.")
        for d in dirs:
            display.display(f"  - Ensuring directory: {d['dest']}")
            d_res = self._execute_module(
                module_name='ansible.builtin.file',
                task_vars=task_vars,
                module_args={
                    'state': 'directory',
                    'dest': d.get('dest'),
                    'owner': d.get('owner', owner),
                    'group': d.get('group', group),
                    'mode': d.get('mode') or '0700'
                }
            )
            if d_res.get('failed'):
                result.update(d_res)
                return result            
            if d_res.get('changed'):
                changed = True
                reasons.append(f"Dir {d['dest']} created/updated")


        for f in files:
            is_inline = 'content' in f
            display.display(f"  - Syncing file: {f['dest']}")

            module_args = {
                'dest': f.get('dest'),
                'owner': f.get('owner', owner),
                'group': f.get('group', group),
                'mode': f.get('mode') or '0600'
            }            
            if is_inline:
                module_args['content'] = f.get('content')
            else:
                module_args['src'] = f.get('src')
            t_res = self.run_action(
                action_name="ansible.builtin.copy",
                task_vars=task_vars,
                tmp=tmp,
                args=module_args,
            )                
            if t_res.get('failed'):
                result.update(t_res)
                return result            
            if t_res.get('changed'):
                changed = True
                reasons.append(f"File {f['dest']} updated")

        for f in templates:
            display.display(f"  - Syncing template {f['dest']}")
            t_res = self.run_action(
                action_name="ansible.builtin.template",
                task_vars=task_vars,
                tmp=tmp,
                args={
                    'src': f.get('src'),
                    'dest': f.get('dest'),
                    'owner': f.get('owner', owner),
                    'group': f.get('group', group),
                    'mode': f.get('mode') or '0600'
                },
            )
            if t_res.get('failed'):
                result.update(t_res)
                return result            
            if t_res.get('changed'):
                changed = True
                reasons.append(f"Template {f['dest']} updated")

        display.display(f"  - Configuring systemd unit: {service_name}.service")

        svc_task_vars = task_vars.copy()
        svc_task_vars['service_name'] = service_name
        svc_task_vars['service_args'] = service_args

        plugin_dir = os.path.dirname(__file__) 
        collection_root = os.path.abspath(os.path.join(plugin_dir, '../../'))
        collection_templates_dir = os.path.join(collection_root, 'templates')
        actual_template_src = self._loader.get_real_file(service_template) if os.path.exists(service_template) else os.path.join(collection_templates_dir, service_template)
        svc_res = self.run_action(
            action_name='ansible.builtin.template',
            task_vars=svc_task_vars,
            tmp=tmp,
            args={
                'src': actual_template_src,
                'dest': f"/etc/systemd/system/{service_name}.service",
                'owner': 'root',
                'group': 'root',
                'mode': '0644'
            }
        )
        if svc_res.get('failed'):
            result.update(svc_res)
            return result        
        if svc_res.get('changed'):
            changed = True
            reasons.append("Systemd unit changed")

        final_res = self._execute_module(
            module_name='ansible.builtin.systemd',
            task_vars=task_vars,
            module_args={
                'name': service_name,
                'state': 'restarted' if changed else 'started',
                'daemon_reload': changed,
                'enabled': True
            }
        )
        result.update(final_res)

        if final_res.get('failed'):
            return result

        result['changed'] = changed or final_res.get('changed', False)
        result['updates'] = reasons

        return result
