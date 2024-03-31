from bokeh.models import GlyphRenderer, Circle
from bokeh.models.ranges import FactorRange, DataRange1d
import numpy as np


def circlestack(plot, renderer):
    # check renderer and glyph, get size
    if (not isinstance(renderer, GlyphRenderer)
            or not isinstance(renderer.glyph, Circle)):
        raise TypeError('renderer must be Circle GlyphRenderer')
    # if renderer.glyph.radius is not None:
    #     raise TypeError('Circle glyph must not have radius property')

    # get renderer data source
    source = renderer.data_source

    # get Circle glyph size (diameter in pixels)
    size = 2 * renderer.glyph.radius

    # check and identify ranges and fields
    if (isinstance(plot.x_range, FactorRange) and
            isinstance(plot.y_range, DataRange1d)):
        fr = plot.x_range
        dr = plot.y_range
        fr_field = renderer.glyph.x
        dr_field = renderer.glyph.y
        fr_length = plot.inner_width
        dr_length = plot.inner_height
    elif (isinstance(plot.y_range, FactorRange) and
            isinstance(plot.x_range, DataRange1d)):
        fr = plot.y_range
        dr = plot.x_range
        fr_field = renderer.glyph.y
        dr_field = renderer.glyph.x
        fr_length = plot.inner_height
        dr_length = plot.inner_width
    else:
        raise TypeError('plot must have one FactorRange and one DataRange1d')
    if fr_length is None or dr_length is None:
        print('plot size not yet known')
        return

    # calculate data–to–screen scaling factors (pixels per unit)
    if fr.start == fr.end:
        fr_scaling = fr_length / len(fr.factors)
    else:
        fr_scaling = fr_length / (fr.end - fr.start)
    if dr.start == dr.end:
        print('DataRange1d not yet known')
        return
    else:
        dr_scaling = dr_length / (dr.end - dr.start)

    # get data
    fr_data = source.data[fr_field]
    dr_data = np.array(source.data[dr_field])

    # unpack fr_data if list of tuples
    if isinstance(fr_data[0], tuple):
        levels, _ = list(zip(*fr_data))
    else:
        levels = fr_data
    offsets = np.zeros(len(levels))

    # possible offsets in pixels
    # of both signs, in ascending order of absolute value
    xcs = np.arange(np.floor((fr_scaling - size - 2) / 2)) + 1
    xcs = np.hstack((0, np.vstack((xcs, -xcs)).reshape(-1, order='F')))
    threshold = (size + 1) ** 2

    # apply stacking to each factor level
    for fl in fr.factors:
        # extract data for factor level and transform to pixels
        level_ind = [fl == level for level in levels]
        x = offsets[level_ind] * fr_scaling
        y = dr_data[level_ind] * dr_scaling

        # *** actual stacking ***
        n = len(x)
        # position points in the order they occur in the data
        for i in range(n):
            # get already positioned points
            xo = x[:i]
            yo = y[:i]

            # consider only points which are close along y alone
            close_ind = (yo - y[i]) ** 2 < threshold
            xo = xo[close_ind]
            yo = yo[close_ind]

            # no other points? no constraints on current point
            if len(xo) == 0:
                x[i] = 0
                continue

            # squared distances between actual positions of other points
            # and possible positions of current point
            d2 = (xo[:, None] - xcs[None, :]) ** 2 + (yo[:, None] - y[i]) ** 2
            # minimum squared distance to other points for each possible offset
            d2 = np.min(d2, axis=0)
            # admissible offsets
            xc = xcs[d2 >= threshold]
            if len(xc) > 0:
                # take the first admissible offset
                # because it is closest to the center
                x[i] = xc[0]
            else:
                # no admissible offsets? minimize overlap
                x[i] = xcs[np.argmax(d2)]

        # transform to data and write back
        offsets[level_ind] = x / fr_scaling

        # ***********************

    # repack fr_data
    fr_data = list(zip(levels, offsets))
    # set data
    source.data[fr_field] = fr_data
