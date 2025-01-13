import os
import platform
import time
from uuid import uuid4

import appdirs
from counterpartycore.lib import config

start_time = time.time()


def get_system():
    return platform.system()


def get_version():
    return config.__version__


def get_uptime():
    return time.time() - start_time


def is_docker():
    """
    Checks if the current process is running inside a Docker container.
    Returns:
        bool: True if running inside a Docker container, False otherwise.
    """
    return (
        os.path.exists("/.dockerenv")
        or "DOCKER_HOST" in os.environ
        or "KUBERNETES_SERVICE_HOST" in os.environ
    )


def get_network():
    return (
        "TESTNET"
        if (
            __read_config_with_default("TESTNET4", False)
            or __read_config_with_default("TESTNET3", False)
        )
        else "MAINNET"
    )


def is_force_enabled():
    return __read_config_with_default("FORCE", False)


def __read_config_with_default(key, default):
    return getattr(config, key, default)


class ID:
    def __init__(self):
        # if file exists, read id from file
        # else create new id and write to file
        id = None

        state_dir = appdirs.user_state_dir(
            appauthor=config.XCP_NAME, appname=config.APP_NAME, roaming=True
        )
        if not os.path.isdir(state_dir):
            os.makedirs(state_dir, mode=0o755)
        node_uid_filepath = os.path.join(state_dir, ".counterparty-node-uuid")

        # Migrate old file
        node_uid_old_filepath = os.path.join(os.path.expanduser("~"), ".counterparty-node-uuid")
        if os.path.exists(node_uid_old_filepath):
            os.rename(node_uid_old_filepath, node_uid_filepath)

        if os.path.exists(node_uid_filepath):
            with open(node_uid_filepath) as f:
                id = f.read()
        else:
            id = str(uuid4())
            with open(node_uid_filepath, "w") as f:
                f.write(id)

        self.id = id
