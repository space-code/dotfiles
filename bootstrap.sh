#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE[0]}")" || exit

git pull origin main

update() {
    rsync --exclude ".git/" \
          --exclude ".DS_Store" \
          --exclude "bootstrap.sh" \
          --exclude "README.md" \
          --exclude "LICENSE" \
          -avh --no-perms . ~
    source ~/.bash_profile
}

if [[ "$1" == "--force" || "$1" == "-f" ]]; then
    update
else
    read -rp "This may overwrite existing files in your home directory. Are you sure? (y/n) " response
    echo
    if [[ "$response" =~ ^[Yy]$ ]]; then
        update
    fi
fi

unset -f update
