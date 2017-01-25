def toggle():
  print 'Hello World'

b = qt.QPushButton('Toggle')
b.connect("clicked()", toggle)
b.show()


transformNode = slicer.vtkMRMLLinearTransformNode()
transformNode.SetName('transformNode')
slicer.mrmlScene.AddNode(transformNode)
