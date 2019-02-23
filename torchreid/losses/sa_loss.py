import torch
import os


def sa_loss(features_dict):

    if os.environ.get('sa') is not None:
        layer3, layer4_1, layer4_2 = features_dict['layers']

        layer3 = torch.norm(layer3, dim=1, p=2) ** 2 / 1024
        print(layer3.size())
        layer3 = layer3.view(layer3.size(0), -1)
        layer4_1 = torch.norm(layer4_1, dim=1, p=2) ** 2 / 2048
        layer4_1 = layer3.view(layer4_1.size(0), -1)
        layer4_2 = torch.norm(layer4_2, dim=1, p=2) ** 2 / 2048
        layer4_2 = layer3.view(layer4_2.size(0), -1)

        layer3 = layer3 / torch.norm(layer3, dim=1, keepdim=True)
        layer4_1 = layer4_1 / torch.norm(layer4_1, dim=1, keepdim=True)
        layer4_2 = layer4_2 / torch.norm(layer4_2, dim=1, keepdim=True)

        as_loss = ((layer3 - layer4_1) ** 2).sum() + ((layer3 - layer4_2) ** 2).sum()
        print(as_loss)
    else:
        as_loss = 0.

    return as_loss
