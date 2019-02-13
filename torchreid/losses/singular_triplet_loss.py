from .wrapped_triplet_loss import WrappedTripletLoss
from .singular_loss import SingularLoss


def SingularTripletLoss(num_classes: int, use_gpu: bool, args, param_controller) -> 'func':

    xent_loss = SingularLoss(num_classes=num_classes, use_gpu=use_gpu, label_smooth=args.label_smooth, penalty_position=args.penalty_position)
    htri_loss = WrappedTripletLoss(num_classes, use_gpu, args, param_controller, htri_only=True)

    def _loss(x, pids):

        _, y, v, _ = x

        loss = (
            args.lambda_xent * xent_loss(x, pids) +
            args.lambda_htri * htri_loss(x, pids) * param_controller.get_value()
        )

        return loss

    return _loss
