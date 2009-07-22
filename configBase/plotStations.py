#!/usr/bin/python
import os
from pyx import *

def plot():
    g = graph.graphxy(width=12,height=12,
                      x=graph.axis.axis.linear(title="x [m]", min=0, max=11000),
                      y=graph.axis.axis.linear(title="y [m]", min=0, max=11000))

    g.plot(graph.data.file("posBS.junk", x=2, y=3),
           [graph.style.symbol(graph.style.symbol.circle, size=0.1,
                               symbolattrs=[deco.filled([color.rgb.green]),
                                            deco.stroked([color.rgb.red])])])
    g.plot(graph.data.file("posSS.junk", x=2, y=3),
           [graph.style.symbol(graph.style.symbol.cross,
                               symbolattrs=[deco.stroked([color.rgb.blue])])])

    if os.path.exists('./posRS.junk'):
        g.plot(graph.data.file("posRS.junk", x=2, y=3),
               [graph.style.symbol(graph.style.symbol.circle, size=0.05,
                                   symbolattrs=[deco.filled([color.rgb.blue]),
                                                deco.stroked([color.rgb.blue])])])

        if os.path.exists('./posRMS.junk'):
            g.plot(graph.data.file("posRMS.junk", x=2, y=3),
                   [graph.style.symbol(graph.style.symbol.cross)])
    
        
    g.writePDFfile("scenario")

if __name__ == "__main__" :
    plot()
