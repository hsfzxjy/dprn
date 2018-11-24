import torch
from torch import nn
from torch.nn import functional as F

from . import densenet as densenet_
from .attention import PAM_Module, CAM_Module

__all__ = ['densenet121_DAN_cat', 'densenet121_DAN_cat_fc512']


class DANetHead(nn.Module):
    def __init__(self, in_channels, out_channels, norm_layer):
        super(DANetHead, self).__init__()
        inter_channels = in_channels // 4
        # inter_channels = in_channels
        self.conv5a = nn.Sequential(nn.Conv2d(in_channels, inter_channels, 3, padding=1, bias=False),
                                    norm_layer(inter_channels),
                                    nn.ReLU())

        self.conv5c = nn.Sequential(nn.Conv2d(in_channels, inter_channels, 3, padding=1, bias=False),
                                    norm_layer(inter_channels),
                                    nn.ReLU())

        self.sa = PAM_Module(inter_channels)
        self.sc = CAM_Module(inter_channels)
        self.conv51 = nn.Sequential(nn.Conv2d(inter_channels, inter_channels, 3, padding=1, bias=False),
                                    norm_layer(inter_channels),
                                    nn.ReLU())
        self.conv52 = nn.Sequential(nn.Conv2d(inter_channels, inter_channels, 3, padding=1, bias=False),
                                    norm_layer(inter_channels),
                                    nn.ReLU())

        self.conv6 = nn.Sequential(nn.Dropout2d(0.1, False), nn.Conv2d(inter_channels, out_channels, 1))
        self.conv7 = nn.Sequential(nn.Dropout2d(0.1, False), nn.Conv2d(inter_channels, out_channels, 1))

        self.conv8 = nn.Sequential(nn.Dropout2d(0.1, False), nn.Conv2d(inter_channels, out_channels, 1))

    def forward(self, x):
        feat1 = self.conv5a(x)
        sa_feat, _ = self.sa(feat1)
        sa_conv = self.conv51(sa_feat)
        sa_output = self.conv6(sa_conv)

        feat2 = self.conv5c(x)
        sc_feat = self.sc(feat2)
        sc_conv = self.conv52(sc_feat)
        sc_output = self.conv7(sc_conv)

        feat_sum = sa_conv + sc_conv

        sasc_output = self.conv8(feat_sum)

        output = [sasc_output]
        output.append(sa_output)
        output.append(sc_output)
        return tuple(output)


class DensenetDANCat(densenet_.DenseNet):

    def __init__(self, num_classes, loss, fc_dims, **kwargs):

        super().__init__(
            num_classes=num_classes,
            loss=loss,
            num_init_features=64,
            growth_rate=32,
            block_config=(6, 12, 24, 16),
            fc_dims=None,
            dropout_p=None,
            **kwargs
        )

        self.danet_head = DANetHead(self.feature_dim, self.feature_dim, nn.BatchNorm2d)
        self.fc = self._construct_fc_layer(fc_dims, self.feature_dim * 2, dropout_p=None)
        print(self.fc)
        # feature_dim changed after _construct_fc_layer, so we must construct
        # classifier again
        self.classifier = nn.Linear(self.feature_dim, num_classes)
        self.pa_avgpool = nn.AdaptiveAvgPool2d(1)

        import os
        x = os.environ.get('DAN_part', 'p')
        if x.lower() not in 'spc':
            x = 'p'
        x = x.lower()
        self.DAN_part = x
        print('Using part', x)

    def forward(self, x):
        f = self.features(x)
        old_f = f

        base_x = f
        pa = f
        pa = self.danet_head(base_x)[{'s': 0, 'p': 1, 'c': 2}[self.DAN_part]]
        pa = self.pa_avgpool(pa)
        pa = pa.view(pa.size(0), -1)

        f = F.relu(f)
        v = self.global_avgpool(f)

        v = v.view(v.size(0), -1)

        v = torch.cat((v, pa), 1)
        # v = pa
        if self.fc is not None:
            v = self.fc(v)
        if not self.training:
            return v.view(v.size(0), -1)

        y = self.classifier(v)

        if self.loss == {'xent'}:
            return y
        elif self.loss == {'xent', 'htri'}:
            return y, v
        else:
            return old_f, y, v
            # raise KeyError("Unsupported loss: {}".format(self.loss))


def densenet121_DAN_cat(num_classes, loss, pretrained='imagenet', **kwargs):

    model = DensenetDANCat(
        num_classes=num_classes,
        loss=loss,
        fc_dims=None,
        **kwargs
    )

    if pretrained == 'imagenet':
        densenet_.init_pretrained_weights(model, densenet_.model_urls['densenet121'])

    return model


def densenet121_DAN_cat_fc512(num_classes, loss, pretrained='imagenet', **kwargs):

    model = DensenetDANCat(
        num_classes=num_classes,
        loss=loss,
        fc_dims=[512],
        **kwargs
    )

    if pretrained == 'imagenet':
        densenet_.init_pretrained_weights(model, densenet_.model_urls['densenet121'])

    return model
