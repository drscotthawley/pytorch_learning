# This is a PyTorch version of [lstm_text_generation.py](https://github.com/fchollet/keras/blob/master/examples/lstm_text_generation.py)
# in keras example using GRU instead of LSTM.

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.autograd import Variable

# variables
file_name = "1984.txt"
maxlen = 50
step = 3
hidden_size = 256
batch_size = 16

# cuda setting
cuda = False
if torch.cuda.is_available():
    cuda = True

# functions


def var(x):
    x = Variable(x)
    if cuda:
        return x.cuda()
    else:
        return x


def sample(preds, size, temperature=1.0):
    # helper function to sample an index from a probability array
    preds = preds.cpu()
    preds = torch.log(preds)/temperature
    exp_preds = torch.exp(preds)
    preds = exp_preds / torch.sum(exp_preds)
    probas = torch.multinomial(preds, size)
    return torch.max(probas, 1)


class Net(nn.Module):
    def __init__(self, features, cls_size):
        super(Net, self).__init__()
        self.rnn1 = nn.GRU(input_size=features,
                            hidden_size=hidden_size,
                            num_layers=1)
        self.dense1 = nn.Linear(hidden_size, cls_size)

    def forward(self, x, hidden):
        x, hidden = self.rnn1(x, hidden)
        x = x.select(0, maxlen-1).contiguous()
        x = x.view(-1, hidden_size)
        x = F.softmax(self.dense1(x))
        return x, hidden

    def init_hidden(self, batch_size=batch_size):
        weight = next(self.parameters()).data
        return Variable(weight.new(1, batch_size, hidden_size).zero_())

# ---
raw_text = ""
with open(file_name) as f:
    raw_text = f.read().lower()
print("corpus size: {}".format(len(raw_text)))

chars = sorted(list(set(raw_text)))
print("corpus has {} chars".format(len(chars)))
char_indices = dict((c, i) for i, c in enumerate(chars))
indices_char = dict((i, c) for i, c in enumerate(chars))

sentences = []
next_chars = []
for i in range(0, len(raw_text) - maxlen, step):
    sentences.append(raw_text[i: i + maxlen])
    next_chars.append(raw_text[i + maxlen])
print('nb sequences:', len(sentences))

print('Vectorization...')
X = np.zeros((maxlen, len(sentences), len(chars)))
# y = np.zeros((len(sentences), len(chars)), dtype=np.int)
y = np.zeros((len(sentences)), dtype=np.int)
for i, sentence in enumerate(sentences):
    for t, char in enumerate(sentence):
        X[t, i, char_indices[char]] = 1
    y[i] = char_indices[next_chars[i]]

features = len(chars)

print("Building the Model")
model = Net(features=features, cls_size=len(chars))
if cuda:
    model.cuda()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=7e-4)


def train():
    model.train()
    hidden = model.init_hidden()
    for epoch in range(len(sentences) // batch_size):
        X_batch = var(torch.FloatTensor(X[:, epoch*batch_size: (epoch+1)*batch_size, :]))
        y_batch = var(torch.LongTensor(y[epoch*batch_size: (epoch+1)*batch_size]))
        model.zero_grad()
        output, hidden = model(X_batch, var(hidden.data))
        loss = criterion(output, y_batch)
        loss.backward()
        optimizer.step()
    print("\r{}".format(loss.data[0]), end="")


def test(x, hidden):
    model.eval()
    model.zero_grad()
    output, hidden = model(x, var(hidden.data))
    return output, hidden


def main():
    for epoch in range(0, 30):
        train()

    for epoch in range(1, 60):
        print("epoch: {}".format(epoch))
        train()
        print("\n---")

        start_index = random.randint(0, len(raw_text) - maxlen - 1)
        generated = ''
        sentence = raw_text[start_index: start_index + maxlen]
        generated += sentence
        print(sentence + "---")
        hidden = model.init_hidden(1)

        for i in range(400):
            x = np.zeros((maxlen, 1, len(chars)))
            for t, char in enumerate(sentence):
                x[t, 0, char_indices[char]] = 1
            x = var(torch.FloatTensor(x))
            pred, hidden = test(x, hidden)
            next_idx = sample(pred.data, features, 1.2)
            next_idx = int(next_idx[1].sum())
            next_char = indices_char[next_idx]
            generated += next_char
            sentence = sentence[1:] + next_char
            print(next_char, end="")
        print()


if __name__ == '__main__':
    main()