#!/bin/bash
##### These lines are for Slurm
#SBATCH -N 1
#SBATCH -t 8:00:00
#SBATCH -o /usr/workspace/synk1/combinatorial-software-pipeline/software-search/data_collection/data/laghos/20220828/quartz_laghos_hard.out

##### These are shell commands
./quartz-laghos-hard.py
