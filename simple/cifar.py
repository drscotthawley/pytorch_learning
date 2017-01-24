import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.autograd import Variable

# cuda setting(s)
cuda = False
if torch.cuda.is_available():
    cuda = True

# variables
batch_size = 128
epochs = 100

# load data
transform=transforms.Compose([transforms.ToTensor(),
                              transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                             ])
train_loader = torch.utils.data.DataLoader(
    datasets.CIFAR10('data/cifar10', train=True, download=True,
                   transform=transform),
    batch_size=batch_size, shuffle=True)
test_loader = torch.utils.data.DataLoader(
    datasets.CIFAR10('data/cifar10', train=False, transform=transform),
    batch_size=batch_size, shuffle=True)


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=32,
                               kernel_size=5,
                               stride=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3)
        self.conv2_bn = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3)
        self.conv3_bn = nn.BatchNorm2d(64)
        self.dense1 = nn.Linear(in_features=4 * 64, out_features=256)
        self.dense1_bn = nn.BatchNorm1d(256)
        self.dense2 = nn.Linear(256, 64)
        self.dense3 = nn.Linear(64, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_bn(self.conv2(x)), 2))
        x = F.relu(F.max_pool2d(self.conv3_bn(self.conv3(x)), 2))
        x = x.view(-1, 4 * 64) #reshape
        x = F.relu(self.dense1_bn(self.dense1(x)))
        x = F.relu(self.dense2(x))
        x = F.log_softmax(self.dense3(x))
        return x

model = Net()
if cuda:
    model.cuda()

optimizer = optim.Adam(model.parameters(),
                       lr=1e-3)


def train(epoch):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        if cuda:
            data, target = data.cuda(), target.cuda()
        data, target = Variable(data), Variable(target)
        optimizer.zero_grad() # reset reset optimizer
        output = model(data)
        loss = F.nll_loss(output, target) # negative log likelihood loss
        loss.backward() # backprop
        optimizer.step()
        if batch_idx % 100 == 0:
            print('\rTrain Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                100 * batch_idx / len(train_loader), loss.data[0]), end='')


def test(epoch):
    model.eval()
    test_loss = 0
    correct = 0
    for data, target in test_loader:
        if cuda:
            data, target = data.cuda(), target.cuda()
        data, target = Variable(data), Variable(target)
        output = model(data)
        test_loss += F.nll_loss(output, target).data[0]
        pred = output.data.max(1)[1]  # get the index of the max log-probability
        correct += pred.eq(target.data).cpu().sum()

    test_loss /= len(test_loader)  # loss function already averages over batch size
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100 * correct / len(test_loader.dataset)))
    return test_loss

loss = []
for i in range(1, epochs + 1):
    train(i)
    loss.append(test(i))


import matplotlib.pyplot as plt
plt.style.use('ggplot')
plt.plot(range(1, epochs+1), loss)
plt.savefig("loss.png")