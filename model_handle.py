import os
import torch
from utils.io_func import save_json, load_json
from utils.optm import get_optimizer
from data.data_loader import DataLoader


class ModelHandle:
    def __init__(self, model):
        self.model = model
        self.BaseModel, self.Model = self.import_model(model)

    def import_model(self, model):
        if model == 'cygnet':
            from base_models.cygnet_base import CyGNetBase as BaseModel
            from models.cygnet import CyGNet as Model
        elif model == 'regcn':
            from base_models.regcn_base import REGCNBase as BaseModel
            from models.regcn import REGCN as Model
        elif model == 'cen':
            from base_models.cen_base import CENBase as BaseModel
            from models.cen import CEN as Model
        elif model == 'cenet':
            from base_models.cenet_base import CeNetBase as BaseModel
            from models.cenet import CeNet as Model
        else:
            raise Exception('Model error!')
        return BaseModel, Model

    def get_base_model(self,
                       args,
                       data: DataLoader, ):
        raise NotImplementedError

    def get_base_model_from_config(self, config):
        if self.model == 'cygnet':
            base_model = self.BaseModel(
                num_entity=config['num_entity'],
                num_relation=config['num_relation'],
                h_dim=config['h_dim'],
                alpha=config['alpha'],
                penalty=config['penalty']
            )
        elif self.model == 'regcn':
            base_model = self.BaseModel(
                num_entity=config['num_entity'],
                num_relation=config['num_relation'],
                hidden_dim=config['hidden_dim'],
                seq_len=config['seq_len'],
                num_layer=config['num_layer'],
                dropout=config['dropout'],
                active=config['active'],
                self_loop=config['self_loop'],
                layer_norm=config['layer_norm'],
            )
        elif self.model == 'cen':
            base_model = self.BaseModel(
                num_entity=config['num_entity'],
                num_relation=config['num_relation'],
                dim=config['dim'],
                dropout=config['dropout'],
                channel=config['channel'],
                width=config['width'],
                seq_len=config['seq_len'],
                layer_norm=config['layer_norm']
            )
        elif self.model == 'cenet':
            base_model = self.BaseModel(
                num_entity=config['num_entity'],
                num_relation=config['num_relation'],
                dim=config['dim'],
                drop_prop=config['drop_prop'],
                lambdax=config['lambdax'],
                alpha=config['alpha'],
                mode=config['mode'],
            )
        else:
            raise Exception('model ' + config['model'] + ' not exist!')
        return base_model

    def get_default_base_model(self,
                               model: str,
                               data: DataLoader) -> torch.nn.Module:
        """
        get base model with default parameter
        :param model: model name
        :param data: dataset
        :return: base model
        """
        if model == 'regcn':
            base_model = self.BaseModel(
                num_entity=data.num_entity,
                num_relation=data.num_relation,
                hidden_dim=50,
                seq_len=3,
                num_layer=2,
                dropout=0.2,
                active=True,
                self_loop=True,
                layer_norm=True)
        elif model == 'cygnet':
            base_model = self.BaseModel(
                num_entity=data.num_entity,
                num_relation=data.num_relation,
                h_dim=200,
                alpha=0.8,
                penalty=-100
            )
        elif model == 'cen':
            base_model = self.BaseModel(
                num_entity=data.num_entity,
                num_relation=data.num_relation,
                dim=50,
                dropout=0.2,
                seq_len=3,
                channel=50,
                width=3
            )
        elif model == 'cenet':
            base_model = self.BaseModel(
                num_entity=data.num_entity,
                num_relation=data.num_relation,
                dim=50,
                drop_prop=0.5,
                lambdax=1.0,
                alpha=0.1
            )
        else:
            raise Exception('model ' + model + ' not exist!')
        return base_model


def save_checkpoint(model: torch.nn.Module,
                    name: str,
                    path='./checkpoint/'):
    """
    save checkpoint
    :param model: model
    :param name: model name
    :param path: path to save
    :return: None
    """
    config = model.get_config()
    full_path = path + config['model'] + '/' + name + '/'
    if not os.path.exists(full_path):
        # create new directory
        os.makedirs(full_path)
    save_json(config, path=full_path, name='config')
    torch.save(model.state_dict(), full_path + 'model_params.pth')


def load_checkpoint(checkpoint: str,
                    model_handle: ModelHandle,
                    args,
                    device,
                    path='./checkpoint/'):
    """
    load checkpoint
    :param device:
    :param args:
    :param path: path where checkpoint saved
    :return: None
    """
    path = path + args.model + '/' + checkpoint + '/'
    if not os.path.exists(path):
        # create new directory
        raise Exception('The path \'' + path + '\' don\'t exist!')
    config = load_json(path=path, name='config')
    base_model = model_handle.get_base_model_from_config(config)
    data = DataLoader(config['dataset'], './data/temporal/extrapolation')
    data.load(load_time=True)
    data.to(device)
    opt = get_optimizer(args, base_model)
    model = model_handle.Model(base_model, data, opt)
    model.load_state_dict(torch.load(path + 'model_params.pth'))
    model.to(device)
    return model
