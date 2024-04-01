import sys
from categoricalscatter import categoricalscatter
from bokeh.plotting import show, output_file

datafile = sys.argv[1]
outputstuff = categoricalscatter(datafile, 'no')

output_file(outputstuff['outfilename'] + '.html')
show(outputstuff['p'])
