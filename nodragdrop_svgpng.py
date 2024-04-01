from categoricalscatter import categoricalscatter
from bokeh.io import export_svg
from bokeh.io import export_png

outputstuff = categoricalscatter(None, 'yes')

export_png(outputstuff['p'], filename=(outputstuff['outfilename'] + '.png'))
outputstuff['p'].output_backend = "svg"
export_svg(outputstuff['p'], filename=(outputstuff['outfilename'] + '.svg'))