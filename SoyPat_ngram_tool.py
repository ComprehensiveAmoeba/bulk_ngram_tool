import streamlit as st
import pandas as pd
import re
import datetime
from nltk import bigrams, trigrams
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk
import base64
from io import BytesIO
import ssl

# Temporarily bypass SSL verification
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required nltk resources with a manual check
try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet")

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

# Add logo and app description
logo_url = "https://assets.zyrosite.com/m5KLvqrBjzHJbZkk/soypat_logo_white_bg-A0x11BXpQ0Tr9o5B.png"
website_url = "https://www.soypat.es"

st.markdown(f'''
    <div style="text-align: center;">
        <a href="{website_url}" target="_blank">
            <img src="{logo_url}" style="max-width: 100%; height: auto;">
        </a>
    </div>
''', unsafe_allow_html=True)


st.title("n-gram analysis tool")

st.markdown(
    """
    **Description:**
    To use this tool, go to the Bulk Operations section in the Ad Console and request a file like the one shown in this [screenshot](https://assets.zyrosite.com/m5KLvqrBjzHJbZkk/ngram_bulk_needs-YrDqqxMLQrtekppJ.png).
    Upload the file below to perform n-gram analysis.
    """
)

# Define tokenize and clean text function using regex instead of Punkt tokenizer
def clean_tokenize(text, stop_words=set()):
    lemmatizer = WordNetLemmatizer()

    # Tokenize using regular expression to split words
    tokens = re.findall(r'\b\w+\b', text.lower())
    cleaned_tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha() and token not in stop_words]
    return cleaned_tokens

# Define function to aggregate data for n-grams
def aggregate_ngrams(data, ngram_func, stop_words):
    data["ngrams"] = data["Customer Search Term"].apply(lambda x: list(ngram_func(clean_tokenize(x, stop_words))))
    ngrams_expanded = data.explode("ngrams")
    if not ngrams_expanded.empty:
        aggregated = ngrams_expanded.groupby("ngrams")[
            ["Impressions", "Clicks", "Spend", "Sales", "Units"]].sum().reset_index()
        aggregated["CTR"] = aggregated["Clicks"] / aggregated["Impressions"]
        aggregated["Conversion Rate"] = aggregated["Units"] / aggregated["Clicks"]
        aggregated["ACOS"] = aggregated["Spend"] / aggregated["Sales"]
        aggregated["CPA"] = aggregated["Spend"] / aggregated["Units"]
        aggregated["CPC"] = aggregated["Spend"] / aggregated["Clicks"]

        return aggregated.sort_values(by="Spend", ascending=False)
    else:
        return pd.DataFrame()

# Set up stop words
stop_words = set(stopwords.words("english"))
additional_stops = {"in", "for", "the", "of", "if", "when", "and", "de", "para"}
stop_words.update(additional_stops)

# File upload and n-gram analysis
data_file = st.file_uploader("Upload Bulk Sheet with Sponsored Products Campaigns", type="xlsx")
sku_mode = st.radio("Select SKU analysis mode:", ["Full Bulk Sheet", "Specific SKUs"])
sku_input = ""

if sku_mode == "Specific SKUs":
    sku_input = st.text_area("Enter SKUs (one per line)")
brand_exclusions = st.text_area("Optionally enter brand terms to exclude (one per line)")

