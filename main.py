import argparse
from models.__list__ import *
from base_models.__list__ import *
import torch
from utils.io_func import save_checkpoint
from utils.io_func import load_checkpoint
from utils.io_func import to_json
from utils.plot import hist_value

opt_list = {
    'sgd': torch.optim.SGD,
    'adam': torch.optim.Adam
}


def train(model, epochs, batch_size, step):
    name = model.get_name()
    metric_history = {}
    loss_history = []
    for epoch in range(epochs):
        loss = model.train_epoch(batch_size=batch_size)
        loss_history.append(loss)
        print('epoch: %d |loss: %f ' % (epoch + 1, loss))
        if (epoch + 1) % step == 0:
            metrics = model.test(batch_size=batch_size)
            print('hist@1 %f |hist@3 %f |hist@10 %f |hist@100 %f |mr %f |mrr %f' % (metrics['hist@1'],
                                                                                    metrics['hist@3'],
                                                                                    metrics['hist@10'],
                                                                                    metrics['hist@100'],
                                                                                    metrics['mr'],
                                                                                    metrics['mrr']))
            for key in metrics.keys():
                if key not in metric_history.keys():
                    metric_history[key] = []
                    metric_history[key].append(metrics[key])
                else:
                    metric_history[key].append(metrics[key])
    # plot
    hist_value({'hist@1': metric_history['hist@1'],
                'hist@3': metric_history['hist@3'],
                'hist@10': metric_history['hist@10'],
                'hist@100': metric_history['hist@100']},
               name=name + '_valid_hist@k')
    hist_value({'mr': metric_history['mr']},
               name=name + '_valid_mr')
    hist_value({'mrr': metric_history['mrr']},
               name=name + '_valid_mrr')
    hist_value({'loss': loss_history},
               name=name + '_valid_loss')
    # save model
    save_checkpoint(model, name=name)
    # save train history
    to_json(metric_history, name=name + '_valid_result')
    to_json(loss_history, name=name + '_train_loss')


def evaluate(model, batch_size, data='test'):
    name = model.get_name()
    metrics = model.test(batch_size=batch_size, dataset='test')
    print('hist@1 %f |hist@3 %f |hist@10 %f |hist@100 %f |mr %f |mrr %f' % (metrics['hist@1'],
                                                                            metrics['hist@3'],
                                                                            metrics['hist@10'],
                                                                            metrics['hist@100'],
                                                                            metrics['mr'],
                                                                            metrics['mrr']))
    to_json(metrics, name=name + '_test_result')


def main(args):
    # choose device
    if args.gpu:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        device = 'cpu'
    # load data
    data = DataLoader(args.dataset, './data/temporal/extrapolation')
    data.load(load_time=True)
    data.to(device)
    # base model
    if args.conf:
        base_model = get_base_model(args, data)
    else:
        base_model = get_default_base_model(args.model, data)
    base_model.to(device)
    # Optimizer
    opt = opt_list[args.opt](base_model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    # model
    model = model_list[args.model](base_model, data, opt)
    model.to(device)
    # load checkpoint
    if args.checkpoint is not None:
        load_checkpoint(model, name=args.checkpoint)
    if args.test:
        # evaluate
        evaluate(model, args.batch_size)
    else:
        # train
        train(model, args.epoch, args.batch_size, args.eva_step)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KGTL')
    # model
    parser.add_argument("--model", type=str, required=True,
                        help="choose model")
    parser.add_argument("--conf", action='store_true', default=False,
                        help="configure parameter")
    # dataset
    parser.add_argument("--dataset", type=str, required=True,
                        help="choose dataset")
    # Optimizer
    parser.add_argument("--opt", type=str, default='adam',
                        help="optimizer")
    parser.add_argument("--weight-decay", type=float, default=0.0,
                        help="weight-decay")
    parser.add_argument("--momentum", type=float, default=0.0,
                        help="momentum")
    parser.add_argument("--lr", type=float, default=1e-3,
                        help="learning rate")
    # train
    parser.add_argument("--epoch", type=int, default=30,
                        help="learning rate")
    parser.add_argument("--batch-size", type=int, default=1024,
                        help="learning rate")
    parser.add_argument("--eva-step", type=int, default=1,
                        help="learning rate")
    # test
    parser.add_argument('--checkpoint', type=str, default=None,
                        help='path and name of model saved')
    # other
    parser.add_argument("--test", action='store_true', default=False,
                        help="load stat from dir and directly test")

    parser.add_argument("--gpu", action='store_true', default=True,
                        help="use GPU")
    args_parsed = parser.parse_args()

    main(args_parsed)
