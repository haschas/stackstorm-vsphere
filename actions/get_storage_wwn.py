from pyVmomi import vim  # pylint: disable-msg=E0611

from vmwarelib import inventory
from vmwarelib import checkinputs
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
        #datastore_container = inventory.get_resources(self.si_content, vim.Datastore)
        datastore_container = self.si_content.viewManager.CreateContainerView(self.si_content.rootFolder, [vim.Datastore], True)
        datastores_list = datastore_container.view
        datastore_container.Destroy()

        # get datastore object
        ds_obj = get_datastore(content, name=storage_name)

        if ds_obj in datastores_list:
            # iterate through clusters
            for d in datastores_list:
                if d.name == storage_name:
                    for te in d.info.vmfs.extent:
                        return ({'name': d.name, 'wwn': te.diskName})
        else:
            return (False, {'state': False, 'msg': 'Datastore not found'})
