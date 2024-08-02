#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Cherry Servers UAB <info@cherryservers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type  # __metaclass__ is an exception to standard naming style, so pylint: disable=invalid-name.

DOCUMENTATION = r"""
---
module: sshkey

short_description: Create and manage SSH keys on Cherry Servers.

version_added: "0.1.0"

description: Create, update and delete SSH keys on Cherry Servers.

options:
    auth_token:
        description:
            - API authentication token for Cherry Servers public API.
            - Can be supplied via CHERRY_AUTH_TOKEN and CHERRY_AUTH_KEY environment variables.
            - See https://portal.cherryservers.com/settings/api-keys for more information.
        type: str
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
        type: str
    label:
        description:
            - The label of the SSH key.
        aliases: [name]
        type: str
    id:
        description:
            - The ID of the SSH key.
        type: str
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
# extends_documentation_fragment:
#     - my_namespace.my_collection.my_doc_fragment_name

author:
    - Martynas Deveikis (@caliban0)
"""

EXAMPLES = r"""
- name: "Create SSH key"
  local.cherryservers.sshkey:
    auth_token: "{{ auth_token }}"
    name: "SSH test key"
    public_key: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBYe+GfpsnLP02tfLOJWWFnGKJNpgrzLYE5VZhclrFy0 example@example.com"
    state: present
  register: result
"""

RETURN = r"""
# Cherry Servers API reference: https://api.cherryservers.com/doc/#tag/SshKeys
cherryservers_sshkey:
    description: SSH key data.
    returned: when C(state=present)
    type: dict
    sample: {
        "cherryservers_sshkey": {
            "created": "2024-07-31T05:33:08+00:00",
            "fingerprint": "54:8e:84:11:bb:29:59:41:36:cb:e2:k2:0c:4a:77:1d",
            "href": "/ssh-keys/0000",
            "id": 0000,
            "key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBYe+GfpsnLP02tfLOJWWFnGKJNpgrzLYE5VZhclrFy0 example@example.com",
            "label": "ansible-test",
            "updated": "2024-07-31T05:33:08+00:00"
        }
    }
"""

from ansible.module_utils import basic as utils
from ..module_utils import client


def run_module():
    """Execute the ansible module."""

    module_args = {
        "auth_token": {
            "type": "str",
            "no_log": True,
            "fallback": (utils.env_fallback, ["CHERRY_AUTH_TOKEN", "CHERRY_AUTH_KEY"]),
        },
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
        },
        "id": {"type": "str"},
    }

    module = utils.AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    api_client = client.CherryServersClient(module)

    if module.params["state"] == "present":
        create_key(api_client, module)
    elif module.params["state"] == "absent":
        delete_key(api_client, module)


def check_key_exists(
    api_client: client.CherryServersClient, module: utils.AnsibleModule
) -> bool:
    """Check if the SSH key already exists."""
    status, _2 = api_client.send_request(
        "GET",
        f"ssh-keys/{module.params['key_id']}",
    )

    if status == 200:
        return True
    return False


def create_key(api_client: client.CherryServersClient, module: utils.AnsibleModule):
    """Create a new SSH key."""
    status, resp = api_client.send_request(
        "POST",
        "ssh-keys",
        label=module.params["label"],
        key=module.params["public_key"],
    )
    if status != 201:
        module.fail_json(msg=f"Failed to create SSH key: {resp}")
    module.exit_json(changed=True, cherryservers_sshkey=resp)


def delete_key(api_client: client.CherryServersClient, module: utils.AnsibleModule):
    """Delete the SSH key."""
    status, resp = api_client.send_request(
        "DEL",
        f"ssh-keys/{module.params['key_id']}",
    )
    if status != 204:
        module.fail_json(msg=f"Failed to delete SSH key: {resp}")
    module.exit_json(changed=True, cherryservers_sshkey=resp)


def main():
    """Main function."""
    run_module()


if __name__ == "__main__":
    main()
