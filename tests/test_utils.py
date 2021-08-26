"""Test utility functions."""
import unittest

import torch
from torch import testing

from song2vec import utils


class UtilsTestCase(unittest.TestCase):
    """Test utility functions and classes."""

    def test_tokenizer(self):
        """Test that the tokenizer works as expected."""
        vocab = {"a", "b", "c", "d"}
        encoder = utils.MultiHotEncoder(vocabulary=vocab)
        for value in vocab:
            self.assertEqual(encoder.vocabulary[encoder.indices[value]], value)

        data = [["a", "b"], ["c", "d"], []]
        encoded = encoder.encode(data)
        testing.assert_equal(
            torch.Tensor([[1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 0, 0]]), encoded.to_dense()
        )
        self.assertTrue(encoded.is_sparse)
