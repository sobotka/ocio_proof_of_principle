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
from transforms import sRGB_transforms

if __name__ == "__main__":
    config_directory = "ocio_configuration"
    config_name = "config.ocio"
    luts_directory = "LUTs"
    LUT_search_paths = [luts_directory]

    config = PyOpenColorIO.Config()

    config.setSearchPath(":".join(LUT_search_paths))

    path = os.path.join(
        config_directory,
        luts_directory
    )
    sRGB_transforms.make_transforms(path, config)

    # Define the radiometrically linear working reference space
    colourspace = PyOpenColorIO.ColorSpace(
        family="Colourspace",
        name="Scene Linear BT.709 D65")
    colourspace.setDescription("Scene Linear BT.709 with D65 white point")
    colourspace.setBitDepth(PyOpenColorIO.Constants.BIT_DEPTH_F32)
    colourspace.setAllocationVars(
        [
            numpy.log2(calculate_ev_to_rl(-10.0)),
            numpy.log2(calculate_ev_to_rl(15.0))
        ])
    colourspace.setAllocation(PyOpenColorIO.Constants.ALLOCATION_LG2)
    config.addColorSpace(colourspace)

    # Define the Non-Colour Data transform
    colorspace = PyOpenColorIO.ColorSpace(
        family="Data",
        name="Float Data")
    colorspace.setDescription("Float data that does not define a colour")
    colorspace.setBitDepth(PyOpenColorIO.Constants.BIT_DEPTH_F32)
    colorspace.setIsData(True)
    config.addColorSpace(colorspace)

    # Define the luminance coefficients for the configuration
    config.setDefaultLumaCoefs(
        colour.models.sRGB_COLOURSPACE.RGB_to_XYZ_matrix[1]
    )

    config.setRole(
        PyOpenColorIO.Constants.ROLE_SCENE_LINEAR,
        "Scene Linear BT.709 D65")
    config.setRole(
        PyOpenColorIO.Constants.ROLE_REFERENCE,
        "Scene Linear BT.709 D65")
    config.setRole(
        PyOpenColorIO.Constants.ROLE_COLOR_TIMING,
        "sRGB Colourspace")
    config.setRole(
        PyOpenColorIO.Constants.ROLE_COMPOSITING_LOG,
        "sRGB Colourspace")
    config.setRole(
        PyOpenColorIO.Constants.ROLE_COLOR_PICKING,
        "sRGB Colourspace")
    config.setRole(
        PyOpenColorIO.Constants.ROLE_DATA,
        "Float Data")
    config.setRole(
        PyOpenColorIO.Constants.ROLE_DEFAULT,
        "sRGB Colourspace")
    config.setRole(
        PyOpenColorIO.Constants.ROLE_MATTE_PAINT,
        "sRGB Colourspace")
    config.setRole(
        PyOpenColorIO.Constants.ROLE_TEXTURE_PAINT,
        "sRGB Colourspace")

    displays = {
        "sRGB-Like Commodity Display": {
            "Display Native": "BT.709 2.2 CCTF Colourspace"
        },
        "sRGB Display": {
            "Display Native": "sRGB Colourspace"
        },
        "sRGB Display Variant": {
            "Display Native": "sRGB Colourspace Variant"
        }
    }

    all_displays = set()
    all_views = set()

    for display, views in displays.items():
        all_displays.add(display)
        for view, transform in views.items():
            all_views.add(view)
            config.addDisplay(display, view, transform)

    config.setActiveDisplays(", ".join(all_displays))
    config.setActiveViews(", ".join(all_views))

    try:
        config.sanityCheck()
        path = os.path.join(
            config_directory,
            config_name
        )
        create_directory(path)

        write_file = open(path, "w")
        write_file.write(config.serialize())
        write_file.close()
        print("Wrote config \"{}\"".format(path))
    except Exception as ex:
        raise ex
