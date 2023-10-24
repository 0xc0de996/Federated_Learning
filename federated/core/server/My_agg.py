import torch
from typing import List
from ..utils import clear_parameter
from torch.utils.data import DataLoader
from . import server
import copy
import math


class My(server.BaseServer):
    clients_weight = [0 for _ in range(20)]
    eps = 1e-3
    def __init__(self, epoch: int, clients: List, model: torch.nn.Module, data: DataLoader, device: str, alpha: float = 0):
        super().__init__(epoch, clients, model, data, device)
        self.para_cache = []
        self.alpha = alpha
        self.beta = [0 for _ in range(self.n_clients)]
        self.round_weight = [0 for _ in range(self.n_clients)]
        self.round_final_weight = [0 for _ in range(self.n_clients)]
        self.clients_norm = [0 for _ in range(self.n_clients)]
        for i in range(self.n_clients):
            self.para_cache.append(clients[i].model.state_dict())
        self.dim =  0
        for key in self.model.state_dict():
            self.dim += self.model.state_dict()[key].view(-1).size(0)
        print(self.dim)
    
    def Lp_distance(self,model_a,model_b,p: float = 2):
        # 将state_dict()中的值转换为张量
        a_values = torch.cat([param.view(-1) for param in model_a.values()])
        b_values = torch.cat([param.view(-1) for param in model_b.values()])
        
        # 计算Lp范数（Lp距离）
        diff = a_values - b_values
        norm = torch.norm(diff, p=p)
        
        return norm.item()  # 将结果转回标量

    def to_1dvector(self,model):
        _1dvector = torch.cat([value.view(-1) for value in model.values()])
        norm = torch.norm(_1dvector, p=2)
        return _1dvector,norm

    def my(self,p: float = 2):
        agg_para_cache = copy.deepcopy(self.clients[0].model)
        clear_parameter(agg_para_cache)
        server_model,self.clients_norm[0] = self.to_1dvector(self.para_cache[0])
        for i in range(1,self.n_clients):
            tmp_model,self.clients_norm[i] = self.to_1dvector(self.para_cache[i])
            # print(f"{i} dis:{self.Lp_distance(server_model,tmp_model)}\n")
            self.round_weight[i] = 1.0/((self.Lp_distance(server_model,tmp_model)+self.alpha)**p)
            if math.isnan(self.round_weight[i]):
                self.round_weight[i] = 0
        round_sum = sum(self.round_weight)
        # print(f"round_sum:{round_sum}\n")
        for i in range(1,self.n_clients):
            self.beta[i] = min(self.round_weight[i]/round_sum*(self.n_clients-1),1)
        for i in range(1,self.n_clients):
            self.clients_weight[i] = (self.beta[i]*self.clients_weight[i] + self.round_weight[i])/2
        clients_sum = sum(self.clients_weight)
        for i in range(1,self.n_clients):
            self.round_final_weight[i] = self.clients_weight[i]/clients_sum
            # print(i)
            # print(f":{self.round_final_weight[i]}\n")
        for i in range(1,self.n_clients):
            if self.round_final_weight[i] > self.eps:
                # print(f'access:{i}\n')
                for key in self.model.state_dict():
                    self.model.state_dict()[key] += self.round_final_weight[i] * self.para_cache[i][key]

    def pull(self, client_nums, total):
        # for i in range(self.n_clients):
        #     for key in self.para_cache[0]:
        #         self.para_cache[i][key] -= self.model.state_dict()[key]
        # clear_parameter(self.model)
        self.my()