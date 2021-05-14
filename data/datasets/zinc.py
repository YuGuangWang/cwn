import pickle
import torch
import os.path as osp

from data.utils import convert_graph_dataset_with_rings
from data.datasets import InMemoryComplexDataset
from torch_geometric.datasets import ZINC


class ZincDataset(InMemoryComplexDataset):
    """This is ZINC from the Benchmarking GNNs paper. This is a graph regression task."""

    def __init__(self, root, max_ring_size, use_edge_features=False, transform=None,
                 pre_transform=None, pre_filter=None):
        self.name = 'ZINC'
        self._max_ring_size = max_ring_size
        self._use_edge_features = use_edge_features
        super(ZincDataset, self).__init__(root, transform, pre_transform, pre_filter,
                                          max_dim=2, cellular=True)

        self.data, self.slices, idx = self.load_dataset()
        self.train_ids = idx[0]
        self.val_ids = idx[1]
        self.test_ids = idx[2]

    @property
    def raw_file_names(self):
        name = self.name
        # The processed graph files are our raw files.
        # I've obtained this from inside the GNNBenchmarkDataset class
        return [f'{name}_train.pt', f'{name}_val.pt', f'{name}_test.pt']

    @property
    def processed_file_names(self):
        name = self.name
        return [f'{name}_complex.pt', f'{name}_idx.pt']

    def download(self):
        # Instantiating this will download and process the graph dataset.
        ZINC(self.raw_dir, subset=True)

    def load_dataset(self):
        """Load the dataset from here and process it if it doesn't exist"""
        print("Loading dataset from disk...")
        data, slices = torch.load(self.processed_paths[0])
        idx = torch.load(self.processed_paths[1])
        return data, slices, idx

    def process(self):
        # At this stage, the graph dataset is already downloaded and processed
        print(f"Processing simplicial complex dataset for {self.name}")
        train_data = ZINC(self.raw_dir, subset=True, split='train')
        val_data = ZINC(self.raw_dir, subset=True, split='val')
        test_data = ZINC(self.raw_dir, subset=True, split='test')

        data_list = []
        idx = []
        start = 0
        print("Converting the train dataset to a cell complex...")
        train_complexes, _, _ = convert_graph_dataset_with_rings(
            train_data,
            max_ring_size=self._max_ring_size,
            include_down_adj=self.include_down_adj,
            init_edges=self._use_edge_features,
            init_rings=False)
        data_list += train_complexes
        idx.append(list(range(start, len(data_list))))
        start = len(data_list)
        print("Converting the validation dataset to a cell complex...")
        val_complexes, _, _ = convert_graph_dataset_with_rings(
            val_data,
            max_ring_size=self._max_ring_size,
            include_down_adj=self.include_down_adj,
            init_edges=self._use_edge_features,
            init_rings=False)
        data_list += val_complexes
        idx.append(list(range(start, len(data_list))))
        start = len(data_list)
        print("Converting the test dataset to a cell complex...")
        test_complexes, _, _ = convert_graph_dataset_with_rings(
            test_data,
            max_ring_size=self._max_ring_size,
            include_down_adj=self.include_down_adj,
            init_edges=self._use_edge_features,
            init_rings=False)
        data_list += test_complexes
        idx.append(list(range(start, len(data_list))))

        path = self.processed_paths[0]
        print(f'Saving processed dataset in {path}....')
        torch.save(self.collate(data_list, 2), path)
        
        path = self.processed_paths[1]
        print(f'Saving idx in {path}....')
        torch.save(idx, path)

    @property
    def processed_dir(self):
        """Overwrite to change name based on edges"""
        directory = super(ZincDataset, self).processed_dir
        suffix1 = f"_{self._max_ring_size}rings" if self._cellular else ""
        suffix2 = "-E" if self._use_edge_features else ""
        return directory + suffix1 + suffix2
