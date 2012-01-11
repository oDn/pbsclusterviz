#!/usr/bin/env python

# This is a program to visualize the load status of a cluster 
# using the output of pbsnodes

import pbsclusterviz
from pbsclusterviz.pbs.pbsnodes import PBSNodes, Node
from pbsclusterviz.pbs.xml_handler import PBSNodesXMLHandler
from pbsclusterviz.compute_node import ComputeNode
import os, re, sys
import xml.sax
import getopt
import ConfigParser
import vtk

def usage():
    print """Usage:
    cluster_load_status [options]
    
    options:
    [-h/--help]                  Print usage information and exit
    [-V/--version]               Print version information and exit
    [-l/--logfile=<filename>]    Specify an alternative log file name
    [-t/--two_d_view]            Display in two dimensions (default 3D)
    [-i/--interactive]           Turn on interactive behaviour (default off)
    [-x/--xmlfile]               Specify an input pbsnodes xml file
    [-o/--outfile=<filename>]    Specify an output image file
    [-c/--configfile=<filename>] Specify an input configuration file
    [-n/--nodesfile=<filename>]  Specify an alternate nodes file
    """

def version():
    print """cluster_load_status version 0.1a"""

# This function looks up the config files, checks whether they exist
# and returns a list with two elements. The first is a Parser for 
# the config file and the second one a list of all nodes

def get_config( xml_file ):
    # work out where the config files are from the PYTHONPATH environment variable
    pythonpath = os.environ.get('PYTHONPATH')
    pythonpath_elements = []
    config_path = "/etc/pbsclusterviz.d"
    if pythonpath is not None:
        # split the PYTHONPATH on ':' and search for the pbsclusterviz.d directory
        pythonpath_elements = pythonpath.split(':')
        for path in pythonpath_elements:
            # trim off the path to the python site-packages to get the base path
            site_packages_regexp = re.compile(r'lib\d{0,2}/python\d\.\d/site-packages')
            path = site_packages_regexp.sub('', path)
            test_path = "%s/etc/pbsclusterviz.d" % path
            if os.path.exists(test_path):
                config_path = test_path
    
            if pbsclusterviz.pbs.__debug:
                print "path = %s" % path
                print "test_path = %s" % test_path
                print "config_path = %s" % config_path
    
    config_file = "%s/clusterviz.conf" % config_path
    nodes_file = "%s/nodes" % config_path
    
    # make sure one can find the config file and the nodes file
    if not os.path.exists(config_file):
        print "Unable to find pbsclusterviz configuration file: %s" % config_file
        print "Your PYTHONPATH variable should include the location of the"
        print ".../etc/pbsclusterviz.d directory"
        sys.exit(1)
    
    if not os.path.exists(nodes_file):
        print "Unable to find pbsclusterviz nodes file: %s" % nodes_file
        print "Your PYTHONPATH variable should include the location of the"
        print ".../etc/pbsclusterviz.d directory"
        sys.exit(1)

    # create a parser for the config file as return value
    config = ConfigParser.RawConfigParser()
    config.read(config_file)

    # Now collect the data from the pbsnodes-generated XML file
    pbsnodes = PBSNodes()
    parser = xml.sax.make_parser()
    handler = PBSNodesXMLHandler(pbsnodes)
    parser.setContentHandler(handler)
    
    if xml_file is not None:
        if not os.path.exists(xml_file):
            print "PBSNodes XML file: '%s' does not exist!" % xml_file
            sys.exit(1)
        parser.parse(xml_file)
    else:
        xml_file = '/tmp/pbsnodes.xml'
        pbsnodes_cmd = "pbsnodes -x"
        error = os.system("%s > %s" % (pbsnodes_cmd, xml_file) )
        if error:
            print "Unable to run '%s'.  Exiting." % pbsnodes_cmd
            sys.exit(1)
        parser.parse(xml_file)

    node_table = pbsnodes.get_node_table()

    # read in the node list
    fp = open(nodes_file, "r")
    lines = fp.readlines()
    fp.close()
    
    node_list = []
    hash_regex = re.compile(r'^#')
    return_regex = re.compile(r'\n')
    for line in lines:
        node_name = ""
        x_pos = 0
        y_pos = 0
        if hash_regex.match(line) or return_regex.match(line):
            pass
        else:
            node_info = line.split(' ', 3)
            node_name = node_info[0]
            x_pos = node_info[1]
            y_pos = node_info[2]
    
        if node_table.has_key(node_name):
            node = ComputeNode(display_mode = "load", three_d_view = three_d_view)
            node.set_hostname(node_name)
            node.set_max_load(node_table[node_name].get_num_processors())
            if testing:
                node.set_load_avg(float(x_pos+y_pos)/20.0)
            else:
                node.set_load_avg(node_table[node_name].get_load_avg())
            node.set_grid_xy_pos(x_pos, y_pos)
            if re.search('down', node_table[node_name].get_state()):
                node.set_node_down()
            node_list.append(node)
    
    return ( config, node_list )
    
# Handle options
try:
    options_list, args_list = getopt.getopt(sys.argv[1:], "hVtil:x:o:c:n:d",
            ["help", "version", "two_d_view", "interactive", "logfile=",
                "xmlfile=", "outfile=", "configfile=", "nodesfile=", "debug"])
except getopt.GetoptError:
    # print help information and exit:
    usage()
    sys.exit(2)

testing = False
three_d_view = True
xml_file = None
interactive = False
output_file = "cluster_load_status.png"

pbsclusterviz.pbs.__debug = False

# parse the command line options
for option, arg in options_list:
    if option in ("-h", "--help"):
        usage()
        sys.exit()
    elif option in ("-V", "--version"):
        version()
        sys.exit()
    elif option in ("-t", "--two_d_view"):
        three_d_view = False
    elif option in ("-i", "--interactive"):
        interactive = True
    elif option in ("-l", "--logfile"):
        print "Not yet implemented"
        sys.exit()
        log_file = arg
    elif option in ("-x", "--xmlfile"):
        xml_file = arg
    elif option in ("-o", "--outfile"):
        output_file = arg
    elif option in ("-c", "--configfile"):
        config_file = arg
    elif option in ("-n", "--nodesfile"):
        nodes_file = arg
    elif option in ("-d", "--debug"):
        pbsclusterviz.pbs.__debug = True
    else:
        print "Unknown option %s" % option
        sys.exit(2)

if len(args_list) > 2:
    print "Too many arguments"
    usage()
    sys.exit()

# Read in the config file
( config, node_list ) = get_config( xml_file )

# Extract the title for the image
title_text = config.get( 'load viewer', 'title' )

# work out the output file name's base name (the bit without .png)
base_regex = re.compile(r'(.*?)\.\w+$')
basename_search_result = base_regex.search(output_file)
if basename_search_result.group(1) is None:
    print "Unable to determine the base image output file name"
    sys.exit(0)

output_file_basename = basename_search_result.group(1)

# Create the usual rendering stuff.
renderer = vtk.vtkRenderer()
render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)
render_window.SetSize(1280, 1024)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(render_window)
style = vtk.vtkInteractorStyleTrackballCamera()
iren.SetInteractorStyle(style)

renderer.SetBackground(0, 0, 0)

# set up the text properties for nice text
font_size = 10
text_prop = vtk.vtkTextProperty()
text_prop.SetFontSize(font_size)
text_prop.SetFontFamilyToArial()
text_prop.BoldOff()
text_prop.ItalicOff()
text_prop.ShadowOff()

# add a title to the image
import time
now = time.ctime()

title_text = "%s: %s" % (title_text, now)

title_actor = vtk.vtkTextActor()
title_actor.SetInput(title_text)
title_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
title_actor.GetPositionCoordinate().SetValue(0.5,0.95)

title_prop = title_actor.GetTextProperty()
title_prop.ShallowCopy(text_prop)
title_prop.SetJustificationToCentered()
title_prop.SetVerticalJustificationToTop()
title_prop.SetFontSize(20)
title_prop.SetColor(1,1,1)
title_prop.BoldOn()

renderer.AddActor(title_actor)

# make a lookup table for the colour map and invert it (colours look
# better when it's inverted)
lut = vtk.vtkLookupTable()
refLut = vtk.vtkLookupTable()
num_colors = 256
lut.SetNumberOfColors(num_colors)
refLut.SetNumberOfColors(num_colors)
lut.SetTableRange(0.0, 1.75)
refLut.SetTableRange(0.0, 1.75)
lut.Build()
refLut.Build()
for j in range(num_colors):
    lut.SetTableValue(j, refLut.GetTableValue(num_colors-1-j))

