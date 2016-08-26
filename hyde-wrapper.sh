#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV="$DIR/env"
mkdir -p $ENV

env_name="hyde-env"

# Check the git hash of when the virtualenv was created.
# If it differs, wipe and reinitialize, saving a new hash.
pushd "$DIR"
git_hash=$(git rev-parse HEAD)
popd
hash_file="$ENV/$env_name/git-hash"
if [[ ! -e "$hash_file" || "$git_hash" != "$(cat $hash_file)" ]]; then
    echo "Initializing virtualenv"
    pushd "$ENV"
    virtualenv "$env_name"
    for package in "django==1.6.11" "markdown==2.6.6" "pyYAML==3.11" "cherrypy==7.1.0" "pygments==1.5" "cssmin==0.2.0"; do
        "./$env_name/bin/pip" install $package
    done
    virtualenv --relocatable "$env_name"
    echo "$git_hash" > "$hash_file"
    popd
fi

# Activate the virtualenv
source "$ENV/$env_name/bin/activate"

# Execute
exec "$DIR/hyde.py" "$@"
