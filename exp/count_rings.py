import sys
import numpy as np
import argparse

from tqdm import tqdm
from data.data_loading import load_graph_dataset
from data.utils import get_rings

parser = argparse.ArgumentParser(description='SCN experiment.')
parser.add_argument('--dataset', type=str, default="ZINC",
                    help='dataset name (default: ZINC)')
parser.add_argument('--max_ring_size', type=int, default=12,
                    help='maximum ring size to look for')


def get_ring_stats(dataset, max_ring):
    keys = list(range(3, max_ring))
    ring_cards = {key: list() for key in keys}
    for graph in tqdm(dataset):
        rings = get_rings(graph.edge_index, max_k=max_ring-1)
        rings_per_graph = {key: 0 for key in keys}
        for ring in rings:
            k = len(ring)
            rings_per_graph[k] += 1
        for k in keys:
            ring_cards[k].append(rings_per_graph[k])
    return ring_cards


def combine_all_stats(*stats):
    all_stats = dict()

    for k in stats[0].keys():
        all_stats[k] = []

    for stat in stats:
        for k, v in stat.items():
            all_stats[k] += v
    return all_stats


def print_stats(stats):
    for k in stats:
        min = np.min(stats[k])
        max = np.max(stats[k])
        mean = np.mean(stats[k])
        med = np.median(stats[k])
        sum = np.sum(stats[k])
        nz = np.count_nonzero(stats[k])
        print(f'Ring {k:02d} => Min: {min:.3f}, Max: {max:.3f}, Mean:{mean:.3f}, Median: {med:.3f}, '
              f'Sum: {sum}, Non-zero: {nz}')


def exp_main(passed_args):
    args = parser.parse_args(passed_args)

    print('----==== {} ====----'.format(args.dataset))
    graph_list, train_ids, val_ids, test_ids, _ = load_graph_dataset(args.dataset)

    train = [graph_list[i] for i in train_ids]
    val = [graph_list[i] for i in val_ids]
    test = None
    if test_ids is not None:
        test = [graph_list[i] for i in test_ids]

    train_stats = get_ring_stats(train, args.max_ring_size)
    val_stats = get_ring_stats(val, args.max_ring_size)

    test_stats = None
    if test is not None:
        test_stats = get_ring_stats(test, args.max_ring_size)
        all_stats = combine_all_stats(train_stats, val_stats, test_stats)
    else:
        all_stats = combine_all_stats(train_stats, val_stats)

    print("=============== Train ================")
    print_stats(train_stats)
    print("=============== Validation ================")
    print_stats(val_stats)
    if test is not None:
        print("=============== Test ================")
        print_stats(test_stats)
    print("=============== Whole Dataset ================")
    print_stats(all_stats)


if __name__ == "__main__":
    passed_args = sys.argv[1:]
    exp_main(passed_args)
