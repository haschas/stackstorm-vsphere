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
from pyVmomi import vim  # pylint: disable-msg=E0611

from vmwarelib import inventory
from vmwarelib import checkinputs
from vmwarelib.actions import BaseAction


class ResourcePoolRemove(BaseAction):
    def run(self, rp_ids, rp_names, cluster_name, vsphere=None):
        """
        Retrieve MOID of the virtual machine's containing resource pool

        Args:
        - rp_id: Moid of Resource Pool to remove
        - rp_name: Name of Resource Pool to remove
        - cluster_name: Cluster name from which Resource Pool needs to be removed
        - vsphere: Pre-configured vsphere connection details (config.yaml)

        Returns:
        - string: MOID of the VM's containing resource pool ex: resgroup-10
        """

        self.establish_connection(vsphere)

        # get clusters
        cluster_container = inventory.get_managed_entities(self.si_content, vim.ClusterComputeResource)
        cluster_list = cluster_container.view
        cluster_container.Destroy()

        for cluster in cluster_list:
            if cluster.name == cluster_name:
                #print(cluster)
                #print(cluster.name)
                #print(cluster.summary)
                #print(cluster.datastore)
                #print(cluster.resourcePool)
                parent_c = cluster.resourcePool
                #print(resource_pool.summary)
            #else:
            #    return (False, {'state': False, 'msg': 'Cluster {} not found.'.format(cluster_name)})
                

        # get resource pools
        rps_container = self.si_content.viewManager.CreateContainerView(self.si_content.rootFolder,
                                                                        [vim.ResourcePool], True)
        rps_list = rps_container.view
        rps_container.Destroy()

        for r in rps_list:
            if r.name in rp_names:
                #print(r.summary)
                if parent_c == r.parent:
                    if len(r.vm) == 0:
                        # Remove ResourcePool only if there is no VMs inside
                        task = r.Destroy_Task()
                    else:
                        rp_vms = []
                        for vm in r.vm:
                            rp_vms.append(vm.name)
                        return (False, {'state': False, 'msg': rp_vms})

        
        success = self._wait_for_task(task)

        if success != True:
            return (False, {'state': success, 'msg': task})
        else:
            return {'state': success}