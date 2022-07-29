#!/bin/bash
##### These lines are for Slurm
#SBATCH -N 1
#SBATCH -J synk1_quartz_test
#SBATCH -p pbatch
#SBATCH -o /usr/workspace/synk1/combinatorial-software-pipeline/software-search/quartz-test-outputdir/slurm_job_output

python3 quartz-test-easy.py --spack-env spack_env
