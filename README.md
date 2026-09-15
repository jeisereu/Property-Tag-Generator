## Converts a CSV with certain columns into a Property Tag formatted for DICT R5
Generates Property Tags with a file called **properties.csv** which includes these columns:
- Property Number
- Description (Includes brand name, model, and serial number) (ex. "Monitor, Gaming Monitor Gamdias Model: ATLAS VH22F SN: VH22F02210201091")
- Cost
- Acquisition Date

There are other supposed information, such as **Person Accountable**, however, currently it only defaults to a default name of someone that holds most properties in DICT Catanduanes Regional office.

## Output
- Outputs all property tag/cards as PNG images individually at the output_property_tags folder
- Outputs batches of property tag/cards as PDF (individual pages), hardcoded as 450 max pages per PDF.
- Outputs another PDF where there's as many property cards in 3 columns, one inch height each, in A4 pages.

## Setup and Execution
- **Install dependencies first on virtual environment, maybe global for all I care LOL using `python -m pip install -r requirements.txt`.**
- **First two outputs are done by running `python generate_pc.py` and for the 3rd listed output, run `python generate_a4_searchable_pdf.py`.**

*Code is messy as hell, has a lot of arbitrary rules because the data was very non-uniform on the description column from the ICF.*
