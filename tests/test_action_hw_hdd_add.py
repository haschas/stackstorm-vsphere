import yaml
from mock import Mock, MagicMock

from vsphere_base_action_test_case import VsphereBaseActionTestCase

from vm_hw_hdd_add import VMAddHDD


__all__ = [
    'GetVMDetailsTestCase'
]


class VMAddHDDTestCase(VsphereBaseActionTestCase):
    __test__ = True
    action_cls = VMAddHDD

    def test_run_blank_identifier_input(self):
        action = self.get_action_instance(self.new_config)
        self.assertRaises(ValueError, action.run, vm_id=None,
                          vm_name=None, datastore_cluster=None,
                          datastore=None, disk_size=None,
                          provision_type=None,  vsphere="default")


