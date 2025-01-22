# n-gram Analysis Tool

Welcome to the n-gram Analysis Tool! This Streamlit application allows users to perform n-gram analysis on advertising data extracted from bulk operations files from the Amazon Advertising Console.

## Features

- Analyze Customer Search Terms for Sponsored Product Campaigns.
- Generate n-gram reports (Monograms, Bigrams, Trigrams).
- Support for excluding specific brand terms during analysis.
- Handles empty datasets and generates detailed error reports.

## Installation

To set up the application locally, follow these steps:

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd ngram-analysis-tool
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   streamlit run ngram_analysis_tool.py
   ```

## Usage

1. Go to the [Bulk Operations](https://assets.zyrosite.com/m5KLvqrBjzHJbZkk/ngram_bulk_needs-YrDqqxMLQrtekppJ.png) section in your Amazon Advertising Console.
2. Request a bulk operations file and upload it using the application.
3. Specify the SKU(s) or use the full dataset for analysis.
4. Optionally exclude brand terms from the analysis.
5. Download the generated n-gram analysis reports.

## Contact

For questions or support, contact me at: [hola@soypat.es](mailto:hola@soypat.es)

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
