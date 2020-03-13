
import nibabel as nib

from scilpy.tracking.dataset import Dataset
from scilpy.tracking.localTracking import track

from scilpy.tracking.tracker import (probabilisticTracker,
                                     deterministicMaximaTracker)
from scilpy.tracking.trackingField import MaximaField


def main():
    if args.mask_interp == 'nn':
        mask_interpolation = 'nearest'
    elif args.mask_interp == 'tl':
        mask_interpolation = 'trilinear'
    else:
        parser.error("--mask_interp has wrong value. See the help (-h).")
        return


    param['mask_interp'] = mask_interpolation
    param['field_interp'] = 'nearest'
    # r+ is necessary for interpolation function in cython who
    # need read/write right
    param['mmap_mode'] = None if args.isLoadData else 'r+'

    dataset = Dataset(nib.load(args.peaks_file), param['field_interp'])
    field = MaximaField(dataset,
                        param['sf_threshold'],
                        param['sf_threshold_init'],
                        param['theta'])

    if args.algo == 'det':
        tracker = deterministicMaximaTracker(field, param)
    elif args.algo == 'prob':
        tracker = probabilisticTracker(field, param)

    streamlines = track(tracker, mask, seed, param,
                        nbr_processes=args.nbr_processes, pft_tracker=None)