# set up the scalar bar
scalar_bar = vtk.vtkScalarBarActor()
scalar_bar.SetLookupTable(lut)
scalar_bar.SetTitle("Scaled Load")
scalar_bar.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
if three_d_view:
    scalar_bar.GetPositionCoordinate().SetValue(0.1, 0.8)
    scalar_bar.SetOrientationToHorizontal()
    scalar_bar.SetWidth(0.8)
    scalar_bar.SetHeight(0.1)
else:
    scalar_bar.GetPositionCoordinate().SetValue(0.9, 0.1)
    scalar_bar.SetOrientationToVertical()
    scalar_bar.SetWidth(0.1)
    scalar_bar.SetHeight(0.8)

scalar_bar_title_prop = scalar_bar.GetTitleTextProperty()
scalar_bar_title_prop.SetFontFamilyToCourier()
scalar_bar_title_prop.SetFontSize(6)
scalar_bar_title_prop.ItalicOff()

scalar_bar_label_prop = scalar_bar.GetLabelTextProperty()
scalar_bar_label_prop.SetFontFamilyToCourier()
scalar_bar_label_prop.SetFontSize(4)
scalar_bar_label_prop.ItalicOff()

renderer.AddActor(scalar_bar)

# get the colours
rgb = [0.0, 0.0, 0.0]
for node in node_list:
    hostname = node.get_hostname()
    node_load = node.get_load_avg()
    max_node_load = node.get_max_load()
    lut.GetColor(node_load/max_node_load, rgb)
    if node.is_down():
        node.set_rgb([0.5, 0.5, 0.5])
    else:
        node.set_rgb(rgb)

### generate the node matrix
for node in node_list:
    node.add_box(renderer)
    node.add_label(renderer)

# set up the camera properly
renderer.ResetCamera()
renderer.ResetCameraClippingRange()
if three_d_view:
    renderer.GetActiveCamera().Azimuth(140)
    renderer.GetActiveCamera().Elevation(30)
    renderer.GetActiveCamera().Zoom(1.3)
else:
    renderer.GetActiveCamera().Azimuth(180)
    renderer.GetActiveCamera().Elevation(90)
    renderer.GetActiveCamera().Zoom(1.3)

if interactive:
    # Render the scene and start interaction.
    iren.Initialize()
    render_window.Render()
    iren.Start()
else:
    # make sure we're using the mesa classes when saving to file
    fact_graphics = vtk.vtkGraphicsFactory()
    fact_graphics.SetUseMesaClasses(1)
    fact_graphics.SetOffScreenOnlyMode(1)
    fact_image = vtk.vtkImagingFactory()
    fact_image.SetUseMesaClasses(1)

    render_window.OffScreenRenderingOn()
    # to save the file to png, need to pass the render window through a filter
    # to an image object
    win2img_filter = vtk.vtkWindowToImageFilter()
    win2img_filter.SetInput(render_window)

    out_writer = vtk.vtkPNGWriter()
    out_writer.SetInput(win2img_filter.GetOutput())
    if three_d_view:
        out_writer.SetFileName("%s.png" % output_file_basename)
    else:
        out_writer.SetFileName("%s_2d.png" % output_file_basename)

    # render the window to save it to file
    render_window.Render()
    out_writer.Write()

    # and write out a file with the current date on it
    if three_d_view:
        from datetime import datetime
        date = datetime.now()
        date_str = date.strftime("%Y%m%d_%H%M")
        fname_str = "%s_%s.png" % (output_file_basename, date_str)
        out_writer.SetFileName(fname_str)

        # save it to file
        out_writer.Write()

    # generate a high resolution version
    render_window.SetSize(2560, 1440)
    renderer.GetActiveCamera().Zoom(1.2)

    win2img_filter = vtk.vtkWindowToImageFilter()
    win2img_filter.SetInput(render_window)

    title_prop.SetFontSize(44)

    out_writer = vtk.vtkPNGWriter()
    out_writer.SetInput(win2img_filter.GetOutput())
    out_writer.SetFileName("%s_highres.png" % output_file_basename)

    render_window.Render()
    out_writer.Write()

# vim: expandtab shiftwidth=4:
