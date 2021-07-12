# Software Stack Performance Study
----------------------------------

The software in this repository is designed to aid in studing the performance of applications over various 
software stacks. A description of each directory is detailed below.


- scripts/
    - Bash, SLURM, and Python utilities for data collection and analysis.
- inputs/
    - Various input configurations for the different experiments. Mostly JSON files.
- data/
    - The data collected from the scripts.



## Case Study on Combinatorial Software Stacks
----------------------------------------------
This highlights how to build an application on a combination of software stacks and then run and profile each one.
First you need to define a list of available software in a json config file. An example of the default MPIs and 
compilers on Quartz is defined in [inputs/module-definitions/default-versions.json](inputs/module-definitions/default-versions.json).

Then you can use `scripts/generate-input-configs.py` to build the combination of experiments. Running
`./scripts/generate-input-configs.py -h` shows the available options for this script. It requires
an input software list and an app name to give to Spack.

The json file this outputs defines the list of experiments to run. `run-experiment.py` can
run these experiments. Running `./scripts/run-experiment.py` shows the available options for this script.
It requires an input experiment json (from `generate-input-configs.py`) and an output directory to
write results into. You should probably also provide `--spack-env` and `--profile`.

Once the jobs are finished (check with `squeue -u $USER`), then `analyze-combinatorial-data.py` can be used
to parse, preprocess, and clean the data. It can also output some basic plots. Running 
`./scripts/analyze-combinatorial-data.py -h` shows the available options for this script.
