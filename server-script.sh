#!/bin/bash
sudo apt-get update
# : '
#install nginx
sudo apt update
sudo apt install -y nginx
sudo ufw allow 'Nginx HTTP'

# install AWS-CLI
sudo apt install -y unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Deploy UI
mkdir demo-UI
aws s3 cp s3://demo-data4-prod/demo-prod-UI.zip demo-UI
sudo unzip demo-UI/demo-prod-UI.zip -d /var/www/html

# Install PostgreSQL DB Client
sudo apt install -y postgresql-client-common
sudo apt install -y postgresql-client

# Install Python3 and dependencies
sudo apt update
sudo apt install -y software-properties-common
sudo apt install -y python3
sudo apt install -y python3-pip
sudo pip3 install gekko
sudo pip3 install pandas
sudo pip3 install matplotlib
sudo pip3 install Flask

# Install R and dependencies

#Add GPG Key
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9

#Add the R Repository
sudo add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu bionic-cran40/'

#Update Package Lists
sudo apt update

#Install R
sudo apt install -y r-base
mkdir R_Scripts
aws s3 cp s3://demo-data4-prod/demo_R_packages.R R_Scripts

# Install R packages dependencies
sudo apt-get update
sudo apt-get install -y openjdk-8-jdk
sudo R CMD javareconf
sudo apt-get install -y libcurl4-openssl-dev libxml2-dev
sudo apt-get install -y libglu1-mesa-dev

# Install R packages
sudo nohup Rscript /R_Scripts/demo_R_packages.R > nohup_r.out
# '
# Mount the EBS Volume
sudo mkfs -t xfs /dev/xvdh
sudo mkdir /data
sudo mount /dev/xvdh /data
