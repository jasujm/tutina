#!/bin/bash
# deploy tutina to AWS lightsail

set -ex

sudo yum update -y
sudo yum install -y emacs git docker mariadb105

#configure docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user

# configure compose
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# setup application
git clone https://github.com/jasujm/tutina.git
cd tutina
touch .env.tutina
cp env/tutina-sample.toml env/tutina.toml
mkdir env/data
docker compose pull

# finish
set +x
echo "Checklist:
 - Edit config in .tutina.env, env/tutina.toml
 - Copy model and data to env/data"
