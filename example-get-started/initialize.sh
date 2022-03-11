
#!/bin/bash

#This is a convenience script to automate steps to run example-get-started for CMF
#This is assumed to run within (a docker container) ./example-get-started
#This assumes that appropriate ENV Variables are initialized
#Please make sure that ENV variables like GIT_USER_NAME, GIT_USER_EMAIL etc are exported
#Run source sample_env before running this.
echo "Executing git init && dvc init"
git init -q
dvc init -q
git config --global user.name $GIT_USER_NAME
git config --global user.email $GIT_USER_EMAIL

echo "Performing Initial Blank Commit into main"
git branch -M main 
git commit --allow-empty -n -m "Initial code commit"

#Add Remote for Git Project
echo "Setting git remote to $GIT_REMOTE_URL"
git remote add origin $GIT_REMOTE_URL

#Add remote for DVC
echo "Setting dvc default remote to $DVC_REMOTE_URL"
dvc remote add myremote $DVC_REMOTE_URL
#Set remote as default
dvc remote default myremote

echo "Run: ./test_script.sh"
echo "Verify with: git log"
echo "To push artifacts: dvc push"
echo "To push git project/code: git push origin"
echo "See Neo4J Browser at: http://[HOST.IP.AD.DR]:7475/browser/"
