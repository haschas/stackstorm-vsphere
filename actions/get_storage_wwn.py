from pyVmomi import vim  # pylint: disable-msg=E0611

from vmwarelib import inventory
from vmwarelib import checkinputs
from vmwarelib.actions import BaseAction


class GetStorageWwn(BaseAction):
    def run(self, storage_names, vsphere=None):
        """
        Retrieve Storage WWN

        Args:
        - storage_names: Storage name
        - vsphere: Pre-configured vsphere connection details (config.yaml)

        Returns:
        - dict: Success
        """
        self.establish_connection(vsphere)
        result, error = None, None

        # getting information for provided storages
        datastore_container = self.si_content.viewManager.CreateContainerView(self.si_content.rootFolder, [vim.Datastore], True)
        datastores_list = datastore_container.view
        datastore_container.Destroy()

        # list of datastores wwns
        ds_wwns = []

        # iterate through datastores
        for d in datastores_list:
            if d.name in storage_names:
                for te in d.info.vmfs.extent:
                    ds_wwns.append({'datastore': d.name, 'wwn': te.diskName})

        result = ds_wwns

        return result