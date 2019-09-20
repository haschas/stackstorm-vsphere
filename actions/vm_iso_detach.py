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


class VMDetachISO(BaseAction):
    def run(self, vm_name, vm_id, answer=None, vsphere=None):
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
        result, error = None, None
        # checkinputs.vm_storage(datastore_cluster, datastore)
        checkinputs.one_of_two_strings(vm_name, vm_id, "Virtual Machine Name or ID")

        vm_obj = inventory.get_virtualmachine(self.si_content, name=vm_name)

        # Setting answer value
        # Answers:
        # 0: button.yes
        # 1: button.no
        if answer:
            if answer == "Yes":
                qa = str(0)
            else:
                qa = str(1)

        if vm_obj:
            dev_changes = []

            cdrom_number = 1
            cdrom_prefix_label = 'CD/DVD drive '
            cdrom_label = cdrom_prefix_label + str(cdrom_number)
            virtual_cdrom_device = None
            for dev in vm_obj.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualCdrom) and dev.deviceInfo.label == cdrom_label:
                    virtual_cdrom_device = dev
                    #print(dev)

            if not virtual_cdrom_device:
                error = ('Virtual {} could not be found.'.format(cdrom_label))

            virtual_cd_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_cd_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            virtual_cd_spec.device = vim.vm.device.VirtualCdrom()
            virtual_cd_spec.device.controllerKey = virtual_cdrom_device.controllerKey
            virtual_cd_spec.device.key = virtual_cdrom_device.key
            virtual_cd_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            # Adding no CD
            virtual_cd_spec.device.backing = vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo()
            # Allowing guest control
            virtual_cd_spec.device.connectable.allowGuestControl = True
            dev_changes.append(virtual_cd_spec)
            spec = vim.vm.ConfigSpec()
            spec.deviceChange = dev_changes
            remove_iso_task = vm_obj.ReconfigVM_Task(spec)

            while remove_iso_task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                if vm_obj.runtime.question is not None:
                    for qm in vm_obj.runtime.question.message:
                        if qm.id == 'msg.cdromdisconnect.locked':
                            msg = qm.text
                            question_id = vm_obj.runtime.question.id
                            if answer:
                                if answer == "Yes":
                                    vm_obj.AnswerVM(question_id, qa)
                            else:
                                # Answering with No, to leave ISO connected
                                vm_obj.AnswerVM(question_id, str(1))
                # using time.sleep to wait for answer to be applied
                time.sleep(5)
            #print(remove_iso_task.info.state)
            if remove_iso_task.info.state == vim.TaskInfo.State.error:
                return (False, {'state': remove_iso_task.info.state, 'msg': msg})
            else:
                return {'state': remove_iso_task.info.state}
