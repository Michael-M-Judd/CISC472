import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy

#
# michael
#

class michael(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "michael" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# michaelWidget
#

class michaelWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # output volume selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.outputSelector)

    #
    # threshold value
    #
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 0.1
    self.imageThresholdSliderWidget.minimum = -100
    self.imageThresholdSliderWidget.maximum = 100
    self.imageThresholdSliderWidget.value = 0.5
    self.imageThresholdSliderWidget.setToolTip("Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
    parametersFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

  def onApplyButton(self):
    logic = michaelLogic()
    enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    imageThreshold = self.imageThresholdSliderWidget.value
    logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode(), imageThreshold, enableScreenshotsFlag)

#
# michaelLogic
#

class michaelLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """


  def averageTransformedDistance(self, pointsA, pointsB, aToBMatrix):
    average = 0.0
    numbersSoFar = 0
    N = pointsA.GetNumberOfPoints()

    for i in range(N):
        numbersSoFar = numbersSoFar + 1
        a = pointsA.GetPoint(i)
        pointA_Reference = numpy.array(a)
        pointA_Reference = numpy.append(pointA_Reference, 1)
        pointA_Ras = aToBMatrix.MultiplyFloatPoint(pointA_Reference)
        b = pointsB.GetPoint(i)
        pointB_Ras = numpy.array(b)
        pointB_Ras = numpy.append(pointB_Ras, 1)
        distance = numpy.linalg.norm(pointA_Ras - pointB_Ras)
        average = average + (distance - average) / numbersSoFar

    return average


  def rigidRegistration(self, alphaPoints, betaPoints, alphatToBetaMatrix):

    landmarkTransform = vtk.vtkLandmarkTransform()
    landmarkTransform.SetSourceLandmarks(alphaPoints)
    landmarkTransform.SetTargetLandmarks(betaPoints)
    landmarkTransform.SetModeToRigidBody()
    landmarkTransform.Update()
    landmarkTransform.GetMatrix(alphatToBetaMatrix)
      
  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('michaelTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

    return True

      
class michaelTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_michael1()


  def generatePoints(self, numPoints, Scale, Sigma):

    rasFids = slicer.util.getNode('RasPoints')

    if rasFids == None:
      rasFids = slicer.vtkMRMLMarkupsFiducialNode()
      rasFids.SetName('RasPoints')
      slicer.mrmlScene.AddNode(rasFids)

    rasFids.RemoveAllMarkups()
    refFids = slicer.util.getNode('ReferencePoints')

    if refFids == None:
      refFids = slicer.vtkMRMLMarkupsFiducialNode()
      refFids.SetName('ReferencePoints')
      slicer.mrmlScene.AddNode(refFids)
      
    refFids.RemoveAllMarkups()
    refFids.GetDisplayNode().SetSelectedColor(1, 1, 0)

    fromNormCoordinates = numpy.random.rand(numPoints, 3)
    noise = numpy.random.normal(0.0, Sigma, numPoints * 3)

    for i in range(numPoints):
      x = (fromNormCoordinates[i, 0] - 0.5) * Scale
      y = (fromNormCoordinates[i, 1] - 0.5) * Scale
      z = (fromNormCoordinates[i, 2] - 0.5) * Scale
      
      rasFids.AddFiducial(x, y, z)
      xx = x + noise[i * 3]
      yy = y + noise[i * 3 + 1]
      zz = z + noise[i * 3 + 2]
      refFids.AddFiducial(xx, yy, zz)




  def fiducialsToPoints(self, fiducials, points):
    n = fiducials.GetNumberOfFiducials()
    
    for i in range(n):
      p = [0,0,0]
      fiducials.GetNthFiducialPosition(i, p)
      points.InsertNextPoint(p[0], p[1], p[2])



  def test_michael1(self):
    
    referenceToRas = slicer.vtkMRMLLinearTransformNode()
    referenceToRas.SetName('ReferenceToRas')
    slicer.mrmlScene.AddNode(referenceToRas)

    createModelsLogic = slicer.modules.createmodels.logic()
    rasModelNode = createModelsLogic.CreateCoordinate(20, 2)
    rasModelNode.SetName('RasModel')
    refModelNode = createModelsLogic.CreateCoordinate(20, 2)
    refModelNode.SetName('RefModel')
    refModelNode.SetAndObserveTransformNodeID(referenceToRas.GetID())


    rasModelNode.GetDisplayNode().SetColor(1, 0, 0)
    refModelNode.GetDisplayNode().SetColor(0, 1, 0)

    rasPoints = vtk.vtkPoints()
    refPoints = vtk.vtkPoints()


    logic = michaelLogic()
    TREs = []
    nVal = [10,15,20,25,30,35,40,45,50,55]
    numPoints = range(10, 60, 5)

    for i in range(10):
      
      numPoints = 10 + i * 5
      sigma = 3.0
      scale = 100.0

      self.generatePoints(numPoints, scale, sigma)
      rasFids = slicer.util.getNode('RasPoints')
      refFids = slicer.util.getNode('ReferencePoints')
      self.fiducialsToPoints(rasFids, rasPoints)
      self.fiducialsToPoints(refFids, refPoints)
      referenceToRasMatrix = vtk.vtkMatrix4x4()
      logic.rigidRegistration(refPoints, rasPoints, referenceToRasMatrix)
      det = referenceToRasMatrix.Determinant()
      
      if det < 1e-8:
        logging.error('All points in one line')
        continue

      referenceToRas.SetMatrixTransformToParent(referenceToRasMatrix)
      avgDistance = logic.averageTransformedDistance(refPoints, rasPoints, referenceToRasMatrix)
      print "Average distance: " + str(avgDistance)

      targetPoint_Ras = numpy.array([0,0,0,1])
      targetPoint_Reference = referenceToRasMatrix.MultiplyFloatPoint(targetPoint_Ras)
      targetPoint_Reference = numpy.array(targetPoint_Reference)
      tre = numpy.linalg.norm(targetPoint_Ras - targetPoint_Reference)
      TREs.append(tre)
      print "TRE: " + str(tre)
      print ""
      
    numPoints = range(10, 70, 5)
    # Homework February 9th
    # Using chart view, plot TRE as a function of num of points

    lns = slicer.mrmlScene.GetNodesByClass('vtkMRMLLayoutNode')
    lns.InitTraversal()
    ln = lns.GetNextItemAsObject()
    # Layout 24 contains chart view to inititate construction of widget
    ln.SetViewArrangement(24)

    # Get chart view node
    cvns = slicer.mrmlScene.GetNodesByClass('vtkMRMLChartViewNode')
    cvns.InitTraversal()
    cvn = cvns.GetNextItemAsObject()

    # Create TRE Array
    TREpts = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
    TREarray = TREpts.GetArray()
    TREarray.SetNumberOfTuples(10)

    for i in range(10):
      TREarray.SetComponent(i, 0, numPoints[i])
      TREarray.SetComponent(i, 1, TREs[i])
      TREarray.SetComponent(i, 2, 0)
      
    # Create a Chart Node.
    cn = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())

    # Add the Array Nodes to the Chart. The first argument is a string used for the legend and to refer to the Array when setting properties.
    cn.AddArray('TRE', TREpts.GetID())
    # Set a few properties on the Chart. The first argument is a string identifying which Array to assign the property. 
    # 'default' is used to assign a property to the Chart itself (as opposed to an Array Node).
    cn.SetProperty('default', 'title', 'TRE as a function of # of pts')
    cn.SetProperty('default', 'xAxisLabel', '# of pts')
    cn.SetProperty('default', 'yAxisLabel', 'TRE Value')

    cvn.SetChartNodeID(cn.GetID())
