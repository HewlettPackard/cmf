#!/bin/sh
#
#This is the script to perform clean docker removal including data. 
#Backup import data first and run this script with caution.


sudo rm $HOME/neo4j -rf
sudo rm $HOME/minio -rf
sudo rm $HOME/cmf-server -rf


docker-compose -f docker-compose-neo4j.yml down
docker-compose -f docker-compose-minio.yml down
docker-compose -f ../../docker-compose-server.yml down
