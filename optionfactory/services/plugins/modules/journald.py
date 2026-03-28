from ansible.module_utils.basic import AnsibleModule
DOCUMENTATION = r'''
---
module: journald
short_description: Configure systemd-journald
description:
  - This module configures systemd-journald.
  - It is backed by an action plugin that automatically manages the persistent journal directory, 
    writes the configuration file, and restarts the systemd-journald service if changes occur.
options:
  configuration:
    description:
      - The raw content to write into C(/etc/systemd/journald.conf).
      - If omitted, the configuration file is left untouched.
    type: str
    required: false
  persistent:
    description:
      - Whether to ensure the C(/var/log/journal) directory exists with correct permissions for persistent logging.
    type: bool
    default: true
'''

EXAMPLES = r'''
# Configures journald as persistent and configures it
- name: Configure journald with persistent storage and a custom configuration
  optionfactory.services.journald:
    persistent: yes
    configuration: |
      [Journal]
      Storage=persistent
      Compress=yes
      SystemMaxUse=1G
      MaxRetentionSec=1month

# Configures journald as persistent
- name: Ensure persistent journal directory exists without changing the conf file
  optionfactory.services.journald:
    persistent: yes
'''

RETURN = r'''
msg:
  description: Summary of the actions taken by the plugin.
  type: str
  returned: always
  sample: "Journald configured."
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
