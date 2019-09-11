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
import time

from pyVmomi import vim  # pylint: disable-msg=E0611

from vmwarelib import inventory
from vmwarelib import checkinputs
from vmwarelib.actions import BaseAction


class VMCheckISO(BaseAction):
    def run(self, vm_name, vm_id, vsphere=None):
        """
        Create barebones VM (CPU/RAM/Graphics)

        Args:
        - vm_name: Name of Virtual Machine to detach ISO from
        - vm_id: ID of Virtual Machine to detach ISO from
        - vsphere: Pre-configured vsphere connection details (config.yaml)

        Returns:
        - dict: vm moid of newly created vm
        """
        # Setup Identifiers for objects
        self.establish_connection(vsphere)

        # checkinputs.vm_storage(datastore_cluster, datastore)
        checkinputs.one_of_two_strings(vm_name, vm_id, "Virtual Machine Name or ID")

        vm_obj = inventory.get_virtualmachine(self.si_content, name=vm_name)

        if vm_obj:
            cdrom_number = 1
            cdrom_prefix_label = 'CD/DVD drive '
            cdrom_label = cdrom_prefix_label + str(cdrom_number)
            virtual_cdrom_device = None
            attached, connected = None, None
            for dev in vm_obj.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualCdrom) and dev.deviceInfo.label == cdrom_label:
                    virtual_cdrom_device = dev
                    if hasattr(dev.backing, 'fileName'):
                        if dev.backing.fileName:
                            attached = True
                        else:
                            attached = False
                    if hasattr(dev.connectable, 'connected'):
                        if dev.connectable.connected == True:
                            connected = True
                        else:
                            connected = False

            if not virtual_cdrom_device:
                return ({'connected': connected, 'attached': attached, 'msg': 'Virtual {} could not be found.'.format(cdrom_label)})

            return ({'connected': connected, 'attached': attached})
