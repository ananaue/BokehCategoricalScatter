from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import GlyphRenderer, Circle, DataRange1d, FactorRange, Whisker, Label, LabelSet
from bokeh.transform import dodge
from circlestack import circlestack
# https://github.com/bokeh/bokeh/issues/11105 (by allefeld) is circlestack. It prevents overlapping points.
import numpy as np
import csv
import os
from configparser import ConfigParser
from scipy import stats

# btw in vs code use ctrl + / to comment out chunks

def categoricalscatter(datafile, useconfiginput):
    
    # here, make the working directory the same directory that this script is in
    # this is a temporary workaround for being able to use batfile in a different folder to make several graphs at once from data files in that folder
    # (for that (e.g., for %%a in (*.txt) ... etc) a better solution is just making the config a .ini, so that it and the txt files can coexist in the same folder)
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # get the config values
    configvals = ConfigParser()
    configvals.read('config_and_info.txt', encoding='utf-8')
    linewidth_ = float(configvals['Config']['line_width'])
    width4_ = float(configvals['Config']['width_with_four_categories'])
    heightofframe_ = float(configvals['Config']['height_of_frame'])
    textfont_ = configvals['Config']['text_font']
    addtitle_ = configvals['Config']['add_title']
    titlefontsize_ = str(configvals['Config']['title_font_size']) + 'px'
    xaxisticklabelsfontsize_ = str(configvals['Config']['x_axis_tick_labels_font_size']) + 'px'
    scale_ = configvals['Config']['y_axis_scale']
    yaxislabel_= configvals['Config']['y_axis_label']
    yaxislabelfontsize_ = str(configvals['Config']['y_axis_label_font_size']) + 'px'
    yaxisticklabelsfontsize_ = str(configvals['Config']['y_axis_tick_labels_font_size']) + 'px'
    ttestsamplenumbsraw_ = configvals['Config']['columns_for_t_test']

    if useconfiginput == 'yes':
        datafile = configvals['Config']['data_file']

    # this part is adapted from https://stackoverflow.com/a/29082892
    with open(datafile, 'r') as infile:
        # read the file as a dictionary for each row ({header : value})
        # tempname = infile.name
        datafilename = os.path.splitext(os.path.splitext(os.path.basename(infile.name))[0])[0]
        reader = csv.DictReader(infile, delimiter='\t')
        data_pre = {
            'xval': [],
            'yval': []
        }
        x_labl_pre = []
        for row in reader:
            for header, value in row.items():
                try:
                    x_labl_pre.append(header)
                    data_pre['yval'].append(float(value))
                # the except leaves out empty cells from data_pre
                except ValueError:
                    continue
                data_pre['xval'].append(str(header))
    x_labl = list(dict.fromkeys(x_labl_pre))

    # make dict of values by label to get for bars + whiskers
    databygrp = {}
    for i in x_labl:
        databygrp[i] = []
    for idx, grp in enumerate(data_pre['xval']):
        databygrp[grp].append(data_pre['yval'][idx])

    # get averages and stdrd dev
    avgbygrp = []
    errbygrp = {
        'vals': []
    }
    for i in x_labl:
        avgbygrp.append(np.average(databygrp[i]))
        errbygrp['vals'].append(np.std(databygrp[i]))
    # these two lines taken from https://stackoverflow.com/a/46517148
    errbygrp['upper'] = [x+e for x,e in zip(avgbygrp, errbygrp['vals'])]
    errbygrp['lower'] = [x-e for x,e in zip(avgbygrp, errbygrp['vals'])]

    if ttestsamplenumbsraw_ != 'no':
        ttestsamplenumbs_ = [int(i) - 1 for i in configvals['Config']['columns_for_t_test'].split(",")]
        
        # Get a p value using scipy, between chosen columns
        t_stat, p_value = stats.ttest_ind(databygrp[x_labl[(ttestsamplenumbs_[0])]], databygrp[x_labl[(ttestsamplenumbs_[1])]])

        print('p value used: ' + str(p_value))

        # choose asterisks to put later
        if 0.05 > p_value > 0.01:
            pasterisk = '*'
        elif 0.01 > p_value > 0.001:
            pasterisk = '**'
        elif 0.001 > p_value:
            pasterisk = '***'
        else:
            ttestsamplenumbsraw_ = 'no'

    if ttestsamplenumbsraw_ != 'no':
        # to check at what height the bar no longer intersects stuff
        # make list of errbygrp['upper'] and databygrp heights of the t tested data groups and all groups in between
        # then take the max of them, add a buffer

        # the buffer added has to take into acount log scale (alternative is maybe using the other type of units)
        likemaxv = max((data_pre['yval'] + errbygrp['upper']))
        if scale_ == 'linear':
            sigbarbuffer = 0.07 * likemaxv
        else:
            sigbarbuffer = likemaxv ** 1.08 - likemaxv
        sigbaracountforheightpre = []
        for i in range(ttestsamplenumbs_[0], (ttestsamplenumbs_[1] + 1)):
            sigbaracountforheightpre.append(max(databygrp[x_labl[i]]))
            sigbaracountforheightpre.append(errbygrp['upper'][i])
        sigbarheight = max(sigbaracountforheightpre) + sigbarbuffer

        if scale_ == 'linear':
            # height of lower points in the p.step used for the significance bar is just taken as sigbarheight
            # for height of middle points:
            sigbarlineheight = sigbarheight + (0.04 * likemaxv)
            # height for asterisk (lower because of the font margin or something)
            astkyval = sigbarlineheight - (0.006 * likemaxv)
            sighighest = sigbarlineheight + (0.04 * likemaxv)
        else:   # TODO- make log scale lengths mre consistent
            sigbarlineheight = sigbarheight + (likemaxv ** 1.07 - likemaxv)
            astkyval = sigbarlineheight - (likemaxv ** 1.006 - likemaxv)
            sighighest = sigbarlineheight + + (likemaxv ** 1.1 - likemaxv)

    source = ColumnDataSource(data=data_pre)

    widthp = int(0.25 * width4_ * len(x_labl))
    if addtitle_ == 'yes':
        heightp=int(1.0710 * heightofframe_)
    else:
        heightp=int(heightofframe_)

    p = figure(width=widthp, height=heightp, inner_width=widthp, inner_height=heightp, x_range=FactorRange(factors=x_labl), y_axis_type=scale_, y_range=DataRange1d(), y_axis_label=yaxislabel_, toolbar_location=None)

    # decide bounds and number of ticks
    # first get largest val in data or highest err bar
    if ttestsamplenumbsraw_ != 'no':
        maxv = max((data_pre['yval'] + errbygrp['upper'] + [sighighest]))
    else:
        maxv = max((data_pre['yval'] + errbygrp['upper']))
    if scale_ == 'linear':
        p.y_range.start=-0.17 * maxv
        # get 10ths place, as in scit notation
        dnumb = int(np.floor(np.log10(maxv)))
        # truncate maxv to first two digits, excluding '.'
        maxvtrcstr = str(np.round(maxv, -(dnumb - 1)))
        maxvtrcstr = maxvtrcstr.replace('.', '')
        maxvtrc = int(maxvtrcstr.replace('0', ''))
        # get y range end by rounding value of first 2 digits to 5s or 10s, sort of like in https://stackoverflow.com/a/49281976
        if (maxvtrc / 5) > 10:
            maxvrnd = int(np.ceil(.11 * maxvtrc))
            p.y_range.end=(10 * maxvrnd) * (10 ** (dnumb - 1))
            p.yaxis.ticker.desired_num_ticks = maxvrnd
        else:
            maxvrnd = int(np.ceil(.22 * maxvtrc))
            p.y_range.end=(5 * maxvrnd) * (10 ** (dnumb - 1))
            p.yaxis.ticker.desired_num_ticks = maxvrnd
        p.xaxis.fixed_location=0
        p.yaxis.bounds=(0, p.y_range.end)
        # define a relative boundary to use with err bars later
        relbound = p.y_range.start
    else:
        minv = min((data_pre['yval']))
        p.y_range.start=10 ** np.floor(np.log10(minv))
        p.y_range.end=10 ** np.ceil(np.log10(maxv))
        p.yaxis.ticker.desired_num_ticks = int(np.log10(p.y_range.end) - np.log10(p.y_range.start))
        # want x axis to be one tick (10^x) above the lowest tick
        p.xaxis.fixed_location=10 ** (np.log10(p.y_range.start) + 1)
        p.yaxis.bounds=(p.y_range.start, p.y_range.end)
        p.min_border_bottom=int(0.02824 * heightofframe_)
        # for x label standoff, I thought this would work, but it hasn't so far
        # using https://www.socscistatistics.com/tests/multipleregression/default.aspx 
        # p.xaxis.major_label_standoff=int(-24.7 * (p.yaxis.ticker.desired_num_ticks + 2) + 0.106 * heightofframe_ + 101.59)
        # old ver didn't work well:
        # p.xaxis.major_label_standoff=int((0.45 / (p.yaxis.ticker.desired_num_ticks)) * heightofframe_)
        # current ver:
        # needs more testing for different heightofframes
        p.xaxis.major_label_standoff=int(2.9341 * heightofframe_ * (p.yaxis.ticker.desired_num_ticks + 1) ** -1.815)
        # define a relative boundary to use with err bars later
        relbound = 10 ** (np.log10(p.y_range.start) + 0.3)

    # hide lower err line/bar when lower than relbound
    for idx, itm in enumerate(errbygrp['lower']):
        if itm <= relbound:
            errbygrp['lower'][idx] = avgbygrp[idx]

    # show title or not
    if addtitle_ == 'yes':
        p.title=datafilename
        p.title.text_font=textfont_
        p.title.text_color='black'
        p.title.text_font_size=titlefontsize_
        p.title.align='center'

    p.grid.visible=False
    p.outline_line_color=None

    p.axis.axis_line_width=linewidth_

    p.axis.major_label_text_color="black"
    p.axis.major_label_text_font=textfont_
    p.xaxis.major_label_text_font_size=xaxisticklabelsfontsize_
    p.yaxis.major_label_text_font_size=yaxisticklabelsfontsize_
    p.yaxis.axis_label_text_color='black'
    p.yaxis.axis_label_text_font=textfont_
    p.yaxis.axis_label_text_font_size=yaxislabelfontsize_
    p.yaxis.axis_label_standoff=int(0.08235 * heightofframe_)

    p.axis.minor_tick_line_color=None
    p.axis.major_tick_line_color='black'
    p.axis.major_tick_line_width=linewidth_
    p.axis.major_tick_in=0
    p.axis.major_tick_out=int(0.02353 * heightofframe_)

    # give cicles to circlestack
    circ = Circle(x='xval', y='yval', radius=int(0.01647 * heightofframe_))

    # correct circlestack y vals in case of log scale, also set bar bottom
    if scale_ == 'linear':
        circlestack(p, GlyphRenderer(data_source=source, glyph=circ))
    else:
        # give circlestack the (relatively) real positions on plot - np.log10(start//end) is important
        sourcelogcirc = ColumnDataSource(data=dict(xval=data_pre['xval'], yval=np.log10(data_pre['yval'])))
        pstck = figure(inner_width=widthp, inner_height=heightp, x_range=FactorRange(factors=x_labl), y_axis_type=scale_, y_range=DataRange1d(start=np.log10(p.y_range.start), end=np.log10(p.y_range.end)))
        circlestack(pstck, GlyphRenderer(data_source=sourcelogcirc, glyph=circ))
        # get just the offsets from circle stack
        source.data['xval'] = sourcelogcirc.data['xval']

    # make CDS for bars and whiskers

    brwhsk = ColumnDataSource(data=dict(x_labl=x_labl, avgbygrp=avgbygrp, lowerr=errbygrp['lower'], uperr=errbygrp['upper']))
    
    # put bars on scatter plot as quad
    p.quad(left=dodge('x_labl', -0.35, range=p.x_range), right=dodge('x_labl', 0.35, range=p.x_range), top='avgbygrp', bottom=p.xaxis.fixed_location, source=brwhsk, fill_color="white", line_width=linewidth_, line_color="black")

    # make whiskers
    whsker = Whisker(base='x_labl', upper='uperr', lower='lowerr', source=brwhsk, level="annotation", line_width=linewidth_)
    whsker.upper_head.size=int(0.06838 * width4_)
    whsker.lower_head.size=int(0.06838 * width4_)
    whsker.upper_head.line_width=linewidth_
    whsker.lower_head.line_width=linewidth_
    p.add_layout(whsker)

    # make scatter plot
    p.scatter(x='xval', y='yval', source=source, size=(1.5 * circ.radius), alpha=0, line_alpha=1, line_color="black", line_width=linewidth_)

    # Draw significance bar
    if ttestsamplenumbsraw_ != 'no':
        # for the bracket, I had tried a line + multiline, but the corner was bad. Step gives it a smooth corner and is less code anyway.
        p.step(
            x=[x_labl[ttestsamplenumbs_[0]], x_labl[ttestsamplenumbs_[0]], x_labl[ttestsamplenumbs_[1]], x_labl[ttestsamplenumbs_[1]]],
            y=[sigbarlineheight, sigbarheight, sigbarlineheight, sigbarheight],
            color="black",
            width=linewidth_
        )

        # for the asterisk, since this is categorical, I have it dodge from
        # the second of the t test's group labels by half of the diff between their index
        # (a ttestsamplenumbs_ value is equivalent to an x_labl index number)
        astkdodge = (ttestsamplenumbs_[0] - ttestsamplenumbs_[1]) / 2

        astkCDS = ColumnDataSource(data=dict(xofoneside=[x_labl[ttestsamplenumbs_[1]]], y=[astkyval], text=[pasterisk]))

        # Must be labelset not Label to take a CDA (needed to do Dodge)
        asterisklabel = LabelSet(
            x=dodge('xofoneside', astkdodge, range=p.x_range),
            y='y',
            text='text',
            source=astkCDS,
            text_align='center',
            text_color="black",
            text_font="textfont_",
            text_font_size=yaxisticklabelsfontsize_
        )

        p.add_layout(asterisklabel)

    # decide out file name
    if addtitle_ == 'yes':
        titleq = '_titled'
    else:
        titleq = ''

    if ttestsamplenumbsraw_ != 'no':
        sigcalcq = '_sigcalc'
    else:
        sigcalcq = ''

    outfilename = datafilename + '_' + scale_ + titleq + sigcalcq

    # print(sigbarheight)
    outputstuff = {
        'p': p,
        'outfilename': outfilename
    }

    return outputstuff
