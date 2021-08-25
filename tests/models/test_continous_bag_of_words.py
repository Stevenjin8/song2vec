"""Tests for the continous bag of words model."""
import torch
from torch import testing
import unittest
from song2vec.models.continous_bag_of_words import ContinousBagOfWords


class ContinousBagOfWordsTestCase(unittest.TestCase):
    """Tests for the continous bag of words model."""

    vocab_size: int
    embedding_dim: int
    model: ContinousBagOfWords

    def setUp(self):
        super().setUpClass()
        self.vocab_size = 2000
        self.embedding_dim = 2
        self.model = ContinousBagOfWords(
            vocab_size=self.vocab_size, embedding_dim=self.embedding_dim
        )

    def test_shapes(self):
        """Test the shape of the tensors in the model."""
        self.assertEqual(self.model.embeddings.in_features, self.vocab_size)
        self.assertEqual(self.model.embeddings.out_features, self.embedding_dim)
        self.assertIsNone(self.model.embeddings.bias)
        self.assertEqual(self.model.linear.in_features, self.embedding_dim)
        self.assertEqual(self.model.linear.out_features, self.vocab_size)
        self.assertIsNotNone(self.model.linear.bias)

    def test_forward(self):
        """Test that we can forward propogate."""
        num_examples = 50

        context = torch.rand(num_examples, self.vocab_size)
        output = self.model(context)
        self.assertEqual(output.shape, (num_examples, self.vocab_size))
        testing.assert_allclose(torch.ones(num_examples), torch.exp(output).sum(axis=1))

        context = context.to_sparse()
        output = self.model(context)
        self.assertEqual(output.shape, (num_examples, self.vocab_size))
        testing.assert_allclose(torch.ones(num_examples), torch.exp(output).sum(axis=1))
