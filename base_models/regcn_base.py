import torch
import torch.nn as nn
from base_models.sacn_base import ConvTransEBase
from base_models.layers.urgcn_layer import URGCNLayer
import torch.nn.functional as F


class REGCNBase(nn.Module):
    def __init__(self,
                 num_entity,
                 num_relation,
                 hidden_dim,
                 seq_len,
                 num_layer,
                 dropout=0.0,
                 decoder='convtranse',
                 active=False,
                 self_loop=True,
                 skip_connect=False,
                 layer_norm=True):
        super(REGCNBase, self).__init__()

        self.num_entity = num_entity
        self.num_relation = num_relation
        self.hidden_dim = hidden_dim
        self.seq_len = seq_len
        self.layer_norm = layer_norm

        # weight and embedding
        self.static_entity_embed = torch.nn.Parameter(torch.Tensor(num_entity, hidden_dim), requires_grad=True)
        self.static_relation_embed = torch.nn.Parameter(torch.Tensor(num_relation * 2, hidden_dim))
        self.w1 = torch.nn.Parameter(torch.Tensor(hidden_dim, hidden_dim), requires_grad=True)
        self.w2 = torch.nn.Parameter(torch.Tensor(hidden_dim, hidden_dim), requires_grad=True)
        self.gate_weight = nn.Parameter(torch.Tensor(hidden_dim, hidden_dim))
        self.gate_bias = nn.Parameter(torch.Tensor(hidden_dim))
        self.init_weight()

        # component
        self.rgcn = URGCNBase(hidden_dim,
                              num_layer=num_layer,
                              active=active,
                              dropout=dropout,
                              self_loop=self_loop,
                              skip_connect=skip_connect)

        self.relation_gru = nn.GRUCell(self.hidden_dim * 2, self.hidden_dim)

    def init_weight(self):
        torch.nn.init.xavier_normal_(self.w1)
        torch.nn.init.xavier_normal_(self.w2)
        torch.nn.init.normal_(self.static_entity_embed)
        torch.nn.init.xavier_normal_(self.static_relation_embed)
        nn.init.xavier_uniform_(self.gate_weight, gain=nn.init.calculate_gain('relu'))
        nn.init.zeros_(self.gate_bias)

    def get_average_rela_embed(self,
                               edge,
                               h):
        sr = edge[:, 0:2]
        ro = torch.cat([edge[:, 2].unsqueeze(1), edge[:, 1].unsqueeze(1)], dim=-1)
        er = torch.cat([sr, ro], dim=0)
        er = torch.unique(er, dim=0)
        rela_unique, rela_index, count = torch.unique(er[:, 1], return_inverse=True, return_counts=True)
        h = h[er[:, 0]]
        avg_embed = torch.zeros(rela_unique.shape[0],
                                self.hidden_dim,
                                device=edge.device).scatter_add_(0,
                                                                 rela_index.unsqueeze(1).expand_as(h),
                                                                 h)
        return avg_embed / count.unsqueeze(1), rela_unique

    def forward(self,
                edges: list):
        if self.layer_norm:
            evolved_entity_embed = F.normalize(self.static_entity_embed)
        else:
            evolved_entity_embed = self.static_entity_embed
        relation_embed = torch.cat([self.static_relation_embed,
                                    torch.zeros(self.num_relation * 2, self.hidden_dim,
                                                device=self.static_relation_embed.device)], dim=1)
        # initial evolved relation embedding
        evolved_relation_embed = self.relation_gru(relation_embed, self.static_relation_embed)

        for i, edge in enumerate(edges):
            current_relation_embed = torch.zeros((self.num_relation * 2, self.hidden_dim),
                                                 device=self.static_relation_embed.device)
            avg_embed, index = self.get_average_rela_embed(edge, evolved_entity_embed)
            current_relation_embed[index] = current_relation_embed[index] + avg_embed
            # concat static and current relation embedding
            relation_embed = torch.cat([self.static_relation_embed, current_relation_embed], dim=1)
            # update evolved relation embedding
            evolved_relation_embed = self.relation_gru(relation_embed, evolved_relation_embed)
            current_entity_embed = self.rgcn.forward(evolved_entity_embed,
                                                     evolved_relation_embed,
                                                     edge)
            gate = F.sigmoid(torch.mm(evolved_entity_embed, self.gate_weight) + self.gate_bias)
            evolved_entity_embed = gate * current_entity_embed + (1 - gate) * evolved_entity_embed
        #evolved_entity_embed.backward()
        return evolved_entity_embed, evolved_relation_embed


class URGCNBase(nn.Module):
    def __init__(self,
                 dim,
                 num_layer=1,
                 active=False,
                 dropout=0.0,
                 self_loop=True,
                 skip_connect=False,
                 ):
        super(URGCNBase, self).__init__()
        self.num_layer = num_layer

        self.layers = nn.ModuleList()
        for i in range(num_layer):
            sc = False
            if i == 0 and skip_connect:
                sc = True
            self.layers.append(URGCNLayer(dim,
                                          dim,
                                          active=active,
                                          dropout=dropout,
                                          self_loop=self_loop,
                                          skip_connect=sc))

    def forward(self, input_h, relation_embed, edges):
        h = input_h
        for i in range(self.num_layer):
            h = self.layers[i](h, relation_embed, edges)
        return h
