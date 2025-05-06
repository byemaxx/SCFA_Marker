# SCFA Marker

SCFA Marker is a user-friendly tool for batch processing and marking SCFA (Short-Chain Fatty Acids) quantification results from CSV files. It provides a modern GUI, flexible parameter settings, and clear output for scientific data analysis.

**It is fully compatible with CSV files exported from [Skyline](https://skyline.ms/), a widely used mass spectrometry data analysis software.**

## Main Features
- **Batch Processing**: Select and process multiple CSV files at once.
- **Dilution Factor**: Apply a user-defined dilution factor to all quantification results.
- **Standard Range Marking**: Mark each result as In, High, or Low based on user-defined standard range coefficients.
- **Group Splitting**: Optionally split results by group and generate grouped Excel sheets.
- **Modern GUI**: Intuitive PyQt5 interface with drag-and-drop and progress dialog.
- **Clear Output**: Generates Excel files with marked and grouped results, and a scrollable result summary.
- **Skyline Compatibility**: Directly supports the typical output format of Skyline, making it easy to process your mass spectrometry quantification results.

## Parameter Definitions & Effects
| Parameter           | Definition                                                                 | Effect on Results                                                                                 |
|---------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| Dilution Factor     | Multiplies all quantification values. Default is 1 (no adjustment).        | If your sample was diluted before measurement, enter the dilution factor (e.g., 2, 5, etc.).      |
| Min Coefficient     | Multiplies the minimum value of the standard range. Default is 0.8.        | Expands or contracts the lower bound for marking results as In/Low.                               |
| Max Coefficient     | Multiplies the maximum value of the standard range. Default is 1.5.        | Expands or contracts the upper bound for marking results as In/High.                              |
| Split by Group      | If enabled, results are split by specified groups.                         | Each group is saved as a separate sheet in the grouped Excel file.                                |
| Group List          | Comma-separated list of group names (e.g., WT, KO).                        | Only these groups will be analyzed and split if group splitting is enabled.                       |
| Control Group       | The group to be prioritized in output.                                     | This group will appear first in grouped results.                                                  |

## Example Input Table

> **Note:** The following table format is compatible with Skyline CSV exports.

| Molecule    | Replicate | Quantification | Sample Type | Analyte Concentration | Exclude From Calibration |
|-------------|-----------|---------------|-------------|----------------------|-------------------------|
| C2-Acetate  | WT_1      | 12.3 uM       | Unknown     | 10.0                 | False                   |
| C2-Acetate  | WT_2      | 11.8 uM       | Sample      | 10.0                 | False                   |
| C2-Acetate  | KO_1      | 8.5 uM        | Sample      | 10.0                 | False                   |
| C2-Acetate  | KO_2      | 7.9 uM        | Sample      | 10.0                 | False                   |
| C2-Acetate  | STD_1     | 10.0 uM       | Standard    | 10.0                 | False                   |

## Example Output Table (Excel, Marked Sheet)
| Molecule    | Replicate | Quantification | Standard Range | Standard | Standard Status |
|-------------|-----------|----------------|---------------|----------|-----------------|
| C2-Acetate  | WT_1      | 12.3           | 8.0 - 15.0    | *        | High            |
| C2-Acetate  | WT_2      | 11.8           | 8.0 - 15.0    |          | In              |
| C2-Acetate  | KO_1      | 8.5            | 8.0 - 15.0    |          | In              |
| C2-Acetate  | KO_2      | 7.9            | 8.0 - 15.0    | *        | Low             |

- **Standard Range** is calculated as: [Standard Min × Min Coefficient] to [Standard Max × Max Coefficient].
- **Standard** column: blank means "In", * means "Out" (High or Low).
- **Standard Status**: In, High, or Low.

## Calculation Process

### 1. Standard Range Calculation
- Filter standard samples where:
  - Sample Type = "Standard"
  - Exclude From Calibration = "false"
- Calculate standard range:
  - Min value = minimum of standard samples' Analyte Concentration
  - Max value = maximum of standard samples' Analyte Concentration
- Apply coefficients to create adjusted range:
  - Adjusted Min = Min value × Min Coefficient (default: 0.8)
  - Adjusted Max = Max value × Max Coefficient (default: 1.5)

### 2. Sample Status Determination
- For each sample:
  - Apply dilution factor to Quantification value if specified
  - Compare adjusted value with standard range:
    - If value < Adjusted Min: Marked as "Low" (*)
    - If value > Adjusted Max: Marked as "High" (*)
    - If Adjusted Min ≤ value ≤ Adjusted Max: Marked as "In" (blank)
  - Note: Samples marked with (*) are considered "Out" of range

### 3. Group Processing (Optional)
- When group splitting is enabled:
  - Parse Replicate column to identify groups (e.g., "WT_1" → "WT")
  - For each molecule:
    - Create pivot table:
      - Rows: Replicate numbers (e.g., "1", "2")
      - Columns: Groups (e.g., "WT", "KO")
      - Values: Quantification values
    - Sort columns to show control group first
    - Generate separate sheets for each molecule-group combination

## Typical Workflow
1. Launch the program: `python SCFA_Marker.py`
2. Select one or more CSV files and an output directory.
3. Set parameters as needed (dilution, coefficients, group options).
4. Click "Start Processing".
5. Review results in the scrollable dialog and find output Excel files in the selected directory.

## Output Files
- **MARKED_*.xlsx**: All processed and marked results. Each molecule is a sheet; the "All" sheet contains all data.
- **GROUPED_*.xlsx**: (If group splitting is enabled) Results split by group, each group as a separate sheet. The index column is named "Replicate".

