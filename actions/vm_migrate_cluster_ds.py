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
        - vm_id: Moid of Virtual Machine to migrate
        - vm_name: Name of Virtual Machine to migrate
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
        # Getting RID code from VM name
        rid = vm_name[:4]
        ds_size_list = []
        disk_size = 0
        cluster_container = inventory.get_managed_entities(self.si_content, vim.ClusterComputeResource)
        cluster_list = cluster_container.view
        cluster_container.Destroy()
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
        if ds_to_migrate_to not in vm.datastore:
            # relocate spec, to migrate vm to another datastore
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
