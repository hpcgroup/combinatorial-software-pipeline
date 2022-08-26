from argparse import ArgumentParser
import re
import os
import pickle

class BuildData:
    def __init__(self, spec_hash, ymd, fom, time, valid):
        self.spec_hash = spec_hash 
        self.ymd = ymd
        self.figure_of_merit = fom 
        self.wall_time = time
        self.valid = valid

def get_args():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input-dir', type=str, help=' input directory with data files')
    parser.add_argument('-o', '--output-file', type=str, help='name of file to save pickle object to')
    return parser.parse_args()

def parse_file(fname, match):
    """ Parses a data file with given name
    This does thing
    Inputs:
        fname = string of data filename, of form {hash}-run-{YMD}-{HMS}.stdout
                where Y = 4 digits, M = 2 digits, D = 2 digits, and HMS are 
                all 2 digits, e.g:
                't5wiwpfkx4ojuqxnucwwszi4xnfnb7ut-run-20220824-165137.stdout'
    Outputs:
        BuildData object containing salient data
    """
    print('parsing {}'.format(fname))
    # If regex is given, then just use that, else get hash from filename
    if match:
        spec_hash = match.group(1)
        ymd = match.group(2)
    else:
        spec_hash = fname.split('-')[0]
        ymd = fname.split('-')[2]

    # Parse file for figure of merit
    found = False
    with open(fname) as f:
        lines = f.readlines()
        for line in lines:
            if line.find('Major kernels total rate') == 0:
                found = True
                fom = float(line.split(' ')[-1])

    valid = found
    if not found:
        fom = None
    # TODO GET WALLTIME INFO
    time = None

    return BuildData(spec_hash, ymd, fom, time, valid)

def parse_dir(dirname):
    datalist = []
    file_regex = re.compile('(\w+)-run-(\d+)-(\d+).stdout') 

    for f in os.listdir(dirname):
        match = re.match(file_regex, f)
        f = os.path.join(dirname, f)
        if os.path.isfile(f) and match:
            datalist.append(parse_file(f, match))

    return datalist

def main():
    args = get_args()
    datalist = parse_dir(args.input_dir)

    with open(args.output_file, 'wb') as f:
        pickle.dump(datalist, f)

if __name__ == "__main__":
    main()
