import sys
import os
import datetime as dt

import matplotlib

matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QMainWindow, QFileDialog

# Import the main GUI built in QTDesigner, compiled into python with pyuic5.bat
# from Controls.ui_main import Ui_PyCCDPlottingTool
from Controls.ui_main import Ui_PyCCDPlottingTool

# Import the CCDReader class which retrieves json and cache data
from retrieve_data import CCDReader

# Import the PlotWindow display built in QT Designer
from PlotFrame.plotwindow import PlotWindow

from Plotting import make_plots

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

        self.ui = Ui_PyCCDPlottingTool()

        self.ui.setupUi(self)

        self.ui.browsecachebutton.clicked.connect(self.browsecache)

        self.ui.browsejsonbutton.clicked.connect(self.browsejson)

        self.ui.browseoutputbutton.clicked.connect(self.browseoutput)

        self.ui.arccoordsline.textChanged.connect(self.check_if_values)

        self.ui.browsecacheline.textChanged.connect(self.check_if_values)

        self.ui.browsejsonline.textChanged.connect(self.check_if_values)

        self.ui.hline.textChanged.connect(self.check_if_values)

        self.ui.vline.textChanged.connect(self.check_if_values)

        self.ui.browseoutputline.textChanged.connect(self.check_if_values)

        self.ui.plotbutton.clicked.connect(self.plot)

        self.ui.exitbutton.clicked.connect(self.exit_plot)

        self.init_ui()

    def init_ui(self):

        self.show()

    def check_if_values(self):
        """
        Check to make sure all required values have been entered before enabling the plot button
        :return:
        """

        # A list of 'switches' to identify whether a particular field has been populated
        c, j, h, v, o, a = 0, 0, 0, 0, 0, 0

        # TODO check that the entered values are valid before accepting them and turning switch on
        if str(self.ui.browsecacheline.text()) == "":
            self.ui.plotbutton.setEnabled(False)
        else:
            c = 1

        if str(self.ui.browsejsonline.text()) == "":
            self.ui.plotbutton.setEnabled(False)
        else:
            j = 1

        if str(self.ui.hline.text()) == "":
            self.ui.plotbutton.setEnabled(False)
        else:
            h = 1

        if str(self.ui.vline.text()) == "":
            self.ui.plotbutton.setEnabled(False)
        else:
            v = 1

        if str(self.ui.browseoutputline.text()) == "":
            self.ui.plotbutton.setEnabled(False)
        else:
            o = 1

        if str(self.ui.arccoordsline.text()) == "":
            self.ui.plotbutton.setEnabled(False)
        else:
            a = 1

        # If all switches are turned on, their sum should be 6
        if c + j + h + v + o + a == 6:
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
        for num, result in enumerate(data.results["change_models"]):
            self.ui.plainTextEdit_results.appendPlainText("Result: {}".format(num))

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

        shp_on = self.ui.radioshp.isChecked()

        model_on = self.ui.radiomodelfit.isChecked()

        masked_on = self.ui.radiomasked.isChecked()

        extracted_data = CCDReader(h=int(self.ui.hline.text()), v=int(self.ui.vline.text()),
                                   cache_dir=str(self.ui.browsecacheline.text()),
                                   json_dir=str(self.ui.browsejsonline.text()),
                                   arc_coords=str(self.ui.arccoordsline.text()),
                                   output_dir=str(self.ui.browseoutputline.text()),
                                   model_on=self.ui.radiomodelfit.isChecked(),
                                   masked_on=self.ui.radiomasked.isChecked())

        self.show_results(data=extracted_data)

        print("Drawing plot...")

        self.item_list = [str(i.text()) for i in self.ui.listitems.selectedItems()]

        print("User selected items:\n", self.item_list)

        fig = make_plots.draw_figure(data=extracted_data, items=self.item_list, model_on=model_on, masked_on=masked_on)

        addmaskstr, addmodelstr = "MASKEDOFF", "_MODELOFF"

        # ****Generate the output .png filename****
        fname = f"{extracted_data.output_dir}{os.sep}h{extracted_data.H}v{extracted_data.V}_" \
                f"{extracted_data.arc_paste}_{addmaskstr}{addmodelstr}{self.item_list}.png"

        # ****Save figure to .png and show figure in QWidget****
        fig.tight_layout()

        if os.path.exists(fname):
            os.remove(fname)

        plt.savefig(fname, figuresize=(16, 38), bbox_inches="tight", dpi=150)

        print("\nplt object saved to file {}\n".format(fname))

        if shp_on is True:
            self.get_shp(extracted_data)

        global p
        p = PlotWindow(fig)

        return None

    def get_shp(self, data):

        # GeoCoordinate(x=(float value), y=(float value), reference coords.x and coords.y to access x and y values
        coords = data.coord

        layer_name = "H" + str(data.H) + "_V" + str(data.V) + "_" + str(coords.x) + "_" + str(coords.y)

        out_shp = data.output_dir + os.sep + layer_name + ".shp"

        try:
            from osgeo import ogr, osr

        except ImportError:
            import ogr, osr

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

    def exit_plot(self):

        # Close the main GUI and plot window
        self.close()

        sys.exit(0)
