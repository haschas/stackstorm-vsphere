from pyVmomi import vim  # pylint: disable-msg=E0611
import sys
import random

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
        # Getting RID code from VM name
        rid = vm_name[:4]
        ds_size_list = []
        rp_usage_list = []
        dest_hosts = []
        foh_hosts = []

        cluster_container = inventory.get_managed_entities(self.si_content, vim.ClusterComputeResource)
        cluster_list = cluster_container.view
        cluster_container.Destroy()

        # iterate through clusters
        for cl in cluster_list:
            if cl.name == cluster:
                # Resource Pool
                # Checking if there is any failover hosts in the cluster
                # adding those to separate list, further it will be comapred
                # with hosts that are attached to matched datastore 
                if hasattr(cl.configuration.dasConfig.admissionControlPolicy, 'failoverHosts'):
                    for foh in cl.configuration.dasConfig.admissionControlPolicy.failoverHosts:
                        foh_hosts.append(foh)
                for rp in cl.resourcePool.resourcePool:
                    # Generating list of all available resource pools
                    # matching RID
                    if rp.name[:4] == rid:
                        overallUsage = rp.summary.runtime.memory.overallUsage + rp.summary.runtime.cpu.overallUsage
                        rp_usage_list.append((rp, overallUsage))
                # Datastore
                datastores = cl.datastore
                # iterate through datastores that
                # exists under specified cluster
                for datastore in datastores:
                    ds = datastore.summary
                    # take datastores that has proper RID
                    if ds.name[:4] == rid:
                        # getting hosts that are attached to datastore
                        # further those will be compared with FOH hosts
                        for h in datastore.host:
                            dest_hosts.append(h.key)
                        ds_size_list.append((ds.datastore, ds.freeSpace))
        
        # If list is empty, no storages found
        if len(ds_size_list) == 0:
            return (False, {'state': False, 'msg': 'No storages found in cluster {} for rid {}.'.format(cluster, rid)})

        ds_to_migrate_to = max(ds_size_list, key = lambda i : i[1])[0]

        # Checking target resource pool list
        if len(rp_usage_list) == 0:
            return (False, {'state': False, 'msg': 'No resource pools found in cluster {} for rid {}.'.format(cluster, rid)})

        rp_to_mirgate_to = min(rp_usage_list, key = lambda i : i[1])[0]

        # Determing to which host VM should be migrated to
        # on destination cluster
        ok_hosts = list(set(dest_hosts)^set(foh_hosts))
        dest_host = random.choice(ok_hosts)
        
        # Migrate VM only if datastores not matching destination one
        if ds_to_migrate_to not in vm.datastore:
            # Setting vm relocation specification
            vm_relocate_spec = vim.vm.RelocateSpec()
            vm_relocate_spec.host = dest_host
            vm_relocate_spec.pool = rp_to_mirgate_to
            vm_relocate_spec.datastore = ds_to_migrate_to
            # Performing actual migration
            relocate_vm = vm.Relocate(spec=vm_relocate_spec)
        # If VM is already on the same storage
        else:
            return (False, {'state': False, 'msg': 'VM is on proper datastore, will not migrate.'})

        successfully_relocated_vm = self._wait_for_task(relocate_vm)
        if successfully_relocated_vm != True:
            return (False, {'state': successfully_relocated_vm, 'msg': relocate_vm})
        else:
            return {
                    'state': successfully_relocated_vm, 
                    'dest_datastore': ds_to_migrate_to.name, 
                    'dest_cluster': cluster, 
                    'dest_resource_pool': rp_to_mirgate_to.name
                    }
