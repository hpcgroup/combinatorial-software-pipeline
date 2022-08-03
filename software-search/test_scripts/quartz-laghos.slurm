#!/bin/tcsh
##### These lines are for Slurm
#SBATCH -N 1
#SBATCH -t 8:00:00
#SBATCH -o 

##### These are shell commands
./quartz-laghos-hard.py