if st.button("Perform n-gram analysis"):
    if data_file:
        bulk_data = pd.ExcelFile(data_file)
        sp_campaign_sheets = [sheet for sheet in bulk_data.sheet_names if "Sponsored Products Campaigns" in sheet]
        campaign_to_sku = {}

        for sheet in sp_campaign_sheets:
            campaigns_df = bulk_data.parse(sheet)
            campaigns_df = campaigns_df[campaigns_df["SKU"].notnull()]
            for _, row in campaigns_df.iterrows():
                campaign_name = row["Campaign Name (Informational only)"]
                sku = row["SKU"]
                campaign_to_sku[campaign_name] = sku

        sp_search_term_sheet = "SP Search Term Report"
        search_term_data = bulk_data.parse(sp_search_term_sheet)

        if sku_mode == "Specific SKUs":
            selected_skus = set(sku.upper() for sku in sku_input.splitlines())
            campaigns_to_include = [
                campaign for campaign, sku in campaign_to_sku.items() if sku.upper() in selected_skus
            ]

            if not campaigns_to_include:
                st.error("No campaigns found for the specified SKUs.")
                unmapped_skus = selected_skus - set(sku.upper() for sku in campaign_to_sku.values())

                # Create error report
                error_report = pd.DataFrame({"Unmapped SKUs": list(unmapped_skus)})
                mapping_report = pd.DataFrame.from_dict(campaign_to_sku, orient="index", columns=["SKU"]).reset_index()
                mapping_report.rename(columns={"index": "Campaign Name (Informational only)"}, inplace=True)

                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    error_report.to_excel(writer, sheet_name="Unmapped SKUs", index=False)
                    mapping_report.to_excel(writer, sheet_name="SKU to Campaign Mapping", index=False)

                timestamp = datetime.datetime.now().strftime("%Y-%m-%S_%H-%M-%S")
                filename = f"error_report_{timestamp}.xlsx"

                st.write("SKUs not found in the dataset. Download the error report below:")
                output.seek(0)
                b64 = base64.b64encode(output.read()).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download Error Report</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                search_term_data = search_term_data[search_term_data["Campaign Name (Informational only)"].isin(campaigns_to_include)]

        if search_term_data.empty:
            st.error("The filtered dataset is empty. Please check your input SKUs and campaign mappings.")

            # Create empty dataset report
            mapping_report = pd.DataFrame.from_dict(campaign_to_sku, orient="index", columns=["SKU"]).reset_index()
            mapping_report.rename(columns={"index": "Campaign Name (Informational only)"}, inplace=True)

            sku_with_search_terms = search_term_data["Campaign Name (Informational only)"].unique()
            sku_report = pd.DataFrame({"SKUs with Search Terms": [campaign_to_sku.get(c, None) for c in sku_with_search_terms]})

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                mapping_report.to_excel(writer, sheet_name="SKU to Campaign Mapping", index=False)
                sku_report.to_excel(writer, sheet_name="SKUs with Search Terms", index=False)

            timestamp = datetime.datetime.now().strftime("%Y-%m-%S_%H-%M-%S")
            filename = f"empty_dataset_report_{timestamp}.xlsx"

            st.write("Download the empty dataset report below:")
            output.seek(0)
            b64 = base64.b64encode(output.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download Empty Dataset Report</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            if brand_exclusions:
                excluded_terms = set(brand_exclusions.lower().splitlines())
                search_term_data = search_term_data[~search_term_data["Customer Search Term"].str.lower().apply(
                    lambda x: any(term in x for term in excluded_terms)
                )]

            monograms_aggregated = aggregate_ngrams(search_term_data, lambda x: x, stop_words)
            bigrams_aggregated = aggregate_ngrams(search_term_data, bigrams, stop_words)
            trigrams_aggregated = aggregate_ngrams(search_term_data, trigrams, stop_words)

            # Combine results and save to Excel
            report_df = pd.concat([monograms_aggregated, bigrams_aggregated, trigrams_aggregated],
                                  keys=["Monograms", "Bigrams", "Trigrams"])
            report_df.reset_index(level=0, inplace=True)
            report_df.rename(columns={"level_0": "N-Gram Type"}, inplace=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                monograms_aggregated.to_excel(writer, sheet_name="Monograms", index=False)
                bigrams_aggregated.to_excel(writer, sheet_name="Bigrams", index=False)
                trigrams_aggregated.to_excel(writer, sheet_name="Trigrams", index=False)
                report_df.to_excel(writer, sheet_name="Report", index=False)

            timestamp = datetime.datetime.now().strftime("%Y-%m-%S_%H-%M-%S")
            filename = f"ngram_analysis_output_{timestamp}.xlsx"

            st.success("Analysis completed. Download the report below:")
            output.seek(0)
            b64 = base64.b64encode(output.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download Excel File</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.error("Please upload a file.")
