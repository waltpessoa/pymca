#/*##########################################################################
#
# The PyMca X-Ray Fluorescence Toolkit
#
# Copyright (c) 2004-2014 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#############################################################################*/
__author__ = "V. Armando Sole - ESRF Data Analysis"
__contact__ = "sole@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
import sys
import copy
from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaPhysics import Elements
from PyMca5.PyMcaGui import PyMca_Icons
from .MaterialEditor import MaterialComboBox

IconDict = PyMca_Icons.IconDict
QTVERSION = qt.qVersion()
DEBUG = 0

def _getPeakList(fitConfiguration):
    elementsList = []
    for element in fitConfiguration['peaks'].keys():
        if len(element) > 1:
            ele = element[0:1].upper() + element[1:2].lower()
        else:
            ele = element.upper()
        if type(fitConfiguration['peaks'][element]) == type([]):
            for peak in fitConfiguration['peaks'][element]:
                elementsList.append(ele + " " + peak)
        else:
            for peak in [fitConfiguration['peaks'][element]]:
                elementsList.append(ele + " " + peak)
    elementsList.sort()
    return elementsList

def _getMatrixDescription(fitConfiguration):
    useMatrix = False
    detector = None
    for attenuator in list(fitConfiguration['attenuators'].keys()):
        if not fitConfiguration['attenuators'][attenuator][0]:
            # set to be ignored
            continue
        if attenuator.upper() == "MATRIX":
            if fitConfiguration['attenuators'][attenuator][0]:
                useMatrix = True
                matrix = fitConfiguration['attenuators'][attenuator][1:4]
                alphaIn= fitConfiguration['attenuators'][attenuator][4]
                alphaOut= fitConfiguration['attenuators'][attenuator][5]
            else:
                useMatrix = False
            break
    if not useMatrix:
        raise ValueError("Sample matrix has to be specified!")

    if matrix[0].upper() == "MULTILAYER":
        multilayerSample = {}
        layerKeys = list(fitConfiguration['multilayer'].keys())
        if len(layerKeys):
            layerKeys.sort()
        for layer in layerKeys:
            if fitConfiguration['multilayer'][layer][0]:
                multilayerSample[layer] = \
                                fitConfiguration['multilayer'][layer][1:]
    else:
        multilayerSample = {"Auto":matrix}
    return multilayerSample

class QuantificationStrategy(qt.QWidget):
    sigQuantificationStrategySignal = qt.pyqtSignal(object)
    def __init__(self, parent=None, name="Single Layer Matrix Iteration Strategy"):
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle(name)
        self.mainLayout = qt.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self._descriptionButton = qt.QPushButton(self)
        self._descriptionButton.setText("Hide algorithm description")
        self._descriptionButton.setAutoDefault(False)
        self._descriptionButton.clicked[()].connect(self.toggleDescription)
        self._descriptionWidget = qt.QTextEdit(self)
        self._description = qt.QTextDocument()
        self.mainLayout.addWidget(self._descriptionButton)
        self.mainLayout.addWidget(self._descriptionWidget)
        self.build()

    def toggleDescription(self):
        if self._descriptionButton.text().startswith("Hide"):
            self._descriptionWidget.hide()
            self._descriptionButton.setText("Show algorithm description")
        else:
            self._descriptionWidget.show()
            self._descriptionButton.setText("Hide algorithm description")

    def setDescription(self, txt):
        self._description.setPlainText(txt)
        self._descriptionWidget.setDocument(self._description)
        
    def build(self):
        self.strategy = SingleLayerStrategy(self)
        self.setDescription(self.strategy.getDescription())
        self.mainLayout.addWidget(self.strategy)

    def setFitConfiguration(self, fitConfiguration):
        self._fitConfiguration = copy.deepcopy(fitConfiguration)
        self.strategy.setFitConfiguration(self._fitConfiguration)
        
    def getParameters(self):
        pass

    def setParameters(self, ddict):
        pass

class SingleLayerStrategy(qt.QWidget):
    def __init__(self, parent=None, name="Single Layer Matrix Iteration Strategy"):
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle(name)
        self.build()
        
    def getDescription(self):
        txt  = "This matrix iteration procedure is implemented as follows:\n"
        txt += "The concentration of the elements selected to be updated, will "
        txt += "be incorporated in the matrix in the specified form.\n"
        txt += "If the sum of the mass fractions of those elements is above 1 "
        txt += "the program will normalize as usual.\n"
        txt += "If the sum of the mass fractions is below 1, the same procedure "
        txt += "will be applied unless the user has chosen a completing material.\n"
        txt += "Limitations of the algorithm:\n"
        txt += "- The incorporated elements cannot be on different layers.\n"
        txt += "- One element cannot be selected more than once.\n"
        txt += "Recommendations:\n"
        txt += "- In order to avoid unnecessary slow setups, "
        txt += "activate this option and any secondary or tertiary excitation "
        txt += "calculation once you are ready for quantification."
        return txt
        
    def build(self):
        self.mainLayout = qt.QGridLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        label = qt.QLabel("Number of matrix iterations to perfom:")
        self._nIterations = qt.QSpinBox(self)
        self._nIterations.setMinimum(1)
        self._nIterations.setMaximum(5)
        self._nIterations.setValue(3)
        self.mainLayout.addWidget(label, 0, 0)
        self.mainLayout.addWidget(qt.HorizontalSpacer(self), 1, 0)
        self.mainLayout.addWidget(self._nIterations, 0, 2)
        
        label = qt.QLabel("Layer in wich the algorithm is to be applied:")
        self._layerOptions = qt.QComboBox(self)
        self._layerOptions.addItem("Auto")
        self.mainLayout.addWidget(label, 1, 0)
        #self.mainLayout.addWidget(qt.HorizontalSpacer(self), 1, 0)
        self.mainLayout.addWidget(self._layerOptions, 1, 2)

        label = qt.QLabel("Completing material to be used:")
        materialList = list(Elements.Material.keys())
        materialList.sort()
        a = ["-"]
        for key in materialList:
            a.append(key)
        self._materialOptions = MyQComboBox(self, options=a)
        self._materialOptions.addItem("-")
        self.mainLayout.addWidget(label, 2, 0)
        self.mainLayout.addWidget(self._materialOptions, 2, 2)
        self._table = IterationTable(self)
        self.mainLayout.addWidget(self._table, 3, 0, 5, 5)  
        
        self.mainLayout.addWidget(qt.VerticalSpacer(self), 10, 0)

    def setFitConfiguration(self, fitConfiguration):
        # obtain the peak families fitted
        _peakList = _getPeakList(fitConfiguration)
        if not len(_peakList):
            raise ValueError("No peaks to fit!!!!")
        
        matrixDescription = _getMatrixDescription(fitConfiguration)
        layerList = list(matrixDescription.keys())
        layerList.sort()

        materialList = list(Elements.Material.keys())
        materialList.sort()
        a = ["-"]
        for key in materialList:
            a.append(key)

        # Material options
        self._materialOptions.setOptions(a)
        self._table.setMaterialOptions(a)

        # If only one layer, all the elements are selectable
        layerPeaks = {}
        if len(layerList) == 1:
            layerPeaks[layerList[0]] = _peakList
        else:
            inAllLayers = []
            toDeleteFromAllLayers = []
            toForgetAbout = []
            for layer in layerList:
                layerPeaks[layer] = []
            for peak in _peakList:
                element = peak.split()[0]
                alreadyInSomeLayer = False
                presentInLayer = ""
                toDeleteFromAllLayers = False
                for layer in layerList:
                    material = matrixDescription[layer][0]
                    if element in Elements.getMaterialMassFractions([material],
                                                                    [1.0]):
                        if alreadyInSomeLayer:
                            toDeleteFromAllLayers = True
                        else:
                            alreadyInSomeLayer = True
                            presentInLayer = layer
                if toDeleteFromAllLayers:
                    continue
                if not alreadyInSomeLayer:
                    for layer in layerList:
                        layerPeaks[layer].append(peak)
                else:
                    layerPeaks[presentInLayer].append(peak)


        oldOption  = self._layerOptions.currentText()
        self._layerOptions.clear()
        for item in layerList:
            self._layerOptions.addItem(item)

        if oldOption not in layerList:
            oldOption = layerList[0]

        self._layerOptions.setCurrentIndex(layerList.index(oldOption))
        self._table.setLayerPeakFamilies(layerPeaks[oldOption])

    def getFitConfiguration(self):
        pass

class IterationTable(qt.QTableWidget):
    sigValueChanged = qt.pyqtSignal(int, int)
    def __init__(self, parent=None):
        qt.QTableWidget.__init__(self, parent)
        self.verticalHeader().hide()
        self.setRowCount(5)
        self.setColumnCount(6)
        labels = ["Use", "Peak Family", "Material Form"] * 2
        for i in range(len(labels)):
            item = self.horizontalHeaderItem(i)
            if item is None:
                item = qt.QTableWidgetItem(labels[i],
                                           qt.QTableWidgetItem.Type)
            self.setHorizontalHeaderItem(i,item)
        self.build()
        self.resizeColumnToContents(0)        
        self.resizeColumnToContents(3)        
        self.cellChanged[int, int].connect(self.mySlot)

    def mySlot(self,row,col):
        if 1 or DEBUG:
            print("Value changed row = %d col = &d" % (row, col))
            if col != 0:
                print("Text = %s" % self.cellWidget(row, col).currentText())
            
    def _itemSlot(self, *var):
        self.mySlot(self.currentRow(), self.currentColumn())

    def build(self):
        materialList = list(Elements.Material.keys())
        materialList.sort()
        a = ["-"]
        for key in materialList:
            a.append(key)
        for idx in range(10):
            row = idx % 5
            c = 3 * (idx // self.rowCount())
            item = self.cellWidget(row, 0 + c)
            if item is None:
                item = qt.QCheckBox(self)
                self.setCellWidget(row, 0 + c, item)
                item.stateChanged[int].connect(self._itemSlot)

            item = self.cellWidget(row, 1 + c)
            if item is None:
                item = SimpleComboBox(self, row=row, col=1 + c)
                self.setCellWidget(row, 1 + c, item)
                item.sigSimpleComboBoxSignal.connect(self._peakFamilySlot)

            item = self.cellWidget(row, 2 + c)
            if item is None:
                item = MyQComboBox(self, options=a, row=row, col=2 + c)
                item.setEditable(True)
                self.setCellWidget(row, 2 + c, item)
                item.sigMaterialComboBoxSignal.connect(self._comboSlot)

    def setMaterialOptions(self, options):
        for idx in range(10):
            row = idx % 5
            c = 3 * (idx // self.rowCount())            
            item = self.cellWidget(row, 2 + c)
            item.setOptions(options)

    def setLayerPeakFamilies(self, layerPeaks):
        for idx in range(10):
            row = idx % 5
            c = 3 * (idx // self.rowCount())
            item = self.cellWidget(row, 1 + c)
            item.setOptions(layerPeaks)
            # reset material form
            item = self.cellWidget(row, 2 + c)
            item.setCurrentText("-")
            

    def _peakFamilySlot(self, ddict):
        if DEBUG:
            print("_peakFamilySlot", ddict)
        row = ddict['row']
        col = ddict['col']
        text = ddict['text']
        self.setCurrentCell(row, col)
        self.sigValueChanged.emit(row, col)

    def _comboSlot(self, ddict):
        if DEBUG:
            print("_comboSlot", ddict)
        row = ddict['row']
        col = ddict['col']
        text = ddict['text']
        self.setCurrentCell(row, col)
        self.sigValueChanged.emit(row, col)

class SimpleComboBox(qt.QComboBox):
    sigSimpleComboBoxSignal = qt.pyqtSignal(object)
    def __init__(self, parent=None,row=None, col=None):
        if row is None: row = 0
        if col is None: col = 0
        self.row = row
        self.col = col
        qt.QComboBox.__init__(self,parent)
        self.setEditable(False)
        self.setDuplicatesEnabled(False)
        self.activated[str].connect(self._mySignal)

    def setOptions(self, options):
        self.clear()
        for item in options:
            self.addItem(item)

    def _mySignal(self, txt):
        ddict = {}
        ddict["event"] = "activated"
        ddict["row"] = self.row
        ddict["col"] = self.col
        ddict["text"] = self.currentText()
        self.sigSimpleComboBoxSignal.emit(ddict)
                
class MyQComboBox(MaterialComboBox):
    def _mySignal(self, qstring0):
        qstring = qstring0
        (result, index) = self.ownValidator.validate(qstring, 0)
        if result != self.ownValidator.Valid:
            qstring = self.ownValidator.fixup(qstring)
            (result, index) = self.ownValidator.validate(qstring,0)
        if result != self.ownValidator.Valid:
            text = str(qstring)
            if text.upper() not in ["-", "None"]:
                qt.QMessageBox.critical(self, "Invalid Material '%s'" % text,
                                        "The material '%s' is not a valid Formula " \
                                        "nor a valid Material.\n" \
                                        "Please define the material %s or correct the formula\n" % \
                                        (text, text))
                self.setCurrentIndex(0)
                for i in range(self.count()):
                    selftext = self.itemText(i)
                    if selftext == qstring0:
                        self.removeItem(i)
                        break
                return
        text = str(qstring)
        self.setCurrentText(text)
        ddict = {}
        ddict['event'] = 'activated'
        ddict['row'] = self.row
        ddict['col'] = self.col
        ddict['text'] = text
        if qstring0 != qstring:
            self.removeItem(self.count() - 1)
        insert = True
        for i in range(self.count()):
            selftext = self.itemText(i)
            if qstring == selftext:
                insert = False
        if insert:
            self.insertItem(-1, qstring)
        # signal defined in the superclass.
        self.sigMaterialComboBoxSignal.emit(ddict)

def main(fileName=None):
    app  = qt.QApplication(sys.argv)
    w = QuantificationStrategy()
    w.show()
    if fileName is not None:
        from PyMca5.PyMca import ConfigDict
        d = ConfigDict.ConfigDict()
        d.read(fileName)
        w.setFitConfiguration(d)
    app.exec_()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python QuantificationStrategy FitConfigurationFile")
        main()
    else:
        fileName = sys.argv[1]
        print(main(fileName))