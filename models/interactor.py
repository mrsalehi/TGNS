import torch
import torch.nn as nn
from torch.nn import LSTM, LSTMCell, Linear, Parameter

class Interactor(nn.Module):
    def __init__(self, hidden_size_textual: int, hidden_size_visual: int,
                 hidden_size_ilstm: int):
        """
        :param input_size:
        :param hidden_size:
        """
        super(Interactor, self).__init__()

        # represented by W_S, W_R, W_V with bias b
        self.projection_S = Linear(hidden_size_textual, hidden_size_ilstm, bias=True)
        self.projection_V = Linear(hidden_size_visual, hidden_size_ilstm, bias=True)
        self.projection_R = Linear(hidden_size_ilstm, hidden_size_ilstm, bias=True)

        # parameter w with bias c
        self.projection_w = Linear(hidden_size_ilstm, 1, bias=True)

        self.hidden_size_textual = hidden_size_textual
        self.hidden_size_visual = hidden_size_visual
        self.hidden_size_ilstm = hidden_size_ilstm

        self.iLSTM = LSTMCell(input_size=hidden_size_textual+hidden_size_visual,
                              hidden_size=hidden_size_ilstm)

    def forward(self, h_v: torch.Tensor, h_s: torch.Tensor):
        """
        :param h_v: with shape (batch_size, T, hidden_size_visual)
        :param h_s: with shape (batch_size, N, hidden_size_textual)
        :return: outputs of the iLSTM with shape (batch, T, hidden_size_ilstm)
        """
        batch_size, T, N = h_v.shape[0], h_v.shape[1], h_s.shape[1]

        # h_r_{t-1} in the paper
        h_r_prev = torch.zeros([batch_size, 1, self.hidden_size_ilstm])
        c_r_prev = torch.zeros([batch_size, 1, self.hidden_size_ilstm])

        outputs = []

        for t in range(T):

            # Computing beta_t with shape (batch, N)
            beta_t =  self.projection_w(torch.tanh(self.projection_R(h_r_prev) +
                                                   self.projection_S(h_s) +
                                                   self.projection_V(h_v[t]))
                                        ).squeeze(2)

            alpha_t = torch.softmax(beta_t, dim=0)  # shape: (batch, N)
            H_t_s = torch.dot(alpha_t, h_s)
            r_t = torch.cat([h_v[t], H_t_s])

            h_r_new, c_r_new = self.iLSTM(r_t, (h_r_prev, c_r_prev))
            outputs.append(h_r_new.unsqueeze(1))
            h_r_prev, c_r_prev = h_r_new, c_r_new

        return torch.cat(outputs, dim=1)




