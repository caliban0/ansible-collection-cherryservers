#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Cherry Servers UAB <info@cherryservers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type  # __metaclass__ is an exception to standard naming style, so pylint: disable=invalid-name.

DOCUMENTATION = r"""
---
module: sshkey

short_description: Create and manage SSH keys on Cherry Servers

version_added: "0.1.0"

description: 
    - Create, update and delete SSH keys on Cherry Servers.
    - The module will attempt to find a key, that matches the specified options.
    - If multiple matching keys are found, the module fails.
    - Otherwise, depending on O(state) and if the key was found or not,
    - it will be updated, deleted or a new key will be created.

options:
    state:
        description:
            - The state of the SSH key.
        default: present
        choices: ['absent', 'present']
        type: str
    public_key:
        description:
            - The public SSH key.
            - Required if the key doesn't exist.
        aliases: [key]
        type: str
    label:
        description:
            - The label of the SSH key.
            - Required if the key doesn't exist.
        aliases: [name]
        type: str
    id:
        description:
            - The ID of the SSH key.
            - Ignored if O(state=present) and SSH key doesn't exist.
        type: int
    fingerprint:
        description:
            - The fingerprint of the SSH key.
            - Ignored if O(state=present) and SSH key doesn't exist.
        type: str


extends_documentation_fragment:
  - local.cherryservers.cherryservers

author:
    - Martynas Deveikis (@caliban0)
"""

EXAMPLES = r"""
- name: Create SSH key
  local.cherryservers.sshkey:
    auth_token: "{{ auth_token }}"
    label: "SSH-test-key"
    public_key: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBYe+GfpsnLP02tfLOJWWFnGKJNpgrzLYE5VZhclrFy0 example@example.com"
    state: present
  register: result

- name: Update SSH key
  local.cherryservers.sshkey:
    auth_token: "{{ auth_token }}"
    label: "SSH-test-key-updated"
    id: "{{ result.cherryservers_sshkey.id }}"
    state: present

- name: Delete SSH key
  local.cherryservers.sshkey:
    auth_token: "{{ auth_token }}"
    label: "SSH-test-key-updated"
    state: absent
"""

RETURN = r"""
cherryservers_sshkey:
    description: SSH key data.
    returned: when O(state=present) and not in check mode
    type: dict
    contains:
        created:
            description: Timestamp of key creation.
            returned: when O(state=present)
            type: str
            sample: "2024-08-06T07:56:16+00:00"
        fingerprint:
            description: SSH key fingerprint.
            returned: when O(state=present)
            type: str
            sample: "54:8e:84:11:bb:29:59:41:36:cb:e2:k2:0c:4a:77:1d"
        href:
            description: SSH key href.
            returned: when O(state=present)
            type: str
            sample: /ssh-keys/7955
        id:
            description: SSH key ID.
            returned: when O(state=present)
            type: int
            sample: 7955
        key:
            description: Public SSH key.
            returned: when O(state=present)
            type: str
            sample: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBYe+GfpsnLP02tfLOJWWFnGKJNpgrzLYE5VZhclrFy0 example@example.com
        label:
            description: SSH key label.
            returned: when O(state=present)
            type: str
            sample: my-label
        updated:
            description: Timestamp of last key update.
            returned: when O(state=present)
            type: str
            sample: "2024-08-06T07:56:16+00:00"
"""

from ansible.module_utils import basic as utils
from ..module_utils import client
from ..module_utils import common
from ..module_utils import constants


def run_module():
    """Execute the ansible module."""
    module_args = get_module_args()

    module = utils.AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    api_client = client.CherryServersClient(module)
    key = common.find_resource_unique(
        api_client,
        module,
        constants.SSH_IDENTIFYING_KEYS,
        "ssh-keys",
        constants.SSH_TIMEOUT,
    )

    if module.params["state"] == "present":
        if key:
            if check_param_state_diff(module.params, key):
                update_key(api_client, module, key["id"])
            elif module.check_mode:
                module.exit_json(changed=False)
            else:
                module.exit_json(changed=False, cherryservers_sshkey=key)
        else:
            create_key(api_client, module)
    elif module.params["state"] == "absent":
        if key:
            delete_key(api_client, module, key)
        else:
            module.exit_json(changed=False)


def get_module_args() -> dict:
    """Return a dictionary with the modules argument specification."""
    module_args = common.get_base_argument_spec()

    module_args.update(
        {
            "state": {
                "choices": ["absent", "present"],
                "default": "present",
                "type": "str",
            },
            "label": {
                "type": "str",
                "aliases": ["name"],
            },
            "public_key": {
                "type": "str",
                "aliases": ["key"],
            },
            "id": {"type": "int"},
            "fingerprint": {"type": "str"},
        }
    )

    return module_args


def check_param_state_diff(module_params: dict, current_state: dict) -> bool:
    """Check if module parameters differ from actual state.

    Check if either `label` or `public_key` are provided in the module params
    and if they differ from actual SSH key state.

    Args:

        module_params (dict): Module parameters.
        current_state (dict): Current SSH key state.

    Returns:

        bool: True if differs from actual SSH key state, False otherwise.

    """
    if (
        module_params["label"] is not None
        and module_params["label"] != current_state["label"]
    ):
        return True
    if (
        module_params["public_key"] is not None
        and module_params["public_key"] != current_state["key"]
    ):
        return True
    return False


def create_key(api_client: client.CherryServersClient, module: utils.AnsibleModule):
    """Create a new SSH key."""
    if module.params["label"] is None or module.params["public_key"] is None:
        module.fail_json("Label and public key are required for creating SSH keys.")

    if module.check_mode:
        module.exit_json(changed=True)

    status, resp = api_client.send_request(
        "POST",
        "ssh-keys",
        constants.SSH_TIMEOUT,
        label=module.params["label"],
        key=module.params["public_key"],
    )
    if status != 201:
        module.fail_json(msg=f"Failed to create SSH key: {resp}")
    module.exit_json(changed=True, cherryservers_sshkey=resp)


def update_key(
    api_client: client.CherryServersClient, module: utils.AnsibleModule, key_id: int
):
    """Update an existing SSH key."""
    if module.check_mode:
        module.exit_json(changed=True)

    status, resp = api_client.send_request(
        "PUT",
        f"ssh-keys/{key_id}",
        constants.SSH_TIMEOUT,
        label=module.params["label"],
        key=module.params["public_key"],
    )
    if status != 201:
        module.fail_json(msg=f"Failed to update SSH key: {resp}")
    module.exit_json(changed=True, cherryservers_sshkey=resp)


def delete_key(api_client: client.CherryServersClient, module: utils.AnsibleModule, key: dict):
    """Delete SSH key that matches the modules argument_spec parameters."""
    if module.check_mode:
        module.exit_json(changed=True)

    key_id = key["id"]
    status, _2 = api_client.send_request(
        "DELETE",
        f"ssh-keys/{key_id}",
        constants.SSH_TIMEOUT,
    )

    if status != 204:
        module.fail_json(f"Failed to delete SSH key: {key_id}")
    module.exit_json(changed=True)


def main():
    """Main function."""
    run_module()


if __name__ == "__main__":
    main()
