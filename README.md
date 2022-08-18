# Feature Tracing

Multifunction GUI application designed to perform feature tracing on solar features. 

## Installation

First, ensure you have Python <3.7 installed, along with pip. 

Clone the repository with

```bash
git clone https://github.com/Pixadus/FeatureAnalysis.git
```

then open the folder. Install all Python requirements with 

```bash
pip install -r requirements.txt
```

Run the program using

```bash
python main.py
```

## Usage

FeatureAnalysis uses `.fits` files to store image data. A few sample `.fits` files are located in the `data/images/` directory.

Descriptions of the application tabs:

- **Preprocessing:** apply image operations such as Gaussian smoothing, sharpening, or isolating features via the Rolling hough transform.
- **Tracing:** the bread and butter of the application, where you can automatically or manually trace curvilinear features.
- **Analysis:** characterizing previously traced data, including length, breadth and custom parameters.
- **Optimization:** identifying an "ideal" parameter set that most closely matches a manual tracing.
- **Helper functions:** currently, .fits image editing (incl. cropping and rotation) and converting images stored in IDL .sav files to .fits.
