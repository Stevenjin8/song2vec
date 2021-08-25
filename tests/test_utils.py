"""Test utility functions."""
import unittest
import torch
from song2vec import utils
from torch import testing


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

    def test_create_data(self):
        """Test that we can create data."""
        data = (
            torch.Tensor([[1, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0]])
            .to_sparse()
            .coalesce()
        )
        X, y = utils.create_data_masks(data)
        expected_X = torch.Tensor([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]])
        expected_y = torch.Tensor([0, 1, 2])
        self.assertTrue(X.is_sparse)
        testing.assert_equal(X.to_dense(), expected_X)
        testing.assert_equal(y, expected_y)
