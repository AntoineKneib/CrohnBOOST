#################################################################################################################################
#################################################################################################################################
# import zone 
import logging
import os
from typing import Annotated, Optional
import vtk
import slicer
import numpy as np 
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)
from slicer import vtkMRMLScalarVolumeNode
# 
#################################################################################################################################
#################################################################################################################################

# DEVELOPPED BY KNEIB Antoine Ph.D. Student AT IADI LABORATORY INSERM (Université de Lorraine, Nancy, France)
#################################################################################################################################
#################################################################################################################################
#
# CrohnBOOST for 3D Slicer 
# For lesion and creeping fat segmentation 
# User draw centerline and wall points detection with region growing technique
# Still under development for ameliorations 
#
#################################################################################################################################
#################################################################################################################################

class CrohnBOOST(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """
    def __init__(self, parent):

        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("CrohnBOOST")  
        
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Crohn's Disease")]
        self.parent.dependencies = []  
        self.parent.contributors = ["Antoine KNEIB (IADI-INSERM, Université de Lorraine"]  
        
        self.parent.helpText = _("""
        CrohnBOOST is a module for the semi-automatic segmentation of Crohn's intestinal lesions and creeping fat on MRI sequences.
        See more information in <a href="https://github.com/organization/projectname#CrohnSegment">module documentation</a>.
        """)
        
        self.parent.acknowledgementText = _("""
        This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
        and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
        """)

        slicer.app.connect("startupCompleted()", registerSampleData)

###################################################
# Register sample data sets in Sample Data module #
###################################################

def registerSampleData():
    """Add data sets to Sample Data module."""

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")


    # CrohnSegment1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        category="CrohnSegment",
        sampleName="CrohnSegment1",
        thumbnailFileName=os.path.join(iconsPath, "CrohnBOOST.png"),
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="CrohnSegment1.nrrd",
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        nodeNames="CrohnSegment1",
    )

    # CrohnSegment2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="CrohnSegment",
        sampleName="CrohnSegment2",
        thumbnailFileName=os.path.join(iconsPath, "CrohnBOOST.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="CrohnSegment2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="CrohnSegment2",
    )

#
# CrohnSegmentParameterNode
#

@parameterNodeWrapper
class CrohnBOOSTParameterNode:
    """
    The parameters needed by module.
    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode

#################################################################################################################################
#################################################################################################################################
#
# CrohnSegmentWidget
#
#################################################################################################################################
#################################################################################################################################

class CrohnBOOSTWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):  
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # Needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/CrohnBOOST.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
        uiWidget.setMRMLScene(slicer.mrmlScene)
        self.logic = CrohnBOOSTLogic()
        
        # Force the connection of inputSelector2 to the scene
        if hasattr(self.ui, 'inputSelector2'):
            self.ui.inputSelector2.setMRMLScene(slicer.mrmlScene)
            print("inputSelector2 connected to the MRML scene.")
        else:
            print("inputSelector2 not found in the UI")
            
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        
        self.ui.centerlineButton.connect('clicked(bool)', self.onCenterlineButtonClicked)
        self.ui.segmentButton.connect('clicked(bool)', self.onSegmentButtonClicked)
        self.ui.applySegmentationButton.connect('clicked(bool)', self.onApplySegmentationButton)
        self.ui.savesegButton.connect('clicked(bool)', self.onSaveSegButtonClicked)

        # Radius slider configuration
        self.ui.radiusSlider.setMinimum(1)
        self.ui.radiusSlider.setMaximum(20) # Maximum radius in mm (search area)
        self.ui.radiusSlider.setValue(6)
        self.ui.radiusSlider.valueChanged.connect(self.onRadiusSliderValueChanged)

        # Sensitivty slider configuration
        self.ui.horizontalSlider.setMinimum(0)
        self.ui.horizontalSlider.setMaximum(99)
        self.ui.horizontalSlider.setValue(50)  # Default value
        self.ui.horizontalSlider.valueChanged.connect(self.onSliderValueChanged)
        
        # Buttons configuration for fat segmentation
        self.ui.fatPointsButton.connect('clicked(bool)', self.onFatPointsButtonClicked)
        self.ui.segmentFatButton.connect('clicked(bool)', self.onSegmentFatButtonClicked)

        # Brush buttons connection
        if hasattr(self.ui, 'paintButton'):
            self.ui.paintButton.connect('clicked(bool)', self.onPaintButtonClicked)
        if hasattr(self.ui, 'eraseButton'):
            self.ui.eraseButton.connect('clicked(bool)', self.onEraseButtonClicked)

        self._current_segment_nodes = None
        self.initializeParameterNode()

    def onSliderValueChanged(self, value):
        """Appelé à chaque changement de valeur du slider."""
        threshold_factor = value / 100.0
        print(f"Facteur d'expansion ajusté à : {threshold_factor:.2f}")

    def onRadiusSliderValueChanged(self, value): 
        print(f"Rayon intestinal estimé : {value} mm")
        if hasattr(self, '_current_segment_nodes') and self._current_segment_nodes:
            self._current_segment_nodes['rayon_estime'] = value 

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        self.setParameterNode(self.logic.getParameterNode())
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: Optional[CrohnBOOSTParameterNode]) -> None: 
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)

    def onCenterlineButtonClicked(self):
        try:
            markupsNode = slicer.util.getNode('Centerline')
        except slicer.util.MRMLNodeNotFoundException:
            markupsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode", "Centerline")
            markupsNode.CreateDefaultDisplayNodes()

        interactionNode = slicer.app.applicationLogic().GetInteractionNode()
        interactionNode.SetCurrentInteractionMode(slicer.vtkMRMLInteractionNode.Place)
        interactionNode.SetPlaceModePersistence(1)  # 0=non-persistant, 1=persistant
        slicer.modules.markups.logic().SetActiveListID(markupsNode)

    def onSegmentButtonClicked(self):
        inputVolume = self.ui.inputSelector.currentNode()
        if not inputVolume:
            slicer.util.errorDisplay("Veuillez sélectionner un volume d'entrée.")
            return

        # Check the volume contains data
        imageData = inputVolume.GetImageData()
        if not imageData:
            slicer.util.errorDisplay("Le volume sélectionné ne contient pas de données.")
            return
            
        # Display the volume information
        dims = imageData.GetDimensions()
        spacing = imageData.GetSpacing()
        scalarRange = imageData.GetScalarRange()
        print(f"Volume info:")
        print(f"- Dimensions: {dims}")
        print(f"- Spacing: {spacing}")
        print(f"- Intensity range: {scalarRange}")
        
        try: 
            markupsNode = slicer.util.getNode('Centerline')
        except slicer.util.MRMLNodeNotFoundException:
            slicer.util.errorDisplay("Tracer ligne centrale avant de segmenter")
            return
                
        segmentationNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
        segmentationNode.SetName('Crohn_Segmentation')
        segmentationNode.CreateDefaultDisplayNodes()
        segmentationNode.GetSegmentation().AddEmptySegment("Paroi_Intestinale")
        
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(inputVolume)

        # Get the centerline points
        centerline_points = self.logic.obtenirPointsDeLaCourbe(markupsNode)
        if centerline_points is None:
            slicer.util.errorDisplay("Erreur lors de la récupération de la centerline")
            return
        
        rayon_estime = self.ui.radiusSlider.value # Retrieve the radius estimated by the user using the slider

        wall_points = self.logic.detecterPointsParoi(markupsNode, inputVolume, rayon_estime) # Detect the wall points
        if wall_points is None:
            slicer.util.errorDisplay("La detection des points de la paroi a echoue")
            return

        # Store all the required nodes and points
        self._current_segment_nodes = {
            'markups': markupsNode,
            'volume': inputVolume,
            'segmentation': segmentationNode,
            'wall_points': wall_points,
            'centerline_points': centerline_points,
            'rayon_estime': rayon_estime
        }
        
        threshold_factor = self.ui.horizontalSlider.value / 100.0 # Get the value of the sensitivity slider
        print(f"Segmentation expansion factor : {threshold_factor:.2f}")
        
        if self.logic.mettreAJourSegmentation(inputVolume, centerline_points, wall_points, segmentationNode, threshold_factor, rayon_estime): # Perform the initial segmentation
            segmentationDisplayNode = segmentationNode.GetDisplayNode()
            segmentationDisplayNode.SetOpacity(0.5)
        else:
            slicer.util.errorDisplay("The segmentation failed for an unknown reason.")

    def onApplySegmentationButton(self):
        if not self._current_segment_nodes:
            return
                
        threshold_factor = self.ui.horizontalSlider.value / 100.0 # Retrieve the sensitivity slider value
        rayon_estime = self.ui.radiusSlider.value # Retrieve the value of the radius slide

        print(f"Applying the segmentation with factor : {threshold_factor:.2f}")

        segmentationNode = self._current_segment_nodes['segmentation']
        
        self._current_segment_nodes['rayon_estime'] = rayon_estime # Update the estimated radius value in the nodes

        # Clear the existing segment
        segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("Paroi_Intestinale")
        if segmentId:
            segmentationNode.GetSegmentation().RemoveSegment(segmentId)
        
        # Create a new empty segment
        segmentationNode.GetSegmentation().AddEmptySegment("Paroi_Intestinale")
        
        # New segmentation :
        inputVolume = self._current_segment_nodes['volume']
        wall_points = self._current_segment_nodes['wall_points']
        centerline_points = self._current_segment_nodes['centerline_points']
        
        with slicer.util.tryWithErrorDisplay("Segmentation update failed", waitCursor=True):
            self.logic.mettreAJourSegmentation(inputVolume, centerline_points, wall_points, 
                                            segmentationNode, threshold_factor)

    def onSaveSegButtonClicked(self):
        try:
            # Retrieve the input image with the correct reference
            inputImage = self.ui.inputSelector.currentNode()
            if not inputImage:
                raise ValueError("No input image selected")

            # Retrieve the segmentation
            segmentationNode = None
            try:
                segmentationNode = slicer.util.getNode('Crohn_Segmentation')
            except slicer.util.MRMLNodeNotFoundException:
                raise ValueError("No segmentation found. Please perform a segmentation first")

            if not segmentationNode:
                raise ValueError("No active segmentation")

            # Create a volume node to store the labeled segmentation 
            labelMapVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
            
            # Convert the segmentation into a labelmap volume
            slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(
                segmentationNode, labelMapVolumeNode, inputImage)

            # Get the file path for saving : 
            fileName = slicer.app.ioManager().openSaveDataDialog()
            if not fileName:
                slicer.mrmlScene.RemoveNode(labelMapVolumeNode)
                return

            # Display a progress dialog 
            progressDialog = slicer.util.createProgressDialog(
                windowTitle="Saving the segmentation",
                labelText="Saving in progres....",
                maximum=100
            )
            
            try:
                progressDialog.value = 50
                
                # Sauvegarder avec le nom de fichier sélectionné
                slicer.util.saveNode(labelMapVolumeNode, fileName)
                
                # Nettoyer: supprimer le noeud temporaire
                slicer.mrmlScene.RemoveNode(labelMapVolumeNode)
                
                progressDialog.value = 100
                print(f"Segmentation successfully saved in: {fileName}")
            
            finally:
                progressDialog.close()
        
        except Exception as e:
            print(f"Error while saving: {str(e)}")
            slicer.util.errorDisplay(f"Error while saving: {str(e)}")

    def onFatPointsButtonClicked(self): 
        try:
            markupsNode = slicer.util.getNode('FatPoints')
        except slicer.util.MRMLNodeNotFoundException: 
            markupsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "FatPoints")
            markupsNode.CreateDefaultDisplayNodes()

            # Configuration area for point appearance 
            displayNode = markupsNode.GetDisplayNode()
            displayNode.SetSelectedColor(1,1,0) # Yellow for points located in fat
        
        interactionNode = slicer.app.applicationLogic().GetInteractionNode()
        interactionNode.SetCurrentInteractionMode(slicer.vtkMRMLInteractionNode.Place)
        interactionNode.SetPlaceModePersistence(1)
        slicer.modules.markups.logic().SetActiveListID(markupsNode)
        
    def onSegmentFatButtonClicked(self):
        fatVolume = self.ui.inputSelector2.currentNode()
        if not fatVolume:
            slicer.util.errorDisplay("Please select the volume for fat segmentation (inputSelector2)")
            return
        
        lesionVolume = self.ui.inputSelector.currentNode()
        if not lesionVolume:
            slicer.util.errorDisplay("Please select the lesion volume (inputSelector)")
            return
        
        volumeInfo = (
            f"Selected volumes:\n"
            f"LESION volume {lesionVolume.GetName()}\n"
            f"FAT volume {fatVolume.GetName()}\n\n"
            f"Dimensions : {fatVolume.GetImageData().GetDimensions()}"
        )
        print("="*50)
        print("Creeping fat segmentation")
        print(volumeInfo)
        print("="*50)
        
        try:
            fatPointsNode = slicer.util.getNode('FatPoints')
        except slicer.util.MRMLNodeNotFoundException:
            slicer.util.errorDisplay("First place points on the fat")
            return 
        if fatPointsNode.GetNumberOfControlPoints() == 0: 
            slicer.util.errorDisplay("No points have been placed. Please place points on the fat to segment first.")
            return
        
        # Attempt to retrive the lesion segmentation
        try: 
            lesionSegNode = slicer.util.getNode('Crohn_Segmentation')
            segmentID = lesionSegNode.GetSegmentation().GetSegmentIdBySegmentName("LabelMapVolume_1")
            if not segmentID:
                print("Attention: Pas de LabelMapVolume_1 cree dans la segmentation")
        except slicer.util.MRMLNodeNotFoundException:
            lesionSegNode = None 
            print("No lesion segmentation found")

        try:
            fatSegmentationNode = slicer.util.getNode('Fat_Segmentation')
        except slicer.util.MRMLNodeNotFoundException:
            fatSegmentationNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
            fatSegmentationNode.SetName('Fat_Segmentation')
            fatSegmentationNode.CreateDefaultDisplayNodes()
            fatSegmentationNode.GetDisplayNode().SetOpacity(0.5)
            fatSegmentationNode.GetDisplayNode().SetColor(1.0, 1.0, 0.0)
            
            # IMPORTANT : Utiliser le volume de fat pour la géométrie
            fatSegmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(fatVolume)
            
            fatSegmentationNode.GetSegmentation().AddEmptySegment("Creeping_fat")

        # S'assurer que la géométrie est toujours correcte
        fatSegmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(fatVolume)

        # Passer les deux volumes : fatVolume pour l'analyse, lesionVolume pour le masque d'exclusion
        with slicer.util.tryWithErrorDisplay("Echec de la segmentation de la graisse", waitCursor=True): 
            success = self.logic.segmenterGraisse(fatVolume, lesionVolume, fatPointsNode, fatSegmentationNode, lesionSegNode)
            
            if success: 
                slicer.util.infoDisplay("Segmentation de la graisse terminee avec succes.")

    def onPaintButtonClicked(self): 
        try:
            # Récupération du nœud de segmentation "Crohn_Segmentation"
            segmentationNode = slicer.util.getNode('Crohn_Segmentation')
            if not segmentationNode:
                slicer.util.errorDisplay("Veuillez d'abord créer une segmentation")
                return 
            
            # Récupération de l'ID du segment "LabelMapvolume_1"
            segmentation = segmentationNode.GetSegmentation()
            segmentID = segmentation.GetSegmentIdBySegmentName("LabelMapvolume_1")
            if not segmentID:
                slicer.util.errorDisplay("Le segment 'LabelMapvolume_1' n'existe pas")
                return 

            # selection du module Segment Editor
            #slicer.util.selectModule("SegmentEditor")

            # recup du widget script (Python)
            segEditorWidgetPython = slicer.modules.segmenteditor.widgetRepresentation().self()
            segEditorWidgetPython.segmentationNode = segmentationNode
            segEditorWidgetPython.masterVolumeNode = self.ui.inputSelector.currentNode()

            # Définition du segment actif
            try:
                segEditorWidgetPython.setActiveSegmentID(segmentID)
            except AttributeError:
                segEditorWidgetPython.activeSegmentID = segmentID

            # Obtenir le vrai qMRMLSegmentEditorWidget (C++) via la propriété "editor"
            realSegmentEditorWidget = segEditorWidgetPython.editor
            if not realSegmentEditorWidget:
                slicer.util.errorDisplay("Impossible de récupérer le qMRMLSegmentEditorWidget sous-jacent")
                return
            
            # Récupération de l'effet "Paint" et activation
            paintEffect = realSegmentEditorWidget.effectByName("Paint")
            if not paintEffect:
                slicer.util.errorDisplay("L'effet 'Paint' n'est pas disponible")
                return

            realSegmentEditorWidget.setActiveEffect(paintEffect)

            # Configuration du pinceau
            paintEffect.setCommonParameter("BrushAbsoluteDiameter", "5")
            paintEffect.setCommonParameter("BrushSphere", 1)

            print("Effet Paint activé avec BrushAbsoluteDiameter=5 et BrushSphere=1")
        except Exception as e:
            slicer.util.errorDisplay("Erreur lors de l'activation du pinceau : " + str(e))


    def onEraseButtonClicked(self): 
        # Active l'outil qui permet d'effacer pour editer manuellement la segmentation
        try : 
            segmentationNode = slicer.util.getNode('Crohn_Segmentation') 
            if not segmentationNode: 
                slicer.util.errorDisplay("Veuille d'abord creer une segmentation") 
                return 
            
            slicer.util.selectModule('SegmentEditor') 
            segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self()
            segmentEditorWidget.setSegmentationNode(segmentationNode)
            segmentEditorWidget.setMasterVolumeNode(self.ui.inputSelector.currentNode())

            segmentEditorWidget.setActiveEffectByName("Erase") 
        except Exception as e: 
            slicer.util.errorDisplay(f"Erreur lors de l activation de l effaceur  : {str(e)}") 

#################################################################################################################################
#################################################################################################################################
# CrohnSegmentLogic
#################################################################################################################################
#################################################################################################################################

class CrohnBOOSTLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """
    import numpy as np
    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return CrohnBOOSTParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """
        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)

        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")
    
    
    def obtenirPointsDeLaCourbe(self, noeudMarkups):
        if not isinstance(noeudMarkups, slicer.vtkMRMLMarkupsCurveNode):
            return None
        polyData = noeudMarkups.GetCurve()
        return polyData.GetPoints() # Retrive the centerline points
    
    def trouverParoi(self, intensities, debut, fin):
        import numpy as np
        if len(intensities) == 0:
            return None

        if np.all(intensities == 0): # Si toutes les intensités sont nulles, on retourne None
            return None

        # Normaliser les intensités
        intensity_range = np.max(intensities) - np.min(intensities)
        if intensity_range == 0:
            return None
            
        intensities_norm = (intensities - np.min(intensities)) / intensity_range
        
        # Appliquer plusieurs méthodes de détection
        # 1. Méthode du gradient
        gradients = np.gradient(intensities_norm)
        grad_threshold = 0.2
        grad_peaks = np.where(gradients > grad_threshold)[0]
        
        # 2. Méthode du seuil d'intensité
        intensity_threshold = 0.5
        intensity_peaks = np.where(intensities_norm > intensity_threshold)[0]
        
        # Combiner les résultats
        combined_peaks = np.union1d(grad_peaks, intensity_peaks)
        
        if len(combined_peaks) == 0:
            return None
            
        # Trouver le pic avec la plus forte intensités
        peak_idx = combined_peaks[np.argmax(intensities_norm[combined_peaks])]
        position_relative = peak_idx / len(intensities)
        
        return debut + (fin - debut) * position_relative

    def sampleIntensitiesAlongLine(self, startPoint, endPoint, volumeNode):
        import numpy as np
        import vtk
        from vtk.util.numpy_support import vtk_to_numpy

        # Obtenir la matrice de transformation RAS vers IJK
        rasToIJK = vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(rasToIJK)

        # Convertir les points en coordonnées IJK
        startIJK_vtk = rasToIJK.MultiplyPoint((*startPoint, 1.0))
        endIJK_vtk = rasToIJK.MultiplyPoint((*endPoint, 1.0))
        startIJK = np.array(startIJK_vtk[:3])
        endIJK = np.array(endIJK_vtk[:3])

        #print(f"Start point RAS: {startPoint} -> IJK: {startIJK}")
        #print(f"End point RAS: {endPoint} -> IJK: {endIJK}")

        # Obtenir l'image data
        imageData = volumeNode.GetImageData()
        if not imageData:
            return np.array([])

        # Créer une ligne dans l'espace IJK
        lineSource = vtk.vtkLineSource()
        lineSource.SetPoint1(startIJK)
        lineSource.SetPoint2(endIJK)
        lineSource.SetResolution(50)
        lineSource.Update()

        # Configurer le probe filter
        probeFilter = vtk.vtkProbeFilter()
        probeFilter.SetInputConnection(lineSource.GetOutputPort())
        probeFilter.SetSourceData(imageData)
        probeFilter.Update()

        # Obtenir les intensites le long des rayons 
        probedData = probeFilter.GetOutput().GetPointData().GetScalars()
        if not probedData:
            return np.array([])
            
        intensities = vtk_to_numpy(probedData)
        
        # Vérifier les intensités obtenues
        #print(f"Sampled intensities shape: {intensities.shape}")
        if len(intensities) > 0:
            #print(f"Sampled range: [{np.min(intensities)}, {np.max(intensities)}]")
            # Appliquer un lissage gaussien
            from scipy.ndimage import gaussian_filter1d
            intensities = gaussian_filter1d(intensities, sigma=0.5)
        
        return intensities
    
    def expansion_locale_adjacente(self, mask, volume_array, n_iterations=3):
        """
        Expanse le masque en capturant les voxels adjacents avec intensités similaires
        """
        
        from scipy import ndimage
        
        # Récupérer les intensités du masque actuel
        intensities_mask = volume_array[mask > 0]
        mean_int = np.mean(intensities_mask)
        std_int = np.std(intensities_mask)
        
        # Critères d'acceptation assouplis
        int_min = mean_int - 2.5 * std_int
        int_max = mean_int + 2.5 * std_int
        
        print(f"Expansion locale - Intensités: {mean_int:.1f} ± {std_int:.1f}")
        
        result_mask = mask.copy()
        
        for iteration in range(n_iterations):
            # Dilater d'un seul voxel
            dilated = ndimage.binary_dilation(result_mask, iterations=1)
            
            # Zone nouvellement dilatée (la "bordure")
            border = (dilated & ~result_mask).astype(bool)
            
            # Vérifier les intensités dans la bordure - VERSION CORRIGÉE
            # Créer un masque d'intensités valides sur TOUT le volume
            intensity_valid = (volume_array >= int_min) & (volume_array <= int_max)
            
            # Ne garder que les voxels de la bordure qui ont une intensité valide
            valid_border = border & intensity_valid
            
            # Ajouter les voxels valides
            new_voxels = np.sum(valid_border)
            if new_voxels == 0:
                print(f"  Itération {iteration+1}: Plus de voxels à ajouter")
                break
                
            result_mask = result_mask | valid_border
            print(f"  Itération {iteration+1}: +{new_voxels} voxels")
        
        return result_mask.astype(np.uint8)

    def placerMarqueur(self, position):
        import slicer
        fiducialNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        fiducialNode.AddControlPoint(vtk.vtkVector3d(position[0], position[1], position[2]))
        fiducialNode.SetName("Emplacement Paroi")

        return fiducialNode

    
    
    def visualiserPointsCandidats(self, points, volumeInput):
        import numpy as np
        rasToIJK = vtk.vtkMatrix4x4()
        volumeInput.GetRASToIJKMatrix(rasToIJK)
        intensities = []
        for i in range(points.GetNumberOfPoints()):
            point = points.GetPoint(i)
            point_ijk = rasToIJK.MultiplyPoint((*point, 1.0))
            x, y, z = [int(round(v)) for v in point_ijk[:3]]
            image_data = volumeInput.GetImageData()
            intensity = image_data.GetScalarComponentAsDouble(x, y, z, 0)
            intensities.append(intensity)
        print(f"Statistiques des points candidats :")
        print(f"- Nombre de points : {len(intensities)}")
        print(f"- Intensité moyenne : {np.mean(intensities):.2f}")
        print(f"- Écart-type : {np.std(intensities):.2f}")
        print(f"- Min : {np.min(intensities):.2f}")
        print(f"- Max : {np.max(intensities):.2f}")
        return intensities

    def segmenterParRegionSimple(self, volumeInput, centerline_points, wall_points, segmentationNode, threshold_factor, rayon_estime=6):

        from scipy import ndimage
        from scipy.spatial import cKDTree

        volume_array = slicer.util.arrayFromVolume(volumeInput)
        mask = np.zeros_like(volume_array)
        
        spacing = volumeInput.GetSpacing()
        rayon_voxels = int(rayon_estime / min(spacing))

        rasToIJK = vtk.vtkMatrix4x4()
        volumeInput.GetRASToIJKMatrix(rasToIJK)
        
        # Convertir les points en coordonnées IJK
        wall_ijk = []   
        wall_intensities = []
        for i in range(wall_points.GetNumberOfPoints()):
            point = wall_points.GetPoint(i)
            point_ijk = rasToIJK.MultiplyPoint((*point, 1.0))
            x, y, z = [int(round(v)) for v in point_ijk[:3]]
            
            if (0 <= z < mask.shape[0] and 
                0 <= y < mask.shape[1] and 
                0 <= x < mask.shape[2]):
                intensity = volume_array[z, y, x]
                wall_intensities.append(intensity)
                wall_ijk.append([z, y, x])

        wall_ijk = np.array(wall_ijk)
        wall_intensities = np.array(wall_intensities)
        
        # Statistiques d'intensité
        mean_intensity = np.mean(wall_intensities)
        std_intensity = np.std(wall_intensities)
        min_intensity = np.min(wall_intensities)
        
        # Seuils d'intensité avec marge
        intensity_margin = std_intensity * threshold_factor
        intensity_threshold_low = min_intensity * 0.8 - intensity_margin
        intensity_threshold_high = mean_intensity + 2.0 * std_intensity + intensity_margin
        
        # Calcul du rayon physique
        rayon_physique = rayon_estime
        base_radius_physique = rayon_physique * 0.7
        expanded_radius_physique = base_radius_physique + threshold_factor * base_radius_physique * 0.3

        radius_x_vox = int(np.ceil(expanded_radius_physique / spacing[0]))
        radius_y_vox = int(np.ceil(expanded_radius_physique / spacing[1]))
        radius_z_vox = int(np.ceil(expanded_radius_physique / spacing[2]))

        print(f"Rayon de recherche physique: {expanded_radius_physique:.2f} mm")
        print(f"Voxel equivalent :  (x:{radius_x_vox}, y:{radius_y_vox}, z:{radius_z_vox})")

        # Region growing initial
        for point_idx, (z, y, x) in enumerate(wall_ijk):
            z_min = max(0, z - radius_z_vox)
            z_max = min(mask.shape[0], z + radius_z_vox + 1)
            y_min = max(0, y - radius_y_vox)
            y_max = min(mask.shape[1], y + radius_y_vox + 1)
            x_min = max(0, x - radius_x_vox)
            x_max = min(mask.shape[2], x + radius_x_vox + 1)
            
            ref_intensity = volume_array[z, y, x]
            intensity_tolerance = std_intensity * (1.0 + threshold_factor)
            
            for lz in range(z_min, z_max):
                for ly in range(y_min, y_max):
                    for lx in range(x_min, x_max):
                        dx = (lx - x) * spacing[0]
                        dy = (ly - y) * spacing[1]
                        dz = (lz - z) * spacing[2]
                        dist_to_point = np.sqrt(dx**2 + dy**2 + dz**2)
                        
                        if dist_to_point <= expanded_radius_physique:
                            current_intensity = volume_array[lz, ly, lx]
                            if (current_intensity >= intensity_threshold_low and
                                current_intensity <= intensity_threshold_high and
                                abs(current_intensity - ref_intensity) <= intensity_tolerance):
                                mask[lz, ly, lx] = 1
        
        mask = mask.astype(np.uint8)

        # Expansion locale pour capturer les zones adjacentes manquées
        print("Expansion locale des zones adjacentes...")
        mask = self.expansion_locale_adjacente(mask, volume_array, n_iterations=3)

        # Filtrer par distance à la centerline
        print("Filtrage par distance à la centerline...")
        mask = self.filtrer_par_distance_centerline(mask, centerline_points, volumeInput, 
                                            rayon_estime=rayon_estime, 
                                            threshold_factor=threshold_factor)

        # 1. Fermeture morphologique adaptée à l'anisotropie
        taille_physique = 2.0 
        taille_x = max(int(np.round(taille_physique / spacing[0])), 1) 
        taille_y = max(int(np.round(taille_physique / spacing[1])), 1) 
        taille_z = max(int(np.round(taille_physique / spacing[2])), 1) 
        struct_el_aniso = np.ones((taille_z, taille_y, taille_x), dtype=np.uint8)

        # Fermeture plus agressive
        mask = ndimage.binary_closing(mask, structure=struct_el_aniso, iterations=2)
        
        # 2. NOUVEAU: Remplissage des trous slice par slice dans chaque direction
        print("Remplissage des trous dans le masque...")
        
        # Remplir les trous dans le plan XY (slice par slice en Z)
        for z in range(mask.shape[0]):
            mask[z, :, :] = ndimage.binary_fill_holes(mask[z, :, :])
        
        # Remplir les trous dans le plan XZ (slice par slice en Y)
        for y in range(mask.shape[1]):
            mask[:, y, :] = ndimage.binary_fill_holes(mask[:, y, :])
        
        # Remplir les trous dans le plan YZ (slice par slice en X)
        for x in range(mask.shape[2]):
            mask[:, :, x] = ndimage.binary_fill_holes(mask[:, :, x])
        
        # 3. NOUVEAU: Remplissage 3D des trous internes
        # Ceci remplit les trous complètement entourés
        mask = ndimage.binary_fill_holes(mask)
        
        # 4. Fermeture finale pour lisser
        mask = ndimage.binary_closing(mask, structure=struct_el_aniso, iterations=1)
        
        mask = mask.astype(np.uint8)

        # 5. Nettoyage des petites régions
        labeled_array, num_features = ndimage.label(mask)
        if num_features > 0:
            sizes = np.bincount(labeled_array.ravel())[1:]
            if len(sizes) > 0:
                threshold_size = np.max(sizes) * 0.05
                mask_cleaned = np.zeros_like(mask)
                for label in range(1, num_features + 1):
                    if sizes[label-1] >= threshold_size:
                        mask_cleaned[labeled_array == label] = 1
                mask = mask_cleaned
        
        print(f"Nombre final de voxels segmentés : {np.sum(mask)}")
        
        # Expansion finale
        mask_final = self.expanderSegmentation(mask, volumeInput, threshold_factor, rayon_estime)

        # Export vers segmentation
        labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
        slicer.util.updateVolumeFromArray(labelmapVolumeNode, mask_final)
        labelmapVolumeNode.CopyOrientation(volumeInput)
        
        segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("Paroi_Intestinale")
        if not segmentId:
            segmentId = segmentationNode.GetSegmentation().AddEmptySegment("Paroi_Intestinale")
            
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
            labelmapVolumeNode, 
            segmentationNode,
            segmentId
        )
        
        # Calcul DICE si ground truth disponible
        try:
            ground_truth = slicer.util.getNode('Test_slicer')
            if ground_truth:
                dice_score = self.calculerDICE(mask, ground_truth)
                print(f"Score DICE : {dice_score:.4f}")
        except:
            print("Ground truth non trouvé pour le calcul du DICE")
        
        slicer.mrmlScene.RemoveNode(labelmapVolumeNode)

        return mask
    
    def expanderSegmentation(self, mask, volumeInput, factor, rayon_estime=6):
        import numpy as np
        from scipy import ndimage
        
        # S'assurer que le masque d'entrée est en uint8
        mask = mask.astype(np.uint8)
        
        spacing = volumeInput.GetSpacing()
        rayon_voxels = int(rayon_estime / min(spacing))
        
        expansion_size = int((factor - 0.5) * rayon_voxels * 0.2)
        struct_element = ndimage.generate_binary_structure(3, 1)
        
        volume_array = slicer.util.arrayFromVolume(volumeInput)
        
        if expansion_size == 0:
            return mask
        elif expansion_size > 0:
            mask_expanded = ndimage.binary_dilation(mask, 
                                                structure=struct_element,
                                                iterations=expansion_size)
            mask_expanded = mask_expanded.astype(np.uint8)
            
            # Zone dilatée
            dilated_region = (mask_expanded & ~mask).astype(np.uint8)
            mean_intensity = np.mean(volume_array[mask == 1])
            std_intensity = np.std(volume_array[mask == 1])
            
            intensity_mask = ((volume_array >= mean_intensity - 2*std_intensity) & 
                            (volume_array <= mean_intensity + 2*std_intensity)).astype(np.uint8)
            
            # Application du masque d'intensité
            result = mask_expanded.copy()
            result[dilated_region == 1] = intensity_mask[dilated_region == 1]
            
            return result.astype(np.uint8)
        else:
            result = ndimage.binary_erosion(mask, 
                                        structure=struct_element,
                                        iterations=abs(expansion_size))
            return result.astype(np.uint8)
                                        
    def calculerDICE(self, segmentation, ground_truth):
        """Calcule le score DICE entre la segmentation et le ground truth"""
        # Seulement si on dispose du DICE score : Segmentation de Astrée en ref 
        import numpy as np
        
        # Convertir le ground truth en array numpy
        ground_truth_array = slicer.util.arrayFromVolume(ground_truth)
        # Binariser si nécessaire (au cas où ce ne sont pas des 0 et 1)
        ground_truth_array = (ground_truth_array > 0).astype(np.uint8)
        
        # Notre segmentation est déjà binaire, mais assurons-nous
        segmentation = segmentation.astype(np.uint8)
        
        # Calculer l'intersection
        intersection = np.sum(segmentation * ground_truth_array)
        
        # Calculer les sommes
        sum_seg = np.sum(segmentation)
        sum_gt = np.sum(ground_truth_array)
        
        # Calculer le DICE
        dice = (2.0 * intersection) / (sum_seg + sum_gt)
        
        return dice

    def mettreAJourSegmentation(self, volumeInput, centerline_points, wall_points, segmentationNode, threshold_factor, rayon_estime=6):
        """Met à jour la segmentation avec les points existants."""
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(volumeInput)

        # Créer la segmentation initiale
        mask = self.segmenterParRegionSimple(volumeInput, centerline_points, wall_points, segmentationNode, threshold_factor, rayon_estime)

        if mask is None:
            return False
        
        print(f"Après application du masque de trajectoire: {np.sum(mask)} voxels restants")
        
        # Créer un masque qui couvre tout le volume
        full_dims = volumeInput.GetImageData().GetDimensions()
        full_mask = np.zeros(full_dims[::-1], dtype=np.uint8)
        
        # Obtenir les limites actuelles du masque
        mask_shape = mask.shape
        
        # Assurez-vous que le masque peut s'insérer dans le volume complet
        z_max = min(full_mask.shape[0], mask_shape[0])
        y_max = min(full_mask.shape[1], mask_shape[1])
        x_max = min(full_mask.shape[2], mask_shape[2])
        
        # Copier le masque actuel dans une région du masque complet
        full_mask[0:z_max, 0:y_max, 0:x_max] = mask[0:z_max, 0:y_max, 0:x_max]
        
        # Appliquer l'expansion/contraction au masque complet
        full_mask_final = self.expanderSegmentation(full_mask, volumeInput, threshold_factor, rayon_estime)
        full_mask_final = full_mask_final.astype(np.uint8)
        
        # Supprimer tous les segments existants
        segmentation = segmentationNode.GetSegmentation()
        while segmentation.GetNumberOfSegments() > 0:
            segmentation.RemoveSegment(segmentation.GetNthSegmentID(0))
        segmentation.AddEmptySegment("Paroi_Intestinale")
        
        # Créer un labelmap avec les dimensions complètes du volume
        labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
        labelmapVolumeNode.SetName("FullVolumeLabelMap")
        
        # Mettre à jour avec notre masque complet
        slicer.util.updateVolumeFromArray(labelmapVolumeNode, full_mask_final)
        
        # Copier l'orientation et la géométrie du volume d'entrée
        labelmapVolumeNode.CopyOrientation(volumeInput)
        
        # S'assurer que le labelmap utilise les mêmes transformations que le volume
        labelmapVolumeNode.SetAndObserveTransformNodeID(volumeInput.GetTransformNodeID())
        
        # Importer le labelmap dans la segmentation
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
            labelmapVolumeNode, segmentationNode)
        
        # Configurer la géométrie de référence manuellement
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(volumeInput)
        
        # Nettoyer
        slicer.mrmlScene.RemoveNode(labelmapVolumeNode)
        
        # Configurer l'éditeur de segment à l'aide d'une autre méthode (compatible avec Slicer 5.6.2)
        try:
            # Passer directement au module SegmentEditor
            slicer.util.selectModule("SegmentEditor")
            
            # Obtenir le widget du SegmentEditor
            segEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self()
            if segEditorWidget:
                # Configurer le nœud de segmentation et le volume de référence
                segEditorWidget.setSegmentationNode(segmentationNode)
                segEditorWidget.setMasterVolumeNode(volumeInput)
                
                # Obtenir l'éditeur sous-jacent
                editor = segEditorWidget.editor
                if editor:
                    # Désactiver les masques et les restrictions de ROI
                    editorNode = segEditorWidget.mrmlSegmentEditorNode()
                    if editorNode:
                        # Utiliser des valeurs numériques au lieu de constantes nommées
                        editorNode.SetMaskMode(0)  # 0 = pas de masque / édition partout
                        editorNode.SetOverwriteMode(2)  # 2 = écraser tous les segments
        except Exception as e:
            print(f"Remarque: Configuration manuelle du SegmentEditor non essentielle: {str(e)}")
        
        return True
    
    def filtrer_par_distance_centerline(self, mask, centerline_points, volumeInput, rayon_estime=6, threshold_factor=0.5):
        """
        Garde uniquement les voxels du masque qui sont à moins de distance_max de la centerline
        Distance calculée en mm physiques pour gérer l'anisotropie
        """
        
        from scipy.spatial import cKDTree
        
        # Adapter la distance max selon le threshold_factor du slider
        # threshold_factor va de 0.0 (restrictif) à 1.0 (permissif)
        # On utilise une échelle entre 2.0x et 3.0x le rayon
        distance_factor = 2.0 + (threshold_factor * 1.0)  # Entre 2.0 et 3.0
        distance_max_mm = rayon_estime * distance_factor
        
        print(f"  Distance max autorisée: {distance_max_mm:.1f} mm (rayon {rayon_estime}mm × {distance_factor:.2f})")
        
        # Récupérer les points centerline en RAS (coordonnées physiques)
        centerline_ras = []
        for i in range(centerline_points.GetNumberOfPoints()):
            point = centerline_points.GetPoint(i)
            centerline_ras.append(point)
        
        centerline_ras = np.array(centerline_ras)
        
        # Créer un arbre KD pour recherche rapide (en coordonnées RAS)
        tree = cKDTree(centerline_ras)
        
        # Convertir les coordonnées IJK du masque en RAS
        ijkToRAS = vtk.vtkMatrix4x4()
        volumeInput.GetIJKToRASMatrix(ijkToRAS)
        
        # Obtenir tous les voxels segmentés
        segmented_coords_ijk = np.argwhere(mask > 0)  # z, y, x
        
        if len(segmented_coords_ijk) == 0:
            return mask
        
        # Convertir chaque voxel IJK en RAS
        segmented_coords_ras = []
        for z, y, x in segmented_coords_ijk:
            point_ijk = [x, y, z, 1.0]  # Attention à l'ordre : x, y, z pour VTK
            point_ras = [0, 0, 0, 1.0]
            ijkToRAS.MultiplyPoint(point_ijk, point_ras)
            segmented_coords_ras.append(point_ras[:3])
        
        segmented_coords_ras = np.array(segmented_coords_ras)
        
        # Calculer les distances en mm physiques
        distances, _ = tree.query(segmented_coords_ras)
        
        # Identifier les voxels à garder
        valid_indices = distances <= distance_max_mm
        
        # Créer le nouveau masque
        filtered_mask = np.zeros_like(mask)
        valid_coords = segmented_coords_ijk[valid_indices]
        filtered_mask[valid_coords[:, 0], valid_coords[:, 1], valid_coords[:, 2]] = 1
        
        removed_voxels = len(segmented_coords_ijk) - np.sum(valid_indices)
        removed_percent = 100 * removed_voxels / len(segmented_coords_ijk) if len(segmented_coords_ijk) > 0 else 0
        print(f"  Voxels conservés: {np.sum(valid_indices)}/{len(segmented_coords_ijk)} ({removed_percent:.1f}% éliminés)")
        
        return filtered_mask.astype(np.uint8)
    
    def detecterPointsParoi(self, noeudMarkups, volumeInput, rayon_estime=6):
        """
        Detecte les points de la paroi a partir de la centerline.
        Retourne les points de la paroi ou None si la detection echoue
        """
        import numpy as np
        
        points = self.obtenirPointsDeLaCourbe(noeudMarkups)
        if points is None or points.GetNumberOfPoints() < 2:
            print("Pas assez de points pour tracer la courbe.")
            return None
                
        progressDialog = slicer.util.createProgressDialog(
            windowTitle="Détection de la paroi",
            labelText="Analyse en cours...",
            maximum=points.GetNumberOfPoints(),
            cancelButton=True
        )
        
        wall_points = vtk.vtkPoints()
        wall_cells = vtk.vtkCellArray()
        point_count = 0
        
        spacing = volumeInput.GetSpacing()
        search_distance = min(20, rayon_estime / min(spacing) * 0.8) # Utiliser x fois le rayon pour la recherche de parois

        print(f"Distance de recherche : {search_distance} voxels")
    
        try:
            for i in range(points.GetNumberOfPoints() - 1):
                progressDialog.setValue(i)
                progressDialog.setLabelText(f"Analyse du point {i+1}/{points.GetNumberOfPoints()-1}...")
                slicer.app.processEvents()
                
                if progressDialog.wasCanceled:
                    return None
                
                p1 = np.array(points.GetPoint(i))
                p2 = np.array(points.GetPoint(i + 1))
                vecteur = p2 - p1
                vecteur = vecteur / np.linalg.norm(vecteur)
                vecteur_perpendiculaire = np.array([-vecteur[1], vecteur[0], 0])
                
                current_points = []
                current_distances = []
                
                angles = np.linspace(0, 2*np.pi, 32) # C'est ici qu'on echantillonnne le nombre de rayon que l'on envoi a partir du points [0, 2pi]
                for angle in angles:
                    rot_matrix = np.array([[np.cos(angle), -np.sin(angle), 0],
                                        [np.sin(angle), np.cos(angle), 0],
                                        [0, 0, 1]])

                    search_vector = np.dot(rot_matrix, vecteur_perpendiculaire) * search_distance
                    end_point = p1 + search_vector
                    intensities = self.sampleIntensitiesAlongLine(p1, end_point, volumeInput)
                    wall_position = self.trouverParoi(intensities, p1, end_point)
                    
                    if wall_position is not None:
                        distance = np.linalg.norm(wall_position - p1)
                        current_points.append(wall_position)
                        current_distances.append(distance)
                
                if len(current_distances) > 0:
                    median_distance = np.median(current_distances)
                    distance_threshold = median_distance * 0.3
                    
                    for point, distance in zip(current_points, current_distances):
                        if distance > distance_threshold:
                            point_id = wall_points.InsertNextPoint(point)
                            cell = vtk.vtkVertex()
                            cell.GetPointIds().SetId(0, point_count)
                            wall_cells.InsertNextCell(cell)
                            point_count += 1
        finally:
            progressDialog.close()
            
        if point_count == 0:
            print("Aucun point de paroi détecté!")
            return None
            
        return wall_points
    
    def segmenterGraisse(self, fatVolumeInput, lesionVolumeInput, pointsNode, segmentationNode, lesionSegNode=None):
        import numpy as np 
        from scipy import ndimage
        
        # Récupération du masque de la lésion
        lesion_mask = None 
        if lesionSegNode is not None: 
            labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
            slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(
                lesionSegNode, labelmapVolumeNode, lesionVolumeInput)
            lesion_mask = slicer.util.arrayFromVolume(labelmapVolumeNode)
            slicer.mrmlScene.RemoveNode(labelmapVolumeNode)
            print("Masque de lésion chargé pour guider la segmentation de graisse")
        
        # Récupération des données du volume et des espacements
        volume_array = slicer.util.arrayFromVolume(fatVolumeInput)
        spacing = fatVolumeInput.GetSpacing()
        print(f"Espacement des voxels: {spacing[0]:.2f} x {spacing[1]:.2f} x {spacing[2]:.2f} mm")

        
        # Calculer le ratio d'anisotropie pour ajuster les opérations morphologiques
        # Typiquement Z a un espacement plus grand
        xy_spacing = min(spacing[0], spacing[1])
        z_spacing = spacing[2]
        anisotropy_ratio = z_spacing / xy_spacing
        print(f"Ratio d'anisotropie Z/XY: {anisotropy_ratio:.2f}")
        
        # Créer un masque vide
        mask = np.zeros_like(volume_array, dtype=np.uint8)
        
        # Matrice de transformation RAS vers IJK
        rasToIJK = vtk.vtkMatrix4x4()
        fatVolumeInput.GetRASToIJKMatrix(rasToIJK)

        # Collecte des points et intensités
        fat_intensities = []
        fat_points_ijk = []

        for i in range(pointsNode.GetNumberOfControlPoints()): 
            pos = [0, 0, 0]
            pointsNode.GetNthControlPointPosition(i, pos) 

            posRAS = list(pos) + [1.0]
            posIJK = [0, 0, 0, 1.0]
            rasToIJK.MultiplyPoint(posRAS, posIJK)
            x, y, z = [int(round(posIJK[j])) for j in range(3)]

            if (0 <= z < mask.shape[0] and
                0 <= y < mask.shape[1] and 
                0 <= x < mask.shape[2]):
                intensity = volume_array[z, y, x]
                fat_intensities.append(intensity) 
                fat_points_ijk.append([z, y, x]) 
        
        if not fat_intensities:
            print("Aucun point valide pour la segmentation de graisse") 
            return False

        fat_intensities = np.array(fat_intensities)
        fat_points_ijk = np.array(fat_points_ijk)

        # Analyse statistique 
        mean_intensity = np.mean(fat_intensities) 
        std_intensity = np.std(fat_intensities)
        
        # Définir la plage d'intensité pour la graisse
        intensity_min = mean_intensity - 3.0 * std_intensity
        intensity_max = mean_intensity + 3.0 * std_intensity
        
        print(f"Points de graisse détectés: {len(fat_intensities)}")
        print(f"Intensité moyenne: {mean_intensity:.2f} ± {std_intensity:.2f}")
        print(f"Plage d'intensités: [{intensity_min:.2f}, {intensity_max:.2f}]")

        # Créer un masque d'intensité
        intensity_mask = np.zeros_like(volume_array, dtype=np.uint8)
        if lesion_mask is not None: 
            intensity_mask[(volume_array >= intensity_min) & 
                        (volume_array <= intensity_max) &
                        (lesion_mask == 0)] = 1 
        else: 
            intensity_mask[(volume_array >= intensity_min) &
                        (volume_array <= intensity_max)] = 1 
        
        # Créer un élément structurant anisotrope pour respecter les proportions du volume
        # Si Z a un espacement plus grand, nous voulons moins de dilatation en Z
        z_scale = max(1, int(round(anisotropy_ratio)))
        struct_size = (
            max(1, min(3, int(round(5 / spacing[2])))),  # Z (moins de dilatation si grand espacement)
            3,  # Y
            3   # X
        )
        print(f"Taille de l'élément structurant anisotrope: {struct_size}")
        struct_aniso = np.ones(struct_size, dtype=np.uint8)
        
        # Initialiser avec les points de l'utilisateur
        seed_mask = np.zeros_like(volume_array, dtype=np.uint8)
        for z, y, x in fat_points_ijk: 
            seed_mask[z, y, x] = 1
        
        # Si on a une lésion, utiliser sa bordure comme source additionnelle
        if lesion_mask is not None:
            # Créer une fine bordure autour de la lésion
            border_struct = ndimage.generate_binary_structure(3, 1)
            lesion_border = ndimage.binary_dilation(
                lesion_mask > 0, 
                structure=border_struct,
                iterations=1
            ) & ~(lesion_mask > 0)
            
            # Ajouter les points de la bordure qui correspondent à la graisse
            border_points = np.where(lesion_border & intensity_mask)
            for z, y, x in zip(*border_points):
                seed_mask[z, y, x] = 1
        
        # Region growing avec contrôle d'anisotropie
        fat_mask = seed_mask.copy()
        max_iterations = 25
        
        # Croissance dans le plan XY et Z séparément
        # D'abord dilatation dans le plan XY
        for iteration in range(max_iterations):
            # Structure dans le plan XY uniquement
            struct_xy = np.zeros((1, 3, 3), dtype=np.uint8)
            struct_xy[0, 1, 1] = 1
            struct_xy[0, 0, 1] = 1
            struct_xy[0, 2, 1] = 1
            struct_xy[0, 1, 0] = 1
            struct_xy[0, 1, 2] = 1
            
            # Dilater dans le plan XY
            dilated_xy = ndimage.binary_dilation(fat_mask, structure=struct_xy)
            new_mask_xy = (dilated_xy & intensity_mask).astype(np.uint8)
            
            # Si lésion présente, exclure
            if lesion_mask is not None:
                new_mask_xy = new_mask_xy & (lesion_mask == 0)
            
            # Si plus de croissance dans XY, on arrête
            if np.array_equal(new_mask_xy, fat_mask):
                break
                
            fat_mask = new_mask_xy
        
        # Ensuite, croissance plus contrôlée en Z
        # Moins d'itérations en Z pour limiter la propagation excessive
        z_iterations = max(3, int(max_iterations / anisotropy_ratio))
        print(f"Itérations en Z: {z_iterations}")
        
        for iteration in range(z_iterations):
            # Structure en Z uniquement
            struct_z = np.zeros((3, 1, 1), dtype=np.uint8)
            struct_z[0, 0, 0] = 1
            struct_z[1, 0, 0] = 1
            struct_z[2, 0, 0] = 1
            
            # Dilater en Z
            dilated_z = ndimage.binary_dilation(fat_mask, structure=struct_z)
            new_mask_z = (dilated_z & intensity_mask).astype(np.uint8)
            
            # Contrainte plus stricte en Z pour éviter les pics
            # Limiter la croissance en Z aux voxels qui ont un support dans le plan XY
            support_xy = ndimage.binary_dilation(
                new_mask_z, 
                structure=struct_xy,
                iterations=1
            )
            new_mask_z = new_mask_z & support_xy
            
            # Si lésion présente, exclure
            if lesion_mask is not None:
                new_mask_z = new_mask_z & (lesion_mask == 0)
            
            # Si plus de croissance en Z, on arrête
            if np.array_equal(new_mask_z, fat_mask):
                break
                
            fat_mask = new_mask_z
        
        # Post-traitement pour lissage et amélioration de la forme
        
        # 1. Fermeture pour combler les trous (adaptée à l'anisotropie)
        fat_mask = ndimage.binary_closing(
            fat_mask, 
            structure=struct_aniso,
            iterations=2
        ).astype(np.uint8)
        
        # 2. Ouverture pour enlever les petites excroissances
        fat_mask = ndimage.binary_opening(
            fat_mask, 
            structure=struct_aniso,
            iterations=1
        ).astype(np.uint8)
        
        # 3. Supprimer les petites régions isolées
        labeled_array, num_features = ndimage.label(fat_mask)
        if num_features > 1:
            sizes = np.bincount(labeled_array.ravel())[1:]
            
            # Ne garder que les plus grandes régions
            threshold_size = max(10, int(np.max(sizes) * 0.1))
            mask_cleaned = np.zeros_like(fat_mask)
            
            for label in range(1, num_features + 1):
                if sizes[label-1] >= threshold_size:
                    mask_cleaned[labeled_array == label] = 1
                    
            fat_mask = mask_cleaned.astype(np.uint8)
        
        # 4. Lissage final adapté à l'anisotropie
        fat_mask = ndimage.binary_closing(
            fat_mask, 
            structure=struct_aniso,
            iterations=1
        ).astype(np.uint8)
        
        print(f"Nombre final de voxels segmentés: {np.sum(fat_mask)}")
        
        # Vérifier si le segment "Creeping_Fat" existe déjà
        segmentId = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("Creeping_Fat")
        if not segmentId:
            # Si le segment n'existe pas, le créer
            segmentId = segmentationNode.GetSegmentation().AddEmptySegment("Creeping_Fat")
            # Définir la couleur du segment
            segment = segmentationNode.GetSegmentation().GetSegment(segmentId)
            segment.SetColor(1.0, 1.0, 0.0)  # Jaune
        else:
            # Si le segment existe, juste mettre à jour
            print("Mise à jour du segment Creeping_Fat existant")
        
        # Créer un volume temporaire pour le labelmap
        labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
        labelmapVolumeNode.SetName("TempLabelMap_Fat")
        slicer.util.updateVolumeFromArray(labelmapVolumeNode, fat_mask)
        labelmapVolumeNode.CopyOrientation(fatVolumeInput)  # <-- Changé
        
        # Importer dans le segment existant
        segmentIds = vtk.vtkStringArray()
        segmentIds.InsertNextValue(segmentId)
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
            labelmapVolumeNode, 
            segmentationNode,
            segmentIds
        )
        
        # Nettoyer
        slicer.mrmlScene.RemoveNode(labelmapVolumeNode)
        
        return True

##################################################################################
##################################################################################
# CrohnSegmentTest
##################################################################################
##################################################################################

class CrohnBOOSTTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_CrohnSegment1()

    def test_CrohnSegment1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("CrohnSegment1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = CrohnBOOSTLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")