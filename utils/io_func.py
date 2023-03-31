import torch


def load_data(file: str,
              load_time=False,
              encoding='utf-8'):
    data = []
    with open(file, encoding=encoding) as f:
        content = f.read()
        content = content.strip()
        content = content.split("\n")
        for line in content:
            fact = line.split()
            if load_time:
                data.append([int(fact[0]), int(fact[1]), int(fact[2]), int(fact[3])])
            else:
                data.append([int(fact[0]), int(fact[1]), int(fact[2])])
    data = torch.LongTensor(data)
    return data


def load_dict(file: str,
              encoding='utf-8'):
    dict_data = {}
    with open(file, encoding=encoding) as f:
        content = f.read()
        content = content.strip()
        content = content.split("\n")
        for line in content:
            items = line.split()
            dict_data[items[0]] = int(items[1])
    return dict_data
