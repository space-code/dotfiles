#!/usr/bin/env bash

#
#  dotfiles - bootstrap.sh
#  Copyright © 2025 Space Code. All rights reserved.
#
#  This script synchronizes the dotfiles from the repository to the user's
#  home directory. It uses rsync to copy configuration files and then
#  sources the .bash_profile to apply changes.
#

# Navigate to the directory where the script is located
cd "$(dirname "${BASH_SOURCE[0]}")" || exit

# Pull the latest changes from the main branch
git pull origin main

# Function to update the home directory with the dotfiles
update() {
    # rsync parameters:
    # -a: archive mode (preserves permissions, symlinks, etc.)
    # -v: verbose output
    # -h: human-readable numbers
    # --no-perms: do not preserve permissions (useful for cross-OS sync)
    # --exclude: skip files that should not be in the home directory
    rsync --exclude ".git/" \
          --exclude ".DS_Store" \
          --exclude "bootstrap.sh" \
          --exclude "README.md" \
          --exclude "LICENSE" \
          -avh --no-perms . ~
          
    # Reload the bash profile to apply environment changes immediately
    source ~/.bash_profile
}

# Check if the --force or -f flag is provided to skip the confirmation prompt
if [[ "$1" == "--force" || "$1" == "-f" ]]; then
    update
else
    # Ask the user for confirmation before overwriting files in the home directory
    read -rp "This may overwrite existing files in your home directory. Are you sure? (y/n) " response
    echo
    if [[ "$response" =~ ^[Yy]$ ]]; then
        update
    fi
fi

# Clean up the update function from the shell environment
unset -f update
