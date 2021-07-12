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
compilers on Quartz is:

```json
{
    "mpi": [
        {
            "name": "mvapich2",
            "version": "2.3",
            "module": "mvapich2/2.3"
        },
        {
            "name": "openmpi",
            "version": "4.1.0",
            "module": "openmpi/4.1.0"
        }
    ],
    "compiler": [
        {
            "name": "intel",
            "version": "19.0.4.227",
            "module": "intel/19.0.4"
        },
        {
            "name": "gcc",
            "version": "4.9.3",
            "module": "gcc/4.9.3"
        },
        {
            "name": "clang",
            "version": "6.0.0",
            "module": "clang/6.0.0"
        }
    ]
}
```

Then you can use `scripts/generate-input-configs.py` to build the combination of experiments. The
options for this script are as follows:

```man
arguments:
  -h, --help            show this help message and exit
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbosity. 1 for just important output, 2 for full
                        output. No args defaults to 1.
  -o OUTPUT, --output OUTPUT
                        Where to output json data. If - is given, then the
                        script outputs to stdout.
  -i INPUT, --input INPUT
                        List of softwares to enumerate in json file.
  -j JOIN, --join JOIN  Join with an existing list of json executables.
  -r [RANKS [RANKS ...]], --ranks [RANKS [RANKS ...]]
                        Number of ranks to run each experiment.
  --input-problems [INPUT_PROBLEMS [INPUT_PROBLEMS ...]]
                        Commmand line args to run application.
  -a APP, --app APP     Spack spec of application to run.
  --app-name APP_NAME   Shorthand name for application if different than
                        basename in -a.
  --max-wall-time MAX_WALL_TIME
                        Define the max wall time to pass to SLURM when running
                        each application.
```

The json file this outputs defines the list of experiments to run. `run-experiment.py` can
run these experiments. It can be called with the following arguments:

```
arguments:
  -h, --help            show this help message and exit
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbosity. 1 for just important output, 2 for full
                        output. No args defaults to 1.
  -i INPUT, --input INPUT
                        Experiments json file.
  --sync                Submit jobs without dependencies, so that they
                        can/might run asynchronously.
  --collate             Submit jobs with same resources requirements as job
                        array.
  --ranks-per-node RANKS_PER_NODE
                        Run with this many ranks per node.
  --build-script BUILD_SCRIPT
                        The script used to build dependencies.
  --run-script RUN_SCRIPT
                        The script used to run jobs.
  --max-build-time MAX_BUILD_TIME
                        Max amount of time to spend in build script.
  --profile             Record HPCToolkit profiles.
  --output-root OUTPUT_ROOT
                        Root directory to put output information into.
  --spack-env SPACK_ENV
                        Spack environment to use for installs.
  --csv-file CSV_FILE   Name of csv file to write out data into.
```

Here `-i` and `--output-root` are required. You should probably also provide `--spack-env`
and `--profile`.

