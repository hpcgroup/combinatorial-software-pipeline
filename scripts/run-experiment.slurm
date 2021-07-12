#!/bin/bash

# This script will run applications as described by the provided environment
# variables. It is intended for use by the 'run-experiment.py' script.
# author: Daniel Nichols
# date: July 2021


# EXTERNAL ENVIRONMENT VARIABLES
# SPACK_ENV_NAME - environment to use
# SPACK_SPEC - spec to load to run application
# PROFILE - 1 to profile with HPCTOOLKIT, 0 to not profile
# APP_NAME - name of application to run (assumed in path)
# APP_ARGS - input arguments to application
# SRC_DIR - source code of application
# MODULE_LIST - modules to load
# OUTPUT_ROOT - root to write output info
# EXPERIMENT_JSON - json experiment string
# CSV_FILE - path to csv file


# GENERATE METADATA
/bin/hostname
srun -l /bin/hostname
srun -l /bin/pwd


# SOURCE UTILITIES
source /usr/WS1/dnicho/software-performance-study/scripts/utilities.bash


# LOAD MODULES
printf "Loading modules '%s'.\n" "${MODULE_LIST}"
module --force purge
module load StdEnv ${MODULE_LIST}

if [ ${PROFILE} -eq 1 ]; then
    module load hpctoolkit/2021.05
fi


# ACTIVATE SPACK ENVIRONMENT AND LOAD SPAC
spack env deactivate > /dev/null 2>&1
spack env activate ${SPACK_ENV_NAME}
spack load ${SPACK_SPEC}


# HPCTOOLKIT RELATED FLAGS
HPCTOOLKIT_OUPUT_ROOT="${OUTPUT_ROOT}/hpctoolkit-dbs"
HPCTOOLKIT_MEAS_DIR="${HPCTOOLKIT_OUPUT_ROOT}/measurements-${SLURM_JOB_ID}"
HPCTOOLKIT_DB_DIR="${HPCTOOLKIT_OUPUT_ROOT}/database-${SLURM_JOB_ID}"
HPCTOOLKIT_STRUCT_FILE="${HPCTOOLKIT_OUPUT_ROOT}/${APP_NAME}-${SLURM_JOB_ID}.hpcstruct"
HPCTOOLKIT_EVENTS="-e CPUTIME@5000"


# CREATE HPCTOOLKIT DIRECTORIES
mkdir -p ${HPCTOOLKIT_OUPUT_ROOT}


# MAKE HPCSTRUCT FILE
if [ ${PROFILE} -eq 1 ]; then
    hpcstruct `which ${APP_NAME}` -I "${SRC_DIR}/*" --output ${HPCTOOLKIT_STRUCT_FILE}
fi


# RUN APPLICATION
BEGIN=$(timestamp)
if [ ${PROFILE} -eq 1 ]; then
    printf "Profiling '%s'.\n" "${APP_NAME}"
    srun -n ${SLURM_NTASKS} \
        hpcrun ${HPCTOOLKIT_EVENTS} --output ${HPCTOOLKIT_MEAS_DIR} \
            ${APP_NAME} ${APP_ARGS}
else
    printf "Running '%s'.\n" "${APP_NAME}"
    srun -n ${SLURM_NTASKS} ${APP_NAME} ${APP_ARGS}
fi
END=$(timestamp)
DURATION="$(diff_minutes ${BEGIN} ${END})"


# PARSE PROFILE
if [ ${PROFILE} -eq 1 ]; then
    printf "Parsing profile '%s' into database '%s'.\n" "${HPCTOOLKIT_MEAS_DIR}" "${HPCTOOLKIT_DB_DIR}"
    srun -n ${SLURM_NTASKS} \
        hpcprof-mpi -I "${SRC_DIR}/+" -S ${HPCTOOLKIT_STRUCT_FILE} --metric-db yes \
            --output ${HPCTOOLKIT_DB_DIR} ${HPCTOOLKIT_MEAS_DIR}
fi


# CLEAN UP
printf "Cleaning up.\n"
if [ ${PROFILE} -eq 1 ]; then
    rm -r ${HPCTOOLKIT_MEAS_DIR}
    rm ${HPCTOOLKIT_STRUCT_FILE}
fi


# WRITE OUTPUT
# write out CSV as described in `FORMAT.md`
# columns:
# application,job_id,ranks,input,start_time,duration,input_config,hpctoolkit_path

if [ ${PROFILE} -ne 1 ]; then
    HPCTOOLKIT_DB_DIR="\"\""
fi

printf "Appending '"
printf "%s,%s,%s,\"%s\",\"%s\",%s,\"%s\",\"%s\"" "${APP_NAME}" "${SLURM_JOB_ID}" "${SLURM_NTASKS}" "${APP_ARGS}" \
    "${BEGIN}" "${DURATION}" "${EXPERIMENT_JSON}" "${HPCTOOLKIT_DB_DIR}"
printf "' to '%s'.\n" "${CSV_FILE}"

printf "%s,%s,%s,\"%s\",\"%s\",%s,\"%s\",\"%s\"\n" "${APP_NAME}" "${SLURM_JOB_ID}" "${SLURM_NTASKS}" "${APP_ARGS}" \
    "${BEGIN}" "${DURATION}" "${EXPERIMENT_JSON}" "${HPCTOOLKIT_DB_DIR}"  >> ${CSV_FILE}
