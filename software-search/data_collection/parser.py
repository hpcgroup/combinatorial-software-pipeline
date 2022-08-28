# File for parsing build experiment data
from argparse import ArgumentParser
import re
import os
import json

def get_args():
    """ Gets command-line arguments for main
    """
    parser = ArgumentParser()
    parser.add_argument('-i', '--input-dir', type=str, help=' input directory with data files')
    parser.add_argument('-o', '--output-file', type=str, help='name of file to save pickle object to')
    return parser.parse_args()

#TODO this function only works for specific laghos files, not a general
#     experiment, so it should probably be named accordingly
def parse_file(fname, match):
    """ Parses a single stdout file from a laghos experiment run
    Before being passed to parse_file, the name of the file was matched against
    a regex.

    Inputs:
        fname = string of data file name, of form described in parse_dir
        match = match groups of filename regex. group 1 is hash, group 2 ymd
    """
    data = {}

    # If regex is given, then just use that, else get hash from filename
    if match:
        data['hash'] = match.group(1)
        data['ymd'] = match.group(2)
    else:
        data['hash'] = fname.split('-')[0]
        data['ymd'] = fname.split('-')[2]

    # Parse file for figure of merit
    found = False
    with open(fname) as f:
        lines = f.readlines()
        for line in lines:
            if line.find('Major kernels total rate') == 0:
                found = True
                data['figure_of_merit'] = float(line.split(' ')[-1])

    valid = found
    if not found:
        data['figure_of_merit'] = None
    # TODO GET WALLTIME INFO
    time = None

    return data

def parse_dir(dirname):
    """ Parses a directory containing data files
    Scripts in test_scripts generate different builds of the same application. 
    For each build, the corresponding exectuable is ran, and its stdout is 
    written to a file.

    This function iterates over those files and returns a list of json objects.
    list of json objects. It matches each file against a regex and passes the
    match groups (along with the file itself) to parse_file

    Inputs:
        dirname = path to directory containing .stdout files of the form:
                  {hash}-run-{YMD}-{HMS}.stdout
                  Y = 4 digits, M = 2 digits, D = 2 digits. HMS all 2 digits,e.g
                  't5wiwpfkx4ojuqxnucwwszi4xnfnb7ut-run-20220824-165137.stdout'
                  (See get_commands_using_api in runner.py to see how files are
                  generated)
    Outputs:
        datalist = list of json objects containing salient data
    """
    datalist = []
    file_regex = re.compile('(\w+)-run-(\d+)-(\d+).stdout') 

    for f in os.listdir(dirname):
        match = re.match(file_regex, f)
        f = os.path.join(dirname, f)
        if os.path.isfile(f) and match:
            datalist.append(parse_file(f, match))

    return datalist

def write_data(datalist, outfile):
    with open(outfile, 'w') as fp:
        json.dump(datalist, fp, indent=0)

def main():
    args = get_args()
    datalist = parse_dir(args.input_dir)
    write_data(datalist, args.output_file)

if __name__ == "__main__":
    main()
