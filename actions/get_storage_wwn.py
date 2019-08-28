# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import eventlet
import json

from pyVmomi import vim  # pylint: disable-msg=E0611

from vmwarelib import inventory
from vmwarelib.actions import BaseAction


class GetStorageWwn(BaseAction):

    def run(self, storage_name, vm_name, vsphere=None):
        """
        Retrieve Storage WWN

        Args:
        - storage_name: Storage name
        - vm_name: Name for VM to lookup for storages and their WWNs
        - vsphere: Pre-configured vsphere connection details (config.yaml)

        Returns:
        - dict: Success
        """
        # ensure that minimal inputs are provided
        checkinputs.one_of_two_strings(storage_name, vm_name, "Storage or VM Name")

        self.establish_connection(vsphere)
        result, error = None, None

        # getting information for provided storage
        datastore_container = inventory.get_resources(self.si_content, vim.Datastore)
        datastores_list = datastore_container.view
        datastore_container.Destroy()
        # iterate through clusters
        for d in datastores_list:
            if d.name == storage_name:
                for te in d.info.vmfs.extent:
                    result = {'name': d.name, 'wwn': te.diskName}
            else:
                return

        return result
    