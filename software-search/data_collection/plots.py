from argparse import ArgumentParser
import json
import matplotlib.pyplot as plt
import numpy as np

def get_args():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input-file', type=str, help='json file containing data')
    parser.add_argument('-o', '--output-file', type=str, help='output filename to save figure')
    return parser.parse_args()

def remove_none(data_json):
    data_json_none_removed = []
    for build in data_json:
        if build['time']:
            data_json_none_removed.append(build)
    return data_json_none_removed

def generate_plot(data_json, output_filename):
    plt.rcdefaults()
    fig, ax = plt.subplots()
    data_json_none_removed = remove_none(data_json)
    y_pos = np.arange(len(data_json_none_removed))
    times = [build['time'] for build in data_json_none_removed]
    specs = ['{} + {}'.format(build['compiler'], build['mpi']) for build in data_json_none_removed]

    ax.barh(y_pos, times, height=0.8)
    ax.set_yticks(y_pos, labels=specs)
    ax.invert_yaxis()
    ax.tick_params(axis='y', labelsize='large')
    ax.set_xlabel('Major Kernels Total Time', fontsize='large')
    ax.set_title('Laghos Performance Data Across Build Configurations')
    fig.set_size_inches(26, 14)
    plt.savefig(output_filename)

def main():
    args = get_args()
    with open(args.input_file) as fp:
        data_json = json.load(fp)
        generate_plot(data_json, args.output_file)

if __name__ == "__main__":
    main()
