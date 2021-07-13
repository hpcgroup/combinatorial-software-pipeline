#!/bin/bash

# This script will build applications as described by the provided environment
# variables. It is intended for use by the 'run-experiment.py' script.
# author: Daniel Nichols
# date: July 2021


# generate metadata
/bin/hostname
srun -l /bin/hostname
srun -l /bin/pwd

# EXTERNAL ENV VARIABLES
# SPACK_ENV_NAME - spack environment to install in. Assumes it exists.

# step into spack environment
spack env deactivate > /dev/null 2>&1
spack env activate ${SPACK_ENV_NAME}

# compiler find and external find
spack compiler find
spack external find

echo "Concretizing."
spack concretize --force

echo "Installing."
spack install --yes-to-all --no-checksum --source

echo "Done."
