from categoricalscatter import categoricalscatter
from bokeh.plotting import show, output_file

outputstuff = categoricalscatter(None, 'yes')

output_file(outputstuff['outfilename'] + '.html')
show(outputstuff['p'])