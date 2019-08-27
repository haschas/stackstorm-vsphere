from pyVmomi import vim  # pylint: disable-msg=E0611
import sys

from vmwarelib import inventory
from vmwarelib import checkinputs
from vmwarelib.actions import BaseAction


class MigrateVm(BaseAction):
    def run(self, vm_id, vm_name, datastore_cluster,
            datastore, vsphere=None):
        """
        Migrate VM to specified datastore

        Args:
        - vm_id: Moid of Virtual Machine to edit
        - vm_name: Name of Virtual Machine to edit
        - datastore_cluster: Datastore Cluster to store new hdd files
        - datastore: Datastore to put new files in
        - vsphere: Pre-configured vsphere connection details (config.yaml)


        Returns:
        - dict: Success
        """
        # ensure that minimal inputs are provided
        checkinputs.one_of_two_strings(vm_id, vm_name, "ID or Name")

        self.establish_connection(vsphere)

        vm = inventory.get_virtualmachine(self.si_content, vm_id, vm_name)
        spec = vim.vm.ConfigSpec()
        #print(spec)
        disk_size = 0
        for device in vm.config.hardware.device:
            if hasattr(device.backing, 'fileName'):
                #print(device)
                disk_size += device.capacityInBytes
                #disk_size += device.capacityInKB
                #print(device.capacityInKB)
        ###print(disk_size)
        # If Datastore Cluster is provided attach Disk via that
        #if datastore_cluster:
        #    ds_clust_obj = inventory.get_datastore_cluster(
        #        self.si_content, name=datastore_cluster)
        #    disk_changes.append(disk_spec)
        #    spec.deviceChange = disk_changes
        #    srm = self.si_content.storageResourceManager
        #
        #    storage_placement_spec = self.get_storage_placement_spec(
        #        ds_clust_obj, vm, spec)
        #    datastores = srm.RecommendDatastores(
        #        storageSpec=storage_placement_spec)
        # 
        #    if not datastores.recommendations:
        #        sys.stderr.write('Skipping as No datastore Recommendations')
        # 
        #    add_disk_task = srm.ApplyStorageDrsRecommendation_Task(
        #        datastores.recommendations[0].key)
        #elif datastore:
        if datastore:
            datastore_obj = inventory.get_datastore(self.si_content,
                                                    name=datastore)
            relocate_spec = vim.vm.RelocateSpec(datastore=datastore_obj)
            relocate_vm = vm.Relocate(relocate_spec)

            summary = datastore_obj.summary
            if not disk_size*2 < summary.freeSpace:
                return (False, {'state': False, 'msg': 'Datastore %s doesn\'t have enough free space.' % summary.name })
        else:
            return {'state': 'Datastore not provided.'}

        successfully_relocated_vm = self._wait_for_task(relocate_vm)
        #print(relocate_vm)
        #print(successfully_relocated_vm)
        if successfully_relocated_vm != True:
            return (False, {'state': successfully_relocated_vm, 'msg': relocate_vm})
        else:
            return {'state': successfully_relocated_vm}
