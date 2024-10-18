#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Computes a very simple connectivity matrix, using the streamline count and the
position of the streamlines' endpoints.

This script is intented for exploration of your data. For a more thorough
computation (using the longest streamline segment), and for more options about
the weights of the matrix, see:
>> scil_connectivity_compute_matrices.py
"""

import argparse
import logging
import os.path

from dipy.io.streamline import save_tractogram
from dipy.io.utils import is_header_compatible
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import nibabel as nib
import numpy as np

from scilpy.connectivity.connectivity import \
    find_streamlines_with_connectivity, compute_triu_connectivity_from_labels
from scilpy.image.labels import get_data_as_labels

from scilpy.io.streamlines import load_tractogram_with_reference
from scilpy.io.utils import assert_inputs_exist, assert_outputs_exist, \
    add_verbose_arg, add_overwrite_arg


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('in_labels',
                   help='Input nifti volume.')
    p.add_argument('streamlines',
                   help='Tractogram (trk or tck).')
    p.add_argument('out_file',
                   help="Out .npy file.")
    p.add_argument('--binary', action='store_true',
                   help="If set, saves the result as binary. Else, the "
                        "streamline count is saved.")
    p.add_argument('--show_now', action='store_true',
                   help="If set, shows the matrix with matplotlib.")
    p.add_argument('--hide_background', nargs='?', const=0, type=int,
                   help="If true, set the connectivity matrix for chosen "
                        "label (default: 0), to 0.")

    add_verbose_arg(p)
    add_overwrite_arg(p)

    return p


def prepare_figure_connectivity(matrix):
    matrix = np.copy(matrix)

    fig, axs = plt.subplots(2, 2)
    im = axs[0, 0].imshow(matrix)
    divider = make_axes_locatable(axs[0, 0])
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    axs[0, 0].set_title("Raw streamline count")

    im = axs[0, 1].imshow(matrix + np.min(matrix[matrix > 0]), norm=LogNorm())
    divider = make_axes_locatable(axs[0, 1])
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    axs[0, 1].set_title("Raw streamline count (log view)")

    matrix = matrix / matrix.sum() * 100
    im = axs[1, 0].imshow(matrix)
    divider = make_axes_locatable(axs[1, 0])
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax, orientation='vertical')
    axs[1, 0].set_title("Percentage")

    matrix = matrix > 0
    axs[1, 1].imshow(matrix)
    axs[1, 1].set_title("Binary")

    plt.suptitle("All versions of the connectivity matrix.")


def main():
    p = _build_arg_parser()
    args = p.parse_args()

    if args.verbose:
        # Currenlty, with debug, matplotlib prints a lot of stuff. Why??
        logging.getLogger().setLevel(logging.INFO)

    tmp, ext = os.path.splitext(args.out_file)

    if ext != '.npy':
        p.error("--out_file should have a .npy extension.")

    out_fig = tmp + '.png'
    out_ordered_labels = tmp + '_labels.txt'
    out_rejected_streamlines = tmp + '_rejected_from_background.trk'
    assert_inputs_exist(p, [args.in_labels, args.streamlines])
    assert_outputs_exist(p, args,
                         [args.out_file, out_fig, out_rejected_streamlines])

    ext = os.path.splitext(args.streamlines)[1]
    if ext == '.trk':
        args.reference = None
        if not is_header_compatible(args.streamlines, args.in_labels):
            p.error("Streamlines not compatible with chosen volume.")
    else:
        args.reference = args.in_labels

    logging.info("Loading tractogram.")
    in_sft = load_tractogram_with_reference(p, args, args.streamlines)
    in_img = nib.load(args.in_labels)
    data_labels = get_data_as_labels(in_img)

    in_sft.to_vox()
    in_sft.to_corner()
    matrix, ordered_labels, start_labels, end_labels = \
        compute_triu_connectivity_from_labels(
            in_sft.streamlines, data_labels)

    if args.hide_background is not None:
        idx = ordered_labels.index(args.hide_background)
        nb_hidden = np.sum(matrix[idx, :]) + np.sum(matrix[:, idx]) - \
            matrix[idx, idx]
        if nb_hidden > 0:
            logging.warning("CAREFUL! {} streamlines had one or both "
                            "endpoints in a non-labelled "
                            "area (background = label {}; line/column {})"
                            .format(nb_hidden, args.hide_background, idx))
            matrix[idx, :] = 0
            matrix[:, idx] = 0
        else:
            logging.info("No streamlines with endpoints in the background :)")
        ordered_labels[idx] = ("Hidden background ({})"
                               .format(args.hide_background))

    # Save figure will all versions of the matrix.
    prepare_figure_connectivity(matrix)
    plt.savefig(out_fig)

    if args.binary:
        matrix = matrix > 0

    # Save results.
    np.save(args.out_file, matrix)

    # Save labels
    with open(out_ordered_labels, "w") as text_file:
        logging.info("Labels are saved in: {}".format(out_ordered_labels))
        for i, label in enumerate(ordered_labels):
            text_file.write("{} = {}\n".format(i, label))

    # Showing as last step. Everything else is done, so if user closes figure
    # it's fine.
    if args.show_now:
        plt.show()


if __name__ == '__main__':
    main()
