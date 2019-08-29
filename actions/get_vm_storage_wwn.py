from pyVmomi import vim  # pylint: disable-msg=E0611

from vmwarelib import inventory
from vmwarelib.actions import BaseAction


class GetVmStorageWwn(BaseAction):
    def run(self, vm_names, vsphere=None):
        """
        Retrieve Storage WWN

        Args:
        - vm_name: Name for VM to lookup for storages and their WWNs
        - vsphere: Pre-configured vsphere connection details (config.yaml)

        Returns:
        - dict: Success
        """

        self.establish_connection(vsphere)
        result, error = None, None

        # get virtual machines
        vms_container = self.si_content.viewManager.CreateContainerView(self.si_content.rootFolder,
                                                                        [vim.VirtualMachine], True)
        vms_list = vms_container.view
        vms_container.Destroy()

        vm_ds_wwns = {}

        # get storages
        datastore_container = self.si_content.viewManager.CreateContainerView(self.si_content.rootFolder,
                                                                              [vim.Datastore], True)
        datastores_list = datastore_container.view
        datastore_container.Destroy()

        # get vm object
        for vm in vms_list:
            if vm.name in vm_names:
                vm_ds_wwns[vm.name] = {}
                vm_disks_list = []
                for vmd in vm.datastore:
                    if vmd in datastores_list:
                        for d in datastores_list:
                            if d == vmd:
                                for te in d.info.vmfs.extent:
                                    vm_disks_list.append({'datastore': d.name, 'wwn': te.diskName})
                                vm_ds_wwns[vm.name] = vm_disks_list
                    else:
                        vm_ds_wwns[vm.name] = {'msg': 'Datastore {} was not found.'.format(vmd.name)}
            else:
                vm_ds_wwns[vm.name] = {'msg': 'VirtualMachine {} was not found.'.format(vm.name)}

        result = vm_ds_wwns

        return result