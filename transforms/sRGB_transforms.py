#!/usr/bin/env python
# -*- coding: utf-8 -*-

import PyOpenColorIO
import numpy
import colour
import os
from colour import (
    io,
    adaptation,
    models
)
from common.utilities import *


def make_transforms(transform_path, config):
    in_xy_D65 = models.sRGB_COLOURSPACE.whitepoint

    sRGB_IE = colour.RGB_Colourspace(
        "sRGB IE",
        models.sRGB_COLOURSPACE.primaries,
        [1./3., 1./3.],
        whitepoint_name="Illuminant E",
        cctf_decoding=models.sRGB_COLOURSPACE.cctf_decoding,
        cctf_encoding=models.sRGB_COLOURSPACE.cctf_encoding,
        use_derived_RGB_to_XYZ_matrix=True,
        use_derived_XYZ_to_RGB_matrix=True)

    ocioshape_IE_to_D65 = shape_OCIO_matrix(sRGB_IE.RGB_to_XYZ_matrix)
    ociotransform_IE_to_D65 =\
        PyOpenColorIO.MatrixTransform(ocioshape_IE_to_D65)

    sRGB_domain = numpy.array([0.0, 1.0])
    sRGB_tf_to_linear_LUT = colour.LUT1D(
        table=models.sRGB_COLOURSPACE.cctf_decoding(
            colour.LUT1D.linear_table(
                1024, sRGB_domain)),
        name="sRGB to Linear",
        domain=sRGB_domain,
        comments=["sRGB CCTF to Display Linear"])
    sRGB_linear_to_tf_LUT = colour.LUT1D(
        table=models.sRGB_COLOURSPACE.cctf_encoding(
            colour.LUT1D.linear_table(
                8192, sRGB_domain)),
        name="Linear to sRGB",
        domain=sRGB_domain,
        comments=["sRGB Display Linear to CCTF"])

    sRGB_D65_to_IE_RGB_to_RGB_matrix = colour.RGB_to_RGB_matrix(
        models.sRGB_COLOURSPACE,
        sRGB_IE)

    path = os.path.join(
        transform_path,
        "sRGB_CCTF_to_Linear.spi1d"
    )
    create_directory(path)
    io.write_LUT(
        LUT=sRGB_tf_to_linear_LUT,
        path=path,
        decimals=10)

    path = os.path.join(
        transform_path,
        "sRGB_Linear_to_CCTF.spi1d"
    )
    create_directory(path)
    io.write_LUT(
        LUT=sRGB_linear_to_tf_LUT,
        path=path,
        decimals=10)

    # Define the sRGB specification
    colourspace = PyOpenColorIO.ColorSpace(
        family="Colourspace",
        name="sRGB Colourspace")
    colourspace.setDescription("sRGB IEC 61966-2-1 Colourspace")
    colourspace.setBitDepth(PyOpenColorIO.Constants.BIT_DEPTH_F32)
    colourspace.setAllocationVars([0.0, 1.0])
    colourspace.setAllocation(PyOpenColorIO.Constants.ALLOCATION_UNIFORM)
    transform_to = PyOpenColorIO.GroupTransform()
    transform_to.push_back(
        PyOpenColorIO.FileTransform(
            "sRGB_CCTF_to_Linear.spi1d",
            interpolation=PyOpenColorIO.Constants.INTERP_NEAREST))

    ocio_sRGB_D65_to_sRGB_IE_matrix = shape_OCIO_matrix(
        sRGB_D65_to_IE_RGB_to_RGB_matrix)
    transform_sRGB_D65_to_sRGB_IE =\
        PyOpenColorIO.MatrixTransform(ocio_sRGB_D65_to_sRGB_IE_matrix)
    transform_to.push_back(transform_sRGB_D65_to_sRGB_IE)
    transform_from = PyOpenColorIO.GroupTransform()

    # The first object is the wrong direction re-used from above.
    transform_sRGB_IE_to_sRGB_D65 =\
        PyOpenColorIO.MatrixTransform(ocio_sRGB_D65_to_sRGB_IE_matrix)

    # Flip the direction to get the proper output
    transform_sRGB_IE_to_sRGB_D65.setDirection(
        PyOpenColorIO.Constants.TRANSFORM_DIR_INVERSE)
    transform_from.push_back(transform_sRGB_IE_to_sRGB_D65)
    transform_from.push_back(
        PyOpenColorIO.FileTransform(
            "sRGB_Linear_to_CCTF.spi1d",
            interpolation=PyOpenColorIO.Constants.INTERP_NEAREST))

    colourspace.setTransform(
        transform_to, PyOpenColorIO.Constants.COLORSPACE_DIR_TO_REFERENCE)
    colourspace.setTransform(
        transform_from, PyOpenColorIO.Constants.COLORSPACE_DIR_FROM_REFERENCE)

    config.addColorSpace(colourspace)

    # Define the commodity sRGB transform
    colourspace = PyOpenColorIO.ColorSpace(
        family="Colourspace",
        name="BT.709 2.2 CCTF Colourspace")
    colourspace.setDescription("Commodity BT.709 2.2 CCTF Colourspace")
    colourspace.setBitDepth(PyOpenColorIO.Constants.BIT_DEPTH_F32)
    colourspace.setAllocationVars([0.0, 1.0])
    colourspace.setAllocation(PyOpenColorIO.Constants.ALLOCATION_UNIFORM)
    transform_to = PyOpenColorIO.GroupTransform()
    transform_to.push_back(
        PyOpenColorIO.ExponentTransform([2.2, 2.2, 2.2, 1.0]))

    transform_to.push_back(transform_sRGB_D65_to_sRGB_IE)
    transform_from = PyOpenColorIO.GroupTransform()

    transform_from.push_back(transform_sRGB_IE_to_sRGB_D65)
    exponent_transform = PyOpenColorIO.ExponentTransform([2.2, 2.2, 2.2, 1.0])
    exponent_transform.setDirection(
        PyOpenColorIO.Constants.TRANSFORM_DIR_INVERSE)
    transform_from.push_back(exponent_transform)

    colourspace.setTransform(
        transform_to, PyOpenColorIO.Constants.COLORSPACE_DIR_TO_REFERENCE)
    colourspace.setTransform(
        transform_from, PyOpenColorIO.Constants.COLORSPACE_DIR_FROM_REFERENCE)

    config.addColorSpace(colourspace)

    # Define the reference ITU-R BT.709 linear RGB to IE based
    # reference transform
    colourspace = PyOpenColorIO.ColorSpace(
        family="Chromaticity",
        name="sRGB Linear RGB")
    colourspace.setDescription("sRGB IEC 61966-2-1 Linear RGB")
    colourspace.setBitDepth(PyOpenColorIO.Constants.BIT_DEPTH_F32)
    colourspace.setAllocationVars(
        [
            numpy.log2(calculate_ev_to_rl(-10.0)),
            numpy.log2(calculate_ev_to_rl(15.0))
        ])
    colourspace.setAllocation(PyOpenColorIO.Constants.ALLOCATION_LG2)

    transform_to = transform_sRGB_D65_to_sRGB_IE
    transform_from = transform_sRGB_IE_to_sRGB_D65

    colourspace.setTransform(
        transform_to, PyOpenColorIO.Constants.COLORSPACE_DIR_TO_REFERENCE)
    colourspace.setTransform(
        transform_from, PyOpenColorIO.Constants.COLORSPACE_DIR_FROM_REFERENCE)

    config.addColorSpace(colourspace)

    # Define the reference ITU-R BT.709 Illuminant E white point basd
    # reference space to linear XYZ transform
    colourspace = PyOpenColorIO.ColorSpace(
        family="Chromaticity",
        name="XYZ IE")
    colourspace.setDescription("XYZ transform with Illuminant E white point")
    colourspace.setBitDepth(PyOpenColorIO.Constants.BIT_DEPTH_F32)
    colourspace.setAllocationVars(
        [
            numpy.log2(calculate_ev_to_rl(-10.0)),
            numpy.log2(calculate_ev_to_rl(15.0))
        ])
    colourspace.setAllocation(PyOpenColorIO.Constants.ALLOCATION_LG2)

    ocio_sRGB_IE_to_XYZ_IE_matrix = shape_OCIO_matrix(
        sRGB_IE.RGB_to_XYZ_matrix
    )
    transform_sRGB_IE_to_XYZ_IE =\
        PyOpenColorIO.MatrixTransform(ocio_sRGB_IE_to_XYZ_IE_matrix)

    transform_to = transform_sRGB_IE_to_XYZ_IE

    # Initialize with the matrix the wrong direction
    transform_from =\
        PyOpenColorIO.MatrixTransform(ocio_sRGB_IE_to_XYZ_IE_matrix)
    # Set the proper direction
    transform_from.setDirection(PyOpenColorIO.Constants.TRANSFORM_DIR_INVERSE)

    colourspace.setTransform(
        transform_to, PyOpenColorIO.Constants.COLORSPACE_DIR_TO_REFERENCE)
    colourspace.setTransform(
        transform_from, PyOpenColorIO.Constants.COLORSPACE_DIR_FROM_REFERENCE)

    config.addColorSpace(colourspace)