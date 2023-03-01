#!/bin/bash

git init -q
git checkout -q -b master
cur_dir=$(pwd)
head_dir="$cur_dir/.git/refs/heads"
if [ "$(ls -A $head_dir)" ]
then
  true
else
  git commit -q --allow-empty -n -m "Initial code commit"
fi
git remote add cmf_origin $1
