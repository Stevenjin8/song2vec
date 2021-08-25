"""Utility functions and classes."""
from typing import Tuple, Dict, Hashable, Iterable, List
from tqdm import tqdm
import torch


class MultiHotEncoder:
    """Encode values into multi hot encodings.

    Attributes:
        vocabulary: Sorted list of the vocabulary.
        indicies: Quick lookup for indices of each item in the vocabulary.
    """

    vocabulary: List[Hashable]
    indices: Dict[Hashable, int]

    def __init__(self, vocabulary: Iterable[Hashable]):
        """Initiate an instance of the class.

        Arguments:
            See class docstring
        """
        self.vocabulary = sorted(set(vocabulary))  # remove duplicates and sort
        self.indices = {t: i for i, t in enumerate(self.vocabulary)}

    def encode(self, token_lists: List[List[Hashable]]) -> torch.Tensor:
        """Take a list of list of tokens and multihot encode them.

        Arguments:
            token_lists: the decoded data.

        Returns:
            A `len(token_lists) x len(self.vocabulary)` multihot encoded tensor.
        """
        num_indices = sum(map(len, token_lists))
        indices = torch.zeros(2, num_indices)

        current_index = 0
        for i, x_i in enumerate(tqdm(token_lists)):
            for t in x_i:
                indices[0][current_index] = i
                indices[1][current_index] = self.indices[t]
                current_index += 1

        values = torch.ones(num_indices)
        return torch.sparse_coo_tensor(
            indices=indices,
            values=values,
            size=(len(token_lists), len(self.vocabulary)),
        )
