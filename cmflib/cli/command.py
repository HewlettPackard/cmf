###
# Copyright (2023) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# Abstract class for commands
class CmdBase(ABC):
    def __init__(self, args):
        self.args = args

    def do_run(self):
        return self.run()

    @abstractmethod
    def run(self):
        pass
