#!/bin/bash

#create global users
export MUNGEUSER=991
sudo groupadd -g $MUNGEUSER munge
sudo useradd  -m -c "MUNGE Uid 'N' Gid Emporium" -d /var/lib/munge -u $MUNGEUSER -g munge  -s /sbin/nologin munge
export SLURMUSER=992
sudo groupadd -g $SLURMUSER slurm
sudo useradd  -m -c "SLURM workload manager" -d /var/lib/slurm -u $SLURMUSER -g slurm  -s /bin/bash slurm

#install munge
sudo yum install epel-release -y
sudo yum install munge munge-libs munge-devel -y

#munge secret key setup
sudo yum install rng-tools -y
sudo rngd -r /dev/urandom --no-tpm=1

#create munge secret key
sudo /usr/sbin/create-munge-key -r
sudo chown munge: /etc/munge/munge.key
sudo chmod 400 /etc/munge/munge.key

#pass munge secret key to compute nodes
sudo cp /etc/munge/munge.key /scratch/munge.key

#correct permissions
sudo chown -R munge: /etc/munge/ /var/log/munge/
sudo chmod 0700 /etc/munge/ /var/log/munge/

while [ ! -f /scratch/metakey.fin ]
do
  sleep 10
done

#start munge service
sudo systemctl enable munge
sudo systemctl start munge

#install slurm dependencies
sudo yum install openssl openssl-devel pam-devel numactl numactl-devel hwloc hwloc-devel lua lua-devel readline-devel rrdtool-devel ncurses-devel man2html libibmad libibumad -y

#get the slurm tarball 
cd /software
sudo wget http://www.schedmd.com/download/latest/slurm-18.08.3.tar.bz2
sudo yum install rpm-build
sudo yum install perl -y
sudo yum install 'perl(ExtUtils::MakeMaker)' -y
sudo rpmbuild -ta slurm-18.08.3.tar.bz2
#cd /root/rpmbuild/RPMS/x86_64

#transfer slurm RPMS to a shared folder
sudo mkdir /software/slurm-rpms
sudo cp /root/rpmbuild/RPMS/x86_64/* /software/slurm-rpms

sudo touch /scratch/rpm.fin

#install slurm
sudo yum --nogpgcheck localinstall /software/slurm-rpms/* -y

#head configuration
sudo cp /scratch/slurm.conf /etc/slurm/slurm.conf
sudo mkdir /var/spool/slurmctld
sudo chown slurm: /var/spool/slurmctld
sudo chmod 755 /var/spool/slurmctld
sudo touch /var/log/slurmctld.log
sudo chown slurm: /var/log/slurmctld.log
sudo touch /var/log/slurm_jobacct.log /var/log/slurm_jobcomp.log
sudo chown slurm: /var/log/slurm_jobacct.log /var/log/slurm_jobcomp.log
sudo touch /var/run/slurmctld
sudo chmod 777 /var/run/slurmctld

#setup clock
sudo yum install ntp -y
sudo chkconfig ntpd on
sudo ntpdate pool.ntp.org
sudo systemctl start ntpd

#enable slurm daemon
while [ ! -f /scratch/d.fin ]
do
  sleep 5
done
sudo systemctl enable slurmctld
sudo systemctl start slurmctld

#notify metadata slurmctld daemon is up
sudo touch /scratch/head.fin

#wait for callback from metadata
while [ ! -f /scratch/cluster.fin ]
do
  sleep 5
done

#restart slurmctld daemon
sudo systemctl restart slurmctld

#remove setup files
cd /scratch
sudo rm d.fin dbd.fin dbd.sql innodb.cnf metakey.fin munge.key rpm.fin setup.sql slurm.conf slurmdbd.conf
