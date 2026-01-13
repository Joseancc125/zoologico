import argparse
import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP


class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Flatten(), nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 2))

    def forward(self, x):
        return self.net(x)


def setup(rank, world_size):
    dist.init_process_group('gloo', rank=rank, world_size=world_size)


def cleanup():
    dist.destroy_process_group()


def train(rank, world_size, epochs=3):
    setup(rank, world_size)
    torch.manual_seed(0)
    model = SimpleModel().to(rank)
    ddp_model = DDP(model, device_ids=None)

    optimizer = optim.SGD(ddp_model.parameters(), lr=0.01)
    for epoch in range(epochs):
        # datos sintéticos
        x = torch.randn(8, 32)
        y = torch.randint(0, 2, (8,))
        outputs = ddp_model(x)
        loss = nn.functional.cross_entropy(outputs, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if rank == 0:
            print(f'Epoch {epoch} loss {loss.item():.4f}')
        time.sleep(0.1)

    cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rank', type=int, default=0)
    parser.add_argument('--world_size', type=int, default=1)
    parser.add_argument('--epochs', type=int, default=3)
    args = parser.parse_args()
    train(args.rank, args.world_size, args.epochs)
