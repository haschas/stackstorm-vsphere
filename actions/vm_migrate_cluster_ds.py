from pyVmomi import vim  # pylint: disable-msg=E0611
import sys

from vmwarelib import inventory
from vmwarelib import checkinputs
from vmwarelib.actions import BaseAction


class MigrateVmClDs(BaseAction):
    def run(self, vm_id, vm_name, cluster, vsphere=None):
        """
        Migrate VM to specified datastore

        Args:
        - vm_id: Moid of Virtual Machine to edit
        - vm_name: Name of Virtual Machine to edit
        - cluster: Cluster to which VM needs to be migrated to
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
        # Getting RID code from VM name
        rid = vm_name[:4]
        ds_size_list = []
        #print(rid)
        disk_size = 0
        cluster_container = inventory.get_managed_entities(self.si_content, vim.ClusterComputeResource)
        cluster_list = cluster_container.view
        cluster_container.Destroy()
        #print(cluster_list)
        #cls = inventory.get_cluster(self.si_content, None, cluster)
        #print(cls)
        # iterate through clusters
        for cl in cluster_list:
            if cl.name == cluster:
                datastores = cl.datastore
                # iterate through datastores that
                # exists under specified cluster
                for datastore in datastores:
                    ds = datastore.summary
                    # take datastores that has proper RID
                    if ds.name[:4] == rid:
                        ds_size_list.append((ds.datastore, ds.freeSpace))
        ds_to_migrate_to = max(ds_size_list, key = lambda i : i[1])[0]

        #print(ds_to_migrate_to)
        if ds_to_migrate_to not in vm.datastore:
            #print('Migrating VM to datastore')
            # relocate spec, to miograte vm to another datastore
            # this can be updated with other migrations like:
            # resource pool, host
            relocate_spec = vim.vm.RelocateSpec(datastore=ds_to_migrate_to)
            # does the actual migration
            relocate_vm = vm.Relocate(relocate_spec)
        else:
            return (False, {'state': False, 'msg': 'VM is on proper datastore, will not migrate.'})
        successfully_relocated_vm = self._wait_for_task(relocate_vm)
        if successfully_relocated_vm != True:
            return (False, {'state': successfully_relocated_vm, 'msg': relocate_vm})
        else:
            return {'state': successfully_relocated_vm}
        #return {'state': True}
        #for device in vm.config.hardware.device:
        #    if hasattr(device.backing, 'fileName'):
        #        #print(device)
        #        disk_size += device.capacityInBytes
        #        #disk_size += device.capacityInKB
        #        #print(device.capacityInKB)
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
        #if datastore:
        #    datastore_obj = inventory.get_datastore(self.si_content,
        #                                            name=datastore)
        #    relocate_spec = vim.vm.RelocateSpec(datastore=datastore_obj)
        #    relocate_vm = vm.Relocate(relocate_spec)
        #
        #    summary = datastore_obj.summary
        #    if not disk_size*2 < summary.freeSpace:
        #        return (False, {'state': False, 'msg': 'Datastore %s doesn\'t have enough free space.' % summary.name })
        #else:
        #    return {'state': 'Datastore not provided.'}

        #successfully_relocated_vm = self._wait_for_task(relocate_vm)
        #print(relocate_vm)
        #print(successfully_relocated_vm)
        #if successfully_relocated_vm != True:
        #    return (False, {'state': successfully_relocated_vm, 'msg': relocate_vm})
        #else:
        #    return {'state': successfully_relocated_vm}
