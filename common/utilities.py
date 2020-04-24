#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy
import os


def create_directory(filename):
    try:
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
    except Exception as ex:
        raise ex


def as_numeric(obj, as_type=numpy.float64):
    try:
        return as_type(obj)
    except TypeError:
        return obj


def shape_OCIO_matrix(numpy_matrix):
    # Shape the RGB to XYZ array for OpenColorIO
    ocio_matrix = numpy.pad(
        numpy_matrix,
        [(0, 1), (0, 1)],
        mode='constant'
    )
    ocio_matrix = ocio_matrix.flatten()
    ocio_matrix[-1] = 1.

    return ocio_matrix


# Convert relative EV to radiometric linear value.
def calculate_ev_to_rl(
    in_ev,
    rl_middle_grey=0.18
):
    in_ev = numpy.asarray(in_ev)

    return as_numeric(numpy.power(2., in_ev) * rl_middle_grey)


# Convert radiometric linear value to relative EV
def calculate_rl_to_ev(
    in_rl,
    rl_middle_grey=0.18
):
    in_rl = numpy.asarray(in_rl)

    return as_numeric(numpy.log2(in_rl) - numpy.log2(rl_middle_grey))

