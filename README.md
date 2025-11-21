<div align="center">

# CrohnBOOST 
![CrohnBOOST Logo](Resources/Icons/icon_boost.png)

</div>

**CrohnBOOST** (BOwel Open-source Segmentation Tool) is a 3D Slicer extension for semi-automated segmentation of intestinal lesions and creeping fat in Crohn's disease using MRI sequences.

Developed at **IADI Laboratory, INSERM** (Université de Lorraine, Nancy, France) as part of PhD research in medical image processing.


## 📋 Overview

CrohnBOOST provides radiologists and researchers with advanced tools for:
- **Semi-automated intestinal wall segmentation** using centerline-guided region growing
- **Creeping fat segmentation** guided by user-placed points
- **Interactive refinement** with sensitivity/radius sliders and manual paint/erase tools 
- **Segmentation export** for downstream quantitative analysis pipelines


---
## ✨ Features

### 🎯 Lesion Segmentation
- **Centerline-based approach**: Draw a simple centerline through the lesion
- **Automatic wall detection**: Radial sampling with intensity-based wall detection
- **Smart region growing**: Adaptive thresholding with spatial constraints
- **Interactive adjustment**: Sensitivity and radius sliders with one-click update

### 🧈 Creeping Fat Segmentation
- **Seed-based growing**: Place control points in fat regions
- **Multi-sequence support**: Uses dedicated DIXON fat sequences
- **Lesion-aware**: Automatically excludes intestinal wall from fat segmentation
- **Anisotropic processing**: Respects voxel spacing for accurate 3D growth

### 🛠️ Save 

---

## 📦 Installation

