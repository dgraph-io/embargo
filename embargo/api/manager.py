#
#  Copyright (C) 2016 Dell, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from ..core import Embargo
from ..errors import InvalidEmbargoName
from ..net import EmbargoNetwork
from ..state import EmbargoState

# TODO(pdmars): breaks if server restarts, refactor to be part of EmbargoState
EMBARGO_CONFIGS = {}
DATA_DIR = "/tmp"


class EmbargoManager:
    """Simple helper for what should eventually be persisted via EmbargoState
    """
    host_exec = None

    @staticmethod
    def set_data_dir(data_dir):
        global DATA_DIR
        DATA_DIR = data_dir

    @staticmethod
    def set_host_exec(host_exec):
        EmbargoManager.host_exec = host_exec

    @staticmethod
    def embargo_exists(name):
        global EMBARGO_CONFIGS
        return name in EMBARGO_CONFIGS

    @staticmethod
    def store_config(name, config):
        global EMBARGO_CONFIGS
        EMBARGO_CONFIGS[name] = config

    @staticmethod
    def delete_config(name):
        global EMBARGO_CONFIGS
        if name in EMBARGO_CONFIGS:
            del EMBARGO_CONFIGS[name]

    @staticmethod
    def load_state(name):
        global DATA_DIR
        try:
            return EmbargoState(embargo_id=name, data_dir=DATA_DIR)
        except InvalidEmbargoName:
            raise

    @staticmethod
    def get_embargo(name):
        global EMBARGO_CONFIGS
        config = EMBARGO_CONFIGS[name]
        host_exec = EmbargoManager.host_exec
        if host_exec is None:
            raise ValueError("host exec not set")
        return Embargo(config,
                        embargo_id=name,
                        state=EmbargoManager.load_state(name),
                        network=EmbargoNetwork(config, host_exec))

    @staticmethod
    def get_all_embargo_names():
        global EMBARGO_CONFIGS
        return list(EMBARGO_CONFIGS.keys())
