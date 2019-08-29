from pyVmomi import vim  # pylint: disable-msg=E0611

from vmwarelib import inventory
from vmwarelib.actions import BaseAction


class GetVmStorageWwn(BaseAction):
    def run(self, vm_name, vsphere=None):
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

        # getting information for provided storage
        datastore_container = self.si_content.viewManager.CreateContainerView(self.si_content.rootFolder, [vim.Datastore], True)
        datastores_list = datastore_container.view
        datastore_container.Destroy()

        vm_disks = []
        # get vm object
        vm_obj = inventory.get_virtualmachine(self.si_content, name=vm_name)
        if vm_obj:
            for vmd in vm_obj.datastore:
                if vmd in datastores_list:
                    # iterate through datastores
                    for d in datastores_list:
                        if d == vmd:
                            for te in d.info.vmfs.extent:
                                vm_disks.append({'name': d.name, 'wwn': te.diskName})
                else:
                    error = "Unable to find datastore {0}.".format(vmd.name)
        else:
            error = "Unable to retrieve VM {0} details. Check name provided.".format(vm_name)

        result = vm_disks

        if error:
            return (False, {'state': False, 'msg': error})
        else:
            return result