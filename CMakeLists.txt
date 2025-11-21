cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(CrohnSegment)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/CrohnSegment")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "KNEIB Antoine (IADI), ODILLE Freddy (IADI), ")
set(EXTENSION_DESCRIPTION "Crohn Segmentation semi-automatic tool for clinician ")
set(EXTENSION_ICONURL "https://www.example.com/Slicer/Extensions/CrohnSegment.png")
set(EXTENSION_SCREENSHOTURLS "https://www.example.com/Slicer/Extensions/CrohnSegment/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(CrohnSegment)
add_subdirectory(Crohn_Segmnet)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
