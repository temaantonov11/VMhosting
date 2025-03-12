import libvirt
from logger import *
import os
import subprocess
import socket
import json
import time


class QEMUMananger:
    def __init__(self):
        try:
            self.__connection = libvirt.open("qemu:///system")
            self.vm = None  # Инициализация атрибута vm
            log.info("[QEMU]: Successful connect to hypervisor")
        except libvirt.libvirtError as _ex:
            log.error(f"[QEMU]: Failed connection to hypervisor \n {_ex}")
    
    def __generateVMconfig(self, name, cpu, memory, disk_size_gib, os_image, network = 'default'):
        disk_size_bytes = disk_size_gib * 1024 * 1024 * 1024
        
        project_dir = os.path.dirname(os.path.abspath(__file__))
        base_image = f"/var/lib/libvirt/images/{os_image}"
        new_disk = os.path.join(project_dir, "vm_disks", f"{name}.qcow2")
        os.makedirs(os.path.dirname(new_disk), exist_ok=True)

        if not os.path.exists(new_disk):
            try:
                subprocess.run(
                    ["qemu-img", "create", "-f", "qcow2", "-b", base_image, "-F", "qcow2", new_disk, f"{disk_size_gib}G"], check=True
                )
            except subprocess.CalledProcessError as _ex:
                log.error(f"[QEMU]: Failed new image created. \n {_ex}")
        else:
            log.info(f"[QEMU]: Image {new_disk} has exist yet.")

        vm_config = f"""
        <domain type='qemu'>
            <name>{name}</name>
            <memory unit='MiB'>{memory}</memory>
            <vcpu placement='static'>{cpu}</vcpu>
            <os>
                <type arch='x86_64' machine='pc-i440fx-2.9'>hvm</type>
                <boot dev='hd'/>
            </os>
            <devices>
                <disk type='file' device='disk'>
                    <driver name='qemu' type='qcow2'/>
                    <source file='{new_disk}'/>
                    <target dev='vda' bus='virtio'/>
                </disk>
                <interface type='network'>
                    <source network='{network}'/>
                    <model type='virtio'/>
                </interface>
                <graphics type='vnc' port='-1' autoport='yes'/>
            </devices>
            <qemu:commandline>
                <qemu:arg value='-qmp'/>
                <qemu:arg value='unix:/tmp/qmp-socket,server,nowait'/>
            </qemu:commandline>
        </domain>
        """
        return vm_config

    def getIP(self):
        try:

            timeout = 300
            start_time = time.time()

            while time.time() - start_time < timeout:
                ifaces = self.vm.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
                if ifaces:
                    for (name, val) in ifaces.items():
                        if val['addrs']:
                            for ipaddr in val['addrs']:
                                if ipaddr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                                    log.info(f"IP addres of VM: {ipaddr['addr']}")
                                    vm_ip = ipaddr['addr']
                                    return vm_ip 

            return None
        except libvirt.libvirtError as _ex:
            log.error(f"Failed get ID \n {_ex}")
            return None
    
    def createVM(self, name, cpu, memory, disk_size_gib, os_image, network = 'default'):
        try:
            self.vm = self.__connection.createXML(self.__generateVMconfig(name, cpu, memory, disk_size_gib, os_image, network))
            log.info(f"[QEMU]: VM {self.vm.name} created successfully.")
        except libvirt.libvirtError as _ex:
            log.error(f'[QEMU]: Failed create VM. \n {_ex}')

    def stopVM(self):
        try:
            if self.vm is None:
                log.error("[QEMU]: VM object is not initialized.")
                return
            
            if self.__connection is None:
                log.error("[QEMU]: Connection to hypervisor is not established.")
                return

            if not self.vm.isActive():
                log.info("[QEMU]: VM object is already stopped.")
                return
            
            self.vm.destroy()
            log.info(f"[QEMU]: VM stopped successfully.")
        except Exception as _ex:
            log.error(f'[QEMU]: Failed stop VM. \n {_ex}')

    def get_cpu_usage(self):
        try:
            if self.vm is None:
                log.error("[QEMU]: VM object is not initialized.")
                return None
            info = self.vm.info()
            cpu_time = info[4]
            cpu_count = info[3]
            cpu_load = (cpu_time / 1e9) / cpu_count
            return cpu_load
        except libvirt.libvirtError as _ex:
            log.error(f"[QEMU]: Failed to get CPU usage. \n {_ex}")

    def get_memory_usage(self):
        try:
            if self.vm is None:
                log.error("[QEMU]: VM object is not initialized.")
                return None
            info = self.vm.info()
            used_memory = info[1]
            return used_memory / 1024
        except libvirt.libvirtError as _ex:
            log.error(f"[QEMU]: Failed to get memory usage.")

    def get_disk_usage(self):
        try:
            if self.vm is None:
                log.error("[QEMU]: VM object is not initialized.")
                return None
            disk_stats = self.vm.blockStats('vda')
            read_bytes = disk_stats[0]
            write_bytes = disk_stats[1]
            return read_bytes, write_bytes            
        except libvirt.libvirtError as _ex:
            log.error(f"[QEMU]: Failed to get disk usage.")


    
