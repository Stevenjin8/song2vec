"""Continous bag of words model."""
from typing import Tuple
import torch
from torch import Tensor
import torch.nn as nn
import torch.nn.functional as F


class ContinousBagOfWords(nn.Module):
    r"""Vanilla continous bag of words model. This model differs slightly from
    a traditional CBOW model because the context can be infinitely large. Instead of
    summing vectors in the context, we take the average:

    .. math::
        h = \frac1{|C|} \sum\limits_{v \in C} v
        p( w | C ) = A(h + b)

    where :code:`embeddings` contain the word vectors, and :math:`A` and :math:`b` are
    the weights and biases of :code:`linear`.

    Attributes:
        vocab_size: the size of the vocab.
        embedding_dim: the dimensionality of the latent space.
        embeddings: layer with embeddings.
        linear: layer with prediction weights.
        ones: an array of ones to use to get row-wise sums.

    We can't use an embedding layer because they require a fixed input size.
    """
    vocab_size: int
    embedding_dim: int
    embeddings: nn.Linear
    linear: nn.Linear
    log_softmax: nn.LogSoftmax
    loss: nn.NLLLoss
    ones: Tensor

    def __init__(self, vocab_size: int, embedding_dim: int):
        """Initialize an instance of the class.

        Attrbutes:
            See class docstring."""
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.embeddings = nn.Linear(vocab_size, embedding_dim, bias=False)
        self.loss = nn.NLLLoss()
        self.log_softmax = nn.LogSoftmax(dim=1)
        self.linear = nn.Linear(embedding_dim, vocab_size, bias=True)
        self.ones = torch.ones(vocab_size, 1)  # pylint: disable=no-member

    def forward(self, context: Tensor) -> Tensor:
        """Find the probability of each word given a tensor.

        Arguments:
            context: multi-hot encoded tensor with each row representing a data point
                and each column representing whether a token is present in the
                corresponding context.

        Returns:
            The log probability distribution of tokens given a context.
        """
        # The `sum` method doesn't work for sparse tensors.
        context_mean = self.embeddings(context) / (context @ self.ones)
        probs = self.log_softmax(self.linear(context_mean), dim=1)
        return probs

    def create_batch(self, data_point: Tensor) -> Tuple[Tensor, Tensor]:
        """Create a batch of data given a bag."""
        indices = data_point.indices()
        num_batch_indices = indices.shape[1]
        y = indices[0]
        hidden_value_indices = torch.vstack(torch.arange(0, num_batch_indices), y)
        embeddings = self.embeddings(data_point) - self.embeddings(hidden_value_indices)
        embeddings = embeddings / (num_batch_indices - 1)

        return embeddings, y

    def training_step(self, train_batch, batch_idx) -> float:
        assert len(train_batch) == 1
        data_point = train_batch[0]
        embeddings, y = self.create_batch(data_point=data_point)
        preds = self.log_softmax(embeddings, axis=1)
        return self.loss(preds, y)
