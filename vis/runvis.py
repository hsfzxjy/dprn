import os
import glob
import os.path as osp


def get_param(input_fn, layer):

    _, dir, name = input_fn.split('/')
    os.makedirs(osp.join('resnet_vis_output', dir, name), 0o777, True)
    path = osp.join('resnet_vis_output', dir, name)
    return ['-i', osp.abspath(input_fn), '-p', osp.abspath(path), '-l', str(layer)]


if __name__ == '__main__':

    params = []
    # for fn in glob.glob('vis_input/**/*'):
    #     params.append(get_param(fn, 5))
    for fn in glob.glob('vis_input/**/*'):
        params.append(get_param(fn, 4))

    for param in params:
        os.system(' '.join(['python', 'vis.py', *param]))

    # splitted = [params[i:i + 1] for i in range(0, len(params), 1)]
    # import subprocess

    # for group in splitted:
    #     ps = []
    #     for param in group:
    #         p = subprocess.Popen([
    #             'python', 'vis.py',
    #             *param
    #         ])
    #         ps.append(p)
    #     for p in ps:
    #         p.communicate()
