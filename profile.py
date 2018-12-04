# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
import geni.rspec.igext as IG

# Create a portal context.
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()


tourDescription = \
"""
This profile provides the template for a full research cluster with head node, scheduler, compute nodes, and shared file systems.
First node (head) should contain: 
- Shared home directory using Networked File System
- Management server for SLURM
Second node (metadata) should contain:
- Metadata server for SLURM
Third node (storage):
- Shared software directory (/software) using Networked File System
Remaining three nodes (computing):
- Compute nodes  
"""

#
# Setup the Tour info with the above description and instructions.
#  
tour = IG.Tour()
tour.Description(IG.Tour.TEXT,tourDescription)
request.addTour(tour)


link = request.LAN("lan")

for i in range(15):
  if i == 0:
    node = request.XenVM("head")
    node.routable_control_ip = "true" 
  elif i == 1:
    node = request.XenVM("metadata")
  elif i == 2:
    node = request.XenVM("storage")
  else:
    node = request.XenVM("compute" + str(i-2))
    node.cores = 2
    node.ram = 4096
    
  node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops:CENTOS7-64-STD"
  
  iface = node.addInterface("if" + str(i-3))
  iface.component_id = "eth1"
  iface.addAddress(pg.IPv4Address("192.168.1." + str(i + 1), "255.255.255.0"))
  link.addInterface(iface)
  
  #setup automatic ssh permissions
  node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/scripts/passwordless.sh"))
  node.addService(pg.Execute(shell="sh", command="sudo /local/repository/scripts/passwordless.sh"))
  
  #deal with firewall on all nodes
  node.addService(pg.Execute(shell="sh", command="sudo systemctl stop firewalld"))
  node.addService(pg.Execute(shell="sh", command="sudo systemctl disable firewalld"))
 
  #make directories and set permissions for all nodes
  if i != 2:
    node.addService(pg.Execute(shell="sh", command="sudo mkdir /software"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /software"))
  node.addService(pg.Execute(shell="sh", command="sudo mkdir /scratch"))
  node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /scratch"))
  
  #setup storage node
  if i == 2:
    node.addService(pg.Execute(shell="sh", command="sudo yum -y install nfs-utils"))
    node.addService(pg.Execute(shell="sh", command="sudo su ag899460 -c 'sudo cp /local/repository/source/* /scratch'"))
    node.addService(pg.Execute(shell="sh", command="sudo su ag899460 -c 'sudo cp /local/repository/scripts/dbd.sql /scratch/dbd.sql'"))
    node.addService(pg.Execute(shell="sh", command="sudo su ag899460 -c 'sudo cp /local/repository/scripts/setup.sql /scratch/setup.sql'"))
    node.addService(pg.Execute(shell="sh", command="sudo su ag899460 -c 'sudo cp /local/repository/export/innodb.cnf /scratch/innodb.cnf'"))
    node.addService(pg.Execute(shell="sh", command="sudo su ag899460 -c 'sudo cp /local/repository/scripts/sbatch.sh /scratch/sbatch.sh'"))
    node.addService(pg.Execute(shell="sh", command="sudo su ag899460 -c 'sudo cp /local/repository/export/slurmdbd.conf /scratch/slurmdbd.conf'"))
    node.addService(pg.Execute(shell="sh", command="sudo su ag899460 -c 'sudo cp /local/repository/export/slurm.conf /scratch/slurm.conf'"))
    node.addService(pg.Execute(shell="sh", command="sudo rm /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo cp /local/repository/export/export_scratch /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo systemctl enable nfs-server"))
    node.addService(pg.Execute(shell="sh", command="sudo systemctl start nfs-server"))
    node.addService(pg.Execute(shell="sh", command="sudo exportfs -a"))
    
  #install mpi on the head node in /software and mount /scratch 
  if i == 0:
    node.addService(pg.Execute(shell="sh", command="sudo yum -y install nfs-utils"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/scripts/install_mpi.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo /local/repository/scripts/install_mpi.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo rm /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo cp /local/repository/export/export_software /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo mkdir /etc/slurm"))

    node.addService(pg.Execute(shell="sh", command="sudo systemctl enable nfs-server"))
    node.addService(pg.Execute(shell="sh", command="sudo systemctl start nfs-server"))
    node.addService(pg.Execute(shell="sh", command="sudo exportfs -a"))
    node.addService(pg.Execute(shell="sh", command="sleep 2m"))
    node.addService(pg.Execute(shell="sh", command="sudo mount -t nfs 192.168.1.3:/scratch /scratch"))
    node.addService(pg.Execute(shell="sh", command="sudo echo '192.168.1.3:/scratch /scratch nfs4 rw,relatime,vers=4.1,rsize=131072,wsize=131072,namlen=255,hard,proto=tcp,port=0,timeo=600,retrans=2,sec=sys,local_lock=none,addr=192.168.1.3,_netdev,x-systemd.automount 0 0' | sudo tee --append /etc/fstab"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/scripts/slurm_head.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo /local/repository/scripts/slurm_head.sh"))
    
  #mount /scratch and /software on metadata node
  if i == 1:
    node.addService(pg.Execute(shell="sh", command="sudo yum -y install nfs-utils"))
    node.addService(pg.Execute(shell="sh", command="sleep 28m"))

    node.addService(pg.Execute(shell="sh", command="sudo mount -t nfs 192.168.1.3:/scratch /scratch"))
    node.addService(pg.Execute(shell="sh", command="sudo mount -t nfs 192.168.1.1:/software /software"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /local/repository/scripts/mpi_path_setup.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo -H -u ag899460 bash -c '/local/repository/scripts/mpi_path_setup.sh'"))   
    node.addService(pg.Execute(shell="sh", command="sudo echo '192.168.1.1:/software /software nfs4 rw,relatime,vers=4.1,rsize=131072,wsize=131072,namlen=255,hard,proto=tcp,port=0,timeo=600,retrans=2,sec=sys,local_lock=none,addr=192.168.1.1,_netdev,x-systemd.automount 0 0' | sudo tee --append /etc/fstab"))
    node.addService(pg.Execute(shell="sh", command="sudo echo '192.168.1.3:/scratch /scratch nfs4 rw,relatime,vers=4.1,rsize=131072,wsize=131072,namlen=255,hard,proto=tcp,port=0,timeo=600,retrans=2,sec=sys,local_lock=none,addr=192.168.1.3,_netdev,x-systemd.automount 0 0' | sudo tee --append /etc/fstab"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/scripts/slurm_metadata.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo /local/repository/scripts/slurm_metadata.sh"))
    
  #mount /scratch and /software on each compute node
  if i > 2:
    node.addService(pg.Execute(shell="sh", command="sudo yum -y install nfs-utils"))
    node.addService(pg.Execute(shell="sh", command="sleep 28m"))
    
    node.addService(pg.Execute(shell="sh", command="sudo mount -t nfs 192.168.1.3:/scratch /scratch"))
    node.addService(pg.Execute(shell="sh", command="sudo mount -t nfs 192.168.1.1:/software /software"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /local/repository/scripts/mpi_path_setup.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo -H -u ag899460 bash -c '/local/repository/scripts/mpi_path_setup.sh'"))   
    node.addService(pg.Execute(shell="sh", command="sudo echo '192.168.1.1:/software /software nfs4 rw,relatime,vers=4.1,rsize=131072,wsize=131072,namlen=255,hard,proto=tcp,port=0,timeo=600,retrans=2,sec=sys,local_lock=none,addr=192.168.1.1,_netdev,x-systemd.automount 0 0' | sudo tee --append /etc/fstab"))
    node.addService(pg.Execute(shell="sh", command="sudo echo '192.168.1.3:/scratch /scratch nfs4 rw,relatime,vers=4.1,rsize=131072,wsize=131072,namlen=255,hard,proto=tcp,port=0,timeo=600,retrans=2,sec=sys,local_lock=none,addr=192.168.1.3,_netdev,x-systemd.automount 0 0' | sudo tee --append /etc/fstab"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/scripts/slurm_compute.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo /local/repository/scripts/slurm_compute.sh"))
    
# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)
