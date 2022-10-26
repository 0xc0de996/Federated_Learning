from torchvision.datasets import MNIST
from torchvision.transforms import Compose, ToTensor, Normalize

from . import Data


class Mnist(Data):
    def __init__(self, n_clients, batch_size, path, alpha=100, plot_path=None, flag=False):
        super().__init__(plot_path)
        transform = Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])
        self.train_set = MNIST(root=path, train=True, transform=transform)
        self.validate_set = MNIST(root=path, train=False, transform=transform)
        self.trainLoader, self.client_nums, self.total = \
            self.train_loader(alpha, n_clients, batch_size, flag)
        self.validationLoader = self.validate_loader(batch_size)

    def __str__(self):
        return "MNIST"
