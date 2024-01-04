#!/bin/bash

#This is a convenience script to automate steps to run example-get-started for CMF
#This is assumed to run within (a docker container) ./example-get-started
#This assumes that appropriate ENV Variables are initialized
#Please make sure that ENV variables like GIT_USER_NAME, GIT_USER_EMAIL etc are exported
#Run source sample_env before running this.
echo "[1/5] [GIT/DVC INIT  ] executing git init and dvc init."
git init -q
dvc init -q
git config --global user.name "${GIT_USER_NAME:-first second}"
git config --global user.email "${GIT_USER_EMAIL:-first.second@corp.com}"

echo "[2/5] [INITIAL COMMIT] performing initial blank commit into main."
git checkout -b master
git commit --allow-empty -n -m "Initial code commit"

echo "[3/5] [GIT REMOTE    ] setting git remote to ${GIT_REMOTE_URL}"
git remote add origin "${GIT_REMOTE_URL:-/tmp/gitremote/url}"

echo "[4/5] [DVC REMOTE    ] setting dvc remote to ${DVC_REMOTE_URL}"
dvc remote add myremote -f "${DVC_REMOTE_URL:-/tmp/dvcremote}"
dvc remote default myremote

echo "[5/5] [NEXT STEPS    ]"
echo "    Run:  \"sh ./test_script.sh\""
echo "    Verify with: git log"
echo "    To push artifacts: dvc push"
echo "    To push git project/code: git push origin"
echo "    See Neo4J Browser at: http://[HOST.IP.AD.DR]:7475/browser/"
