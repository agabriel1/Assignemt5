#!/bin/bash
set -x
sudo yum -y group install "Development Tools"
cd /software
sudo wget https://download.open-mpi.org/release/open-mpi/v3.1/openmpi-3.1.2.tar.gz
sudo tar xzf openmpi-3.1.2.tar.gz
cd openmpi-3.1.2
sudo ./configure --prefix=/software
sudo make
sudo make all install
echo "export PATH='$PATH:/software/bin'" >> /users/ag899460/.bashrc
echo "export LD_LIBRARY_PATH='$LD_LIBRARY_PATH:/software/lib/'" >> /users/ag899460/.bashrc
cd ..
sudo rm -Rf openmpi-3.1.2
sudo rm -Rf openmpi-3.1.2.tar.gz
