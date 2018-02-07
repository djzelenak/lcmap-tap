import datetime as dt
import glob
import os
import sys
import traceback

import matplotlib

# Tell matplotlib to use the QT5Agg Backend
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QMainWindow, QFileDialog

# Import the main GUI built in QTDesigner, compiled into python with pyuic5.bat
from tap_tool.UserInterface import ui_main

# Import the CCDReader class which retrieves json and cache data
from tap_tool.RetrieveData.retrieve_data import CCDReader

# Import the PlotWindow class defined in the plotwindow.py module
from tap_tool.PlotFrame.plotwindow import PlotWindow

from tap_tool.Plotting import make_plots

from tap_tool.Visualization.ard_viewer_qpixelmap import ARDViewerX

import matplotlib.pyplot as plt

# ARD standard projection
WKT = 'PROJCS["Albers",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378140,298.2569999999957,AUTHORITY["EPSG",' \
      '"7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG",' \
      '"4326"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",29.5],' \
      'PARAMETER["standard_parallel_2",45.5],PARAMETER["latitude_of_center",23],PARAMETER["longitude_of_center",-96],' \
      'PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'


class PlotControls(QMainWindow):
    def __init__(self):

        super(PlotControls, self).__init__()

        # Create an instance of a class that builds the user-interface, created in QT Designer and compiled with pyuic5
        self.ui = ui_main.Ui_TAP_Tool()

        # Call the method that adds all of the widgets to the GUI
        self.ui.setupUi(self)

        #### some temporary default values to make testing easier ####
        # self.ui.browseoutputline.setText(r"D:\Plot_Outputs\12.7.17")
        # self.ui.browsejsonline.setText(r"Z:\sites\sd\pyccd-results\H13V05\2017.08.18\json")
        # self.ui.browsecacheline.setText(r"Z:\sites\sd\ARD\h13v05\cache")
        # self.ui.arccoordsline.setText(r"-608,699.743  2,437,196.249 Meters")
        # self.ui.hline.setText(r"13")
        # self.ui.vline.setText(r"5")

        #### Connect the various widgets to the methods they interact with ####
        self.ui.browsecachebutton.clicked.connect(self.browsecache)

        self.ui.browsejsonbutton.clicked.connect(self.browsejson)

        self.ui.browseoutputbutton.clicked.connect(self.browseoutput)

        # self.ui.arccoordsline.textChanged.connect(self.check_values)

        self.ui.browsecacheline.textChanged.connect(self.check_values)

        self.ui.browsejsonline.textChanged.connect(self.check_values)

        self.ui.xline.textChanged.connect(self.check_values)

        self.ui.yline.textChanged.connect(self.check_values)

        self.ui.browseoutputline.textChanged.connect(self.check_values)

        self.ui.plotbutton.clicked.connect(self.plot)

        self.ui.clearpushButton.clicked.connect(self.clear)

        self.ui.savefigpushButton.clicked.connect(self.savefig)

        self.ui.exitbutton.clicked.connect(self.exit_plot)

        self.ui.clicked_listWidget.itemClicked.connect(self.show_ard)

        self.init_ui()

    def init_ui(self):
        """
        Show the user interface
        :return:
        """
        self.show()

    def clear(self):
        """
        Clear the observations window
        :return:
        """
        # self.ui.plainTextEdit_click.clear()
        self.ui.clicked_listWidget.clear()

    def savefig(self):
        """
        Save the current figure to a PNG file
        :return:
        """
        outdir = self.ui.browseoutputline.text()

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        # Pull the coordinate so it can be a part of the .PNG filename
        # coord = CCDReader.arcpaste_to_coord(self.ui.arccoordsline.text())
        coord = self.ui.xline.text() + "_" + self.ui.yline.text()

        # Generate the output .png filename
        self.fname = "{outdir}{sep}H{h}V{v}_{xy}.png".format(outdir=outdir, sep=os.sep, h=self.extracted_data.H,
                                                                v=self.extracted_data.V, xy=coord)

        # Overwrite the .png if it already exists
        if os.path.exists(self.fname):
            os.remove(self.fname)

        # Save the .png
        plt.savefig(self.fname, bbox_inches="tight", dpi=150)
        print("\nplt object saved to file {}\n".format(self.fname))

    def check_values(self):
        """
        Check to make sure all of the required parameters have been entered before enabling the plot button
        :return: None
        """
        counter = 0

        checks = [self.ui.browsecacheline.text(), self.ui.browsejsonline.text(), self.ui.xline.text(),
                  self.ui.yline.text(), self.ui.browseoutputline.text()]

        for check in checks:
            if check == "":
                self.ui.plotbutton.setEnabled(False)
                self.ui.clearpushButton.setEnabled(False)
                self.ui.savefigpushButton.setEnabled(False)
            else:
                counter += 1

        # If all parameters are entered, then the sum will be 6
        if counter == 5:
            self.ui.plotbutton.setEnabled(True)

    def browsecache(self):

        cachedir = QFileDialog.getExistingDirectory(self)

        self.ui.browsecacheline.setText(cachedir)

        return None

    def browsejson(self):

        jsondir = QFileDialog.getExistingDirectory(self)

        self.ui.browsejsonline.setText(jsondir)

        return None

    def browseoutput(self):

        output_dir = QFileDialog.getExistingDirectory(self)

        self.ui.browseoutputline.setText(output_dir)

        return None

    def show_results(self, data):
        """
        Print the model results out to the GUI QPlainTextEdit widget
        :param data:
        :return:
        """
        self.ui.plainTextEdit_results.clear()

        self.ui.plainTextEdit_results.appendPlainText(data.message)

        try:
            self.ui.plainTextEdit_results.appendPlainText("\n***Duplicate dates***\n{}".format(data.duplicates))

        except AttributeError:
            pass

        self.ui.plainTextEdit_results.appendPlainText("\n\nBegin Date: {}".format(data.BEGIN_DATE))

        self.ui.plainTextEdit_results.appendPlainText("End Date: {}\n".format(data.END_DATE))

        for num, result in enumerate(data.results["change_models"]):
            self.ui.plainTextEdit_results.appendPlainText("Result: {}".format(num + 1))

            self.ui.plainTextEdit_results.appendPlainText(
                "Start Date: {}".format(dt.datetime.fromordinal(result["start_day"])))

            self.ui.plainTextEdit_results.appendPlainText(
                "End Date: {}".format(dt.datetime.fromordinal(result["end_day"])))

            self.ui.plainTextEdit_results.appendPlainText(
                "Break Date: {}".format(dt.datetime.fromordinal(result["break_day"])))

            self.ui.plainTextEdit_results.appendPlainText("QA: {}".format(result["curve_qa"]))

            self.ui.plainTextEdit_results.appendPlainText("Change prob: {}\n".format(result["change_probability"]))

        return None

    def plot(self):
        """
        Instantiate the CCDReader class that retrieves the plotting data and generate the plots
        :return:
        """

        # If True, generate a point shapefile for the entered coordinates
        shp_on = self.ui.radioshp.isChecked()

        # Close the previous plot window if still open
        try:
            self.p.close()
        # Will raise AttributeError if this is the first plot because "p" doesn't exist yet
        except AttributeError:
            pass

        # If there is a problem with any of the parameters, the first erroneous parameter
        # will cause an exception to occur which will be displayed in the GUI for the user, and the tool won't close.
        try:
            self.extracted_data = CCDReader(x=self.ui.xline.text(),
                                            y=self.ui.yline.text(),
                                            cache_dir=str(self.ui.browsecacheline.text()),
                                            json_dir=str(self.ui.browsejsonline.text()))

        except (IndexError, AttributeError, TypeError, ValueError):
            # Clear the results window
            self.ui.plainTextEdit_results.clear()

            # Show which exception was raised
            self.ui.plainTextEdit_results.appendPlainText("***Plotting Error***\
                                                          \n\nType of Exception: {}\
                                                          \nException Value: {}\
                                                          \nTraceback Info: {}".format(sys.exc_info()[0],
                                                                                       sys.exc_info()[1],
                                                                                       traceback.print_tb(
                                                                                           sys.exc_info()[2])))

            return None

        # Display change model information for the entered coordinates
        self.show_results(data=self.extracted_data)

        # Retrieve the bands and/or indices selected for plotting
        self.item_list = [str(i.text()) for i in self.ui.listitems.selectedItems()]

        # Make the matplotlib figure object containing all of the artists(axes, points, lines, legends, labels, etc.)
        # The artist_map is a dict mapping each specific PathCollection artist to it's underlying dataset
        # The lines_map is a dict mapping artist lines and points to the legend lines
        self.fig, artist_map, lines_map = make_plots.draw_figure(data=self.extracted_data, items=self.item_list)

        if not os.path.exists(self.ui.browseoutputline.text()):
            os.makedirs(self.ui.browseoutputline.text())

        # Generate the ESRI point shapefile
        if shp_on is True:
            self.get_shp()

        # Show the figure in an interactive window
        self.p = PlotWindow(fig=self.fig, artist_map=artist_map, lines_map=lines_map, gui=self,
                            scenes=self.extracted_data.image_ids)

        # Make these buttons available once a figure has been created
        self.ui.clearpushButton.setEnabled(True)
        self.ui.savefigpushButton.setEnabled(True)

        return None

    def get_shp(self):
        """
        Create a point shapefile from the pair of x, y coordinates entered into the GUI
        :return:
        """
        ###########################################################
        # GeoCoordinate(x=(float value), y=(float value)
        # References coords.x and coords.y to access x and y values
        ###########################################################
        h = self.extracted_data.H

        v = self.extracted_data.V

        coords = self.extracted_data.coord

        out_folder = self.ui.browseoutputline.text()

        layer_name = "H" + str(h) + "_V" + str(v) + "_" + str(coords.x) + "_" + str(coords.y)

        out_shp = out_folder + os.sep + layer_name + ".shp"

        try:
            from osgeo import ogr, osr

        except ImportError:
            import ogr, osr

            print("GDAL not found, can't generate point shapefile.")

            return None

        # Set up driver
        driver = ogr.GetDriverByName("ESRI Shapefile")

        # Create data source
        data_source = driver.CreateDataSource(out_shp)

        # Set the spatial reference system to NAD83 CONUS Albers
        srs = osr.SpatialReference()

        # Set the spatial reference system to match ARD output (WGS 84 Albers)
        srs.ImportFromWkt(WKT)

        # Create layer, add fields to contain x and y coordinates
        layer = data_source.CreateLayer(layer_name, srs)
        layer.CreateField(ogr.FieldDefn("X", ogr.OFTReal))
        layer.CreateField(ogr.FieldDefn("Y", ogr.OFTReal))

        # Create feature, populate X and Y fields
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField("X", coords.x)
        feature.SetField("Y", coords.y)

        # Create the Well Known Text for the feature
        wkt = "POINT(%f %f)" % (coords.x, coords.y)

        # Create a point from the Well Known Text
        point = ogr.CreateGeometryFromWkt(wkt)

        # Set feature geometry to point-type
        feature.SetGeometry(point)

        # Create the feature in the layer
        layer.CreateFeature(feature)

        # Save and close the data source
        data_source = None

        # Dereference the feature
        feature, point, layer = None, None, None

        return None

    def show_ard(self, item):
        """

        :param item: Passed automatically by the ItemClicked method of the QListWidget
        :return:
        """
        try:
            self.ard.close()

        except AttributeError:
            pass

        try:
            sceneID = item.text().split()[2]

            ARD_dir = os.path.split(self.ui.browsecacheline.text())[0]

            scene_dir = ARD_dir + os.sep + sceneID

            scene_file = glob.glob(scene_dir + os.sep + "*.tif")[0]

            print(scene_file)

            self.ard = ARDViewerX(ard_file=scene_file, ccd=self.extracted_data, gui=self)

        except (AttributeError, IndexError):
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            traceback.print_tb(sys.exc_info()[2])
            pass

    def exit_plot(self):
        """
        Close the tool at the user's behest
        :return:
        """
        self.close()

        sys.exit(0)