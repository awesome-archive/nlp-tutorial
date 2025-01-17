import matplotlib.pyplot as plt
plt.switch_backend('agg')
import matplotlib.ticker as ticker
import numpy as np
import random
import time
import math
import dataLoader as loader
import seq2seq
import torch
import torch.nn as nn
from torch import optim

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def indexesFromSentence(lang, sentence):
    return [lang.word2index[word] for word in sentence.split(' ')]

def tensorFromSentence(lang, sentence):
    indexes = indexesFromSentence(lang, sentence)
    indexes.append(loader.EOS_token)
    return torch.tensor(indexes, dtype=torch.long, device=device).view(-1, 1)

def tensorsFromPair(pair):
    input_tensor = tensorFromSentence(input_lang, pair[0])
    target_tensor = tensorFromSentence(output_lang, pair[1])
    return (input_tensor, target_tensor)

def asMinutes(s):
    m = math.floor(s / 60)
    s -= m * 60
    return '%dm %ds' % (m, s)

def timeSince(since, percent):
    now = time.time()
    s = now - since
    es = s / (percent)
    rs = es - s
    return '%s (- %s)' % (asMinutes(s), asMinutes(rs))

def showPlot(points):
    plt.figure()
    fig, ax = plt.subplots()
    # this locator puts ticks at regular intervals
    loc = ticker.MultipleLocator(base=0.2)
    ax.yaxis.set_major_locator(loc)
    plt.plot(points)

def merge_encoder_hiddens(encoder_hiddens):
    new_hiddens = []
    new_cells = []
    hiddens, cells = encoder_hiddens
    # |hiddens|, |cells| = (2, 1, hidden_size/2)
    
    # i-th and (i+1)-th layer is opposite direction.
    # Also, each direction of layer is half hidden size.
    # Therefore, we concatenate both directions to 1 hidden size layer.
    for i in range(0, hiddens.size(0), 2):
        new_hiddens += [torch.cat([hiddens[i], hiddens[i+1]], dim =-1)]
        new_cells += [torch.cat([cells[i], cells[i+1]], dim = -1)]
        # |torch.cat([hiddens[i], hiddens[i+1]], dim =-1)| =  (1, hidden_size)
        # |torch.cat([cells[i], cells[i+1]], dim = -1)| =  (1, hidden_size)
    
    new_hiddens, new_cells = torch.stack(new_hiddens), torch.stack(new_cells)
    # |new_hiddens| = (1, 1, hidden_size)
    # |new_cells| = (1, 1, hidden_size)

    return (new_hiddens, new_cells)

def train(input_tensor, target_tensor, encoder, decoder, encoder_optimizer, decoder_optimizer,
            criterion, max_length=loader.MAX_LENGTH):

    encoder_optimizer.zero_grad()
    decoder_optimizer.zero_grad()

    input_length = input_tensor.size(0)
    target_length = target_tensor.size(0)
    # |input_length|, |target_length| = (sentence_length)

    encoder_hidden = (encoder.initHidden().to(device), encoder.initHidden().to(device))
    # |encoder_hidden[0]|, |encoder_hidden[1]| = (2, 1, hidden_size/2)
    encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)
    # |encoder_outputs| = (max_length, hidden_size)

    loss = 0
    for ei in range(input_length):
        encoder_output, encoder_hidden = encoder(input_tensor[ei], encoder_hidden)
        # |encoder_output| = (1, 1, hidden_size)
        # |encoder_hidden[0]|, |encoder_hidden[1]| = (2, 1, hidden_size/2)
        encoder_outputs[ei] = encoder_output[0, 0]
    
    decoder_input = torch.tensor([[loader.SOS_token]], device=device)
    decoder_hidden = merge_encoder_hiddens(encoder_hidden)
    # |decoder_input| = (1, 1)
    # |decoder_hidden[0]|, |decoder_hidden[1]| = (1, 1, hidden_size), (1, 1, hidden_size)

    use_teacher_forcing = True if random.random() < teacher_forcing_ratio else False
    if use_teacher_forcing:
        # Teacher forcing: feed the target as the next input
        for di in range(target_length):
            decoder_output, decoder_hidden = decoder(decoder_input, decoder_hidden)
            # |decoder_output| = (1, output_lang.n_words)
            # |decoder_hidden[0]|, |decoder_hidden[1]| = (1, 1, hidden_size)

            loss += criterion(decoder_output, target_tensor[di])
            decoder_input = target_tensor[di] # teacher forcing
            # |target_tensor[di]|, |decoder_input| = (1)
    else:
        # Without teacher forcing: use its own predictions as the next input
        for di in range(target_length):
            decoder_output, decoder_hidden = decoder(decoder_input, decoder_hidden)
            # |decoder_output| = (1, output_lang.n_words)
            # |decoder_hidden[0]|, |decoder_hidden[1]| = (1, 1, hidden_size)
            topv, topi = decoder_output.topk(1)
            # |topv| = (1, 1)
            # |topi| = (1, 1)
            decoder_input = topi.squeeze().detach() # detach from history as input
            loss += criterion(decoder_output, target_tensor[di])
            # |target_tensor[di]| = (1)
            if decoder_input.item() == loader.EOS_token:
                break
    
    loss.backward()

    encoder_optimizer.step()
    decoder_optimizer.step()
    return loss.item() / target_length


def trainiters(encoder, decoder, n_iters, print_every=5000, plot_every=1000, learning_rate=0.01):
    start = time.time()
    plot_losses = []
    print_loss_total, plot_loss_total = 0, 0

    training_pairs = [tensorsFromPair(random.choice(pairs)) for i in range(n_iters)]
    # |training_pairs| = (n_iters, len(pairs), sentence_length)
    encoder_optimizer = optim.SGD(encoder.parameters(), lr=learning_rate)
    decoder_optimizer = optim.SGD(decoder.parameters(), lr=learning_rate)
    criterion = nn.NLLLoss()

    for iter in range(1, n_iters+1):
        training_pair = training_pairs[iter-1]
        # |training_pair| = (len(pairs))

        input_tensor = training_pair[0]
        target_tensor = training_pair[1]
        # |input_tensor|, |target_tensor| = (sentence_length, 1)

        loss = train(input_tensor, target_tensor, encoder, decoder,
                    encoder_optimizer, decoder_optimizer, criterion)
        
        print_loss_total += loss
        plot_loss_total += loss

        if iter % print_every == 0:
            print_loss_avg = print_loss_total / print_every
            print_loss_total = 0
            print('%s (%d %d%%) %.4f' % (timeSince(start, iter / n_iters),
                                        iter, iter / n_iters * 100, print_loss_avg))

        if iter % plot_every == 0:
            plot_loss_avg = plot_loss_total/plot_every
            plot_losses.append(plot_loss_avg)
            plot_loss_total = 0
        
    showPlot(plot_losses)
    
    plt.savefig('reverse-embeddings-loss')
    torch.save(encoder.state_dict(), 'encoder.pth')
    torch.save(decoder.state_dict(), 'decoder.pth')

if __name__ == "__main__":
    hidden_size = 300
    n_iters = 910000
    teacher_forcing_ratio = 0.5

    input_lang, output_lang, pairs = loader.prepareData('eng', 'fra', True)
    
    input_emb_matrix, output_emb_matrix= np.load('input_emb_matrix.npy'), np.load('output_emb_matrix.npy')
    print('Embedding-matrix shape: {}, {}'.format(input_emb_matrix.shape, output_emb_matrix.shape))
    
    encoder = seq2seq.Encoder(input_lang.n_words, hidden_size, input_emb_matrix).to(device)
    decoder = seq2seq.Decoder(hidden_size, output_lang.n_words, output_emb_matrix).to(device)

    trainiters(encoder, decoder, n_iters)