### Prerequisites
- **3D Slicer** 5.6.2 or later ([Download here](https://www.slicer.org/))
- Python packages (automatically installed):
  - `scipy >= 1.7.0`
  - `numpy >= 1.21.0`
  - `vtk` (included with Slicer)

### Installation Steps

#### Method : Manual Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/AntoineKneib/CrohnBOOST.git
   ```

2. In 3D Slicer:
   - Go to `Edit` → `Application Settings` → `Modules`
   - Add the path to the `CrohnBOOST` folder
   - Restart Slicer

3. The module should appear under `Modules` → `Crohn's Disease` → `CrohnBOOST`

---

## 🚀 Quick Start

### Step 1: Load Your MRI Data
1. Load your MRI sequences (Ensure volumes are co-registered)

### Step 2: Segment the Intestinal Lesion

1. **Select Input Volume**: Choose your MRI sequence
2. **Draw Centerline**: Click `Place Centerline` and trace through the lesion center
3. **Adjust Parameters**:
   - `Intestinal Radius`: Estimate of bowel diameter (default: 6mm)
   - `Sensitivity`: Control segmentation aggressiveness (0-100%, default : 50%)
4. **Click `Segmentation`**: Automatic wall detection and segmentation
5. **Refine**: Use the sensitivity slider and click `Apply` to update

### Step 3: Segment Creeping Fat

1. **Select Fat Volume**: Choose your DIXON fat sequence (inputSelector2)
2. **Place Fat Points**: Click `Place Fat Points` and add 3-5 points in the fat regions
3. **Click `Segment Fat`**: Automatic fat segmentation excluding the lesion
4. **Review**: Fat appears in yellow, lesion in beige

### Step 4: Manual Refinement (Optional)
- Use `Paint` and `Erase` tools for fine-tuning
- Compatible with 3D Slicer's Segment Editor

### Step 5: Export Results
- Click `Save Segmentation` to export as NIFTI labelmap
- Compatible with downstream quantitative analysis tools

---

## 📊 Example Results

| Centerline Drawing | Automatic Segmentation | Fat Segmentation |
|:------------------:|:----------------------:|:----------------:|
| ![Centerline](docs/images/centerline_example.png) | ![Lesion](docs/images/lesion_seg.png) | ![Fat](docs/images/fat_seg.png) |

*Example: Segmentation of terminal ileum Crohn's disease with creeping fat*

---

## 🎓 Scientific Background

### Algorithm Overview

#### Lesion Segmentation Pipeline
1. **Centerline sampling**: Extract equidistant points along user-drawn curve
2. **Radial wall detection**: Cast 32 rays perpendicular to centerline
3. **Intensity-based detection**: Gradient + threshold analysis
4. **Region growing**: Expand from wall points with intensity constraints
5. **Distance filtering**: Keep only voxels near centerline trajectory
6. **Hole filling**: Multi-directional slice-by-slice + 3D filling
7. **Morphological refinement**: Closing + component analysis

#### Fat Segmentation Pipeline
1. **Intensity profiling**: Characterize fat signal from seed points
2. **Anisotropic growth**: Separate XY (in-plane) and Z (through-plane) expansion
3. **Lesion masking**: Exclude intestinal wall from fat regions
4. **Connected component filtering**: Keep largest coherent fat regions

---

## 📖 Documentation

### UI Elements Reference

| Element | Description |
|---------|-------------|
| **inputSelector** | T1-DIXON water sequence for lesion segmentation |
| **inputSelector2** | T1-DIXON fat sequence for fat segmentation |
| **Radius Slider** | Estimated intestinal radius (1-20mm) |
| **Sensitivity Slider** | Segmentation aggressiveness (0-100%) |
| **Place Centerline** | Draw centerline through lesion |
| **Segment** | Launch automatic lesion segmentation |
| **Apply Segmentation** | Update with current slider values |
| **Place Fat Points** | Mark seed points in creeping fat |
| **Segment Fat** | Launch fat segmentation |

### Parameter Guidelines

| Parameter | Typical Range | Notes |
|-----------|---------------|-------|
| Intestinal Radius | 4-8mm | Smaller for strictures, larger for dilated bowel |
| Sensitivity (lesion) | 40-60% | Lower = conservative, Higher = aggressive |
| Fat seed points | 3-10 points | More points = better coverage |

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🐛 Known Limitations

- Requires manual centerline drawing (not fully automatic)
- Best results with high-resolution MRI (< 1mm in-plane)
- Fat segmentation requires DIXON or fat-saturated sequences
- Performance depends on image quality, contrast, and user input.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 📚 Citation

If you use CrohnBOOST in your research, please cite:

```bibtex
@software{crohnboost2025,
  author       = {Kneib, Antoine},
  title        = {CrohnBOOST: Semi-Automated Segmentation Tool for Crohn's Disease MRI},
  year         = {2025},
  publisher    = {GitHub},
  url          = {https://github.com/YourUsername/CrohnBOOST},
  institution  = {IADI Laboratory, INSERM, Université de Lorraine}
}
```

*Publication in preparation - citation will be updated upon acceptance*

---

## 👤 Author

**Antoine KNEIB**  
PhD Student in Medical Image Processing  
IADI Laboratory, INSERM U1254  
Université de Lorraine, Nancy, France

📧 Contact: antoine.kneib@univ-lorraine.fr  
🔗 LinkedIn: [https://www.linkedin.com/in/antoine-kneib-b173131b8/]  

---

## 🙏 Acknowledgments

- **Supervisor**: [Freddy and team names]
- **IADI Laboratory** for research support
- **3D Slicer Community** for the amazing platform
- **Collaborators**: [List key collaborators]
- Funded by: [Grant information if applicable]

---

## 📊 Project Status

![GitHub release](https://img.shields.io/github/v/release/YourUsername/CrohnBOOST)
![License](https://img.shields.io/github/license/YourUsername/CrohnBOOST)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![3D Slicer](https://img.shields.io/badge/3D%20Slicer-5.6.2+-green.svg)

**Status**: 🚧 Active Development  
**Version**: 1.0.0-beta  
**Last Updated**: November 2025

---
If you find CrohnBOOST useful, please consider giving it a star! ⭐
---
<div align="center">
**Made with ❤️ for the Crohn's disease research community**
</div>
