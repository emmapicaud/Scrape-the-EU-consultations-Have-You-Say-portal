# Scrape the EU Public Consultations Have You Say Portal

A data-driven project to scrape and analyze textual data from the European Commission's **["Have Your Say"](https://ec.europa.eu/info/law/better-regulation/have-your-say_en)** public consultation portal, one of the largest repositories of stakeholder input in European policymaking.

By collecting and structuring consultation data at scale, this project aims to build an observatory of EU regulation capable of revealing lobbying patterns, coordinated campaigns, emerging controversies, and shifts in public debate across policy sectors.

This project relies on the open-source Python package **[`eu_consultations`](https://github.com/marioangst/eu_consultations)**, developed by Mario Angst, to collect and structure the data.

## Overview

The "Have Your Say" portal centralizes public consultations, feedback, and attached documents submitted by citizens, companies, NGOs, and other stakeholders on EU legislative initiatives. This project provides a reproducible pipeline to:

- Query consultations by policy topic and/or keyword
- Retrieve consultation metadata and stakeholder feedback
- Download attached documents (PDF, DOCX, etc.)
- Extract machine-readable text from those attachments
- Export the resulting corpus as structured data (JSON/CSV) for downstream analysis

## Technical Approach

The project relies on the [`eu_consultations`](https://github.com/marioangst/eu_consultations) GitHub package, an open-source Python package built specifically to interface with the public API behind the [Have Your Say portal](https://ec.europa.eu/info/law/better-regulation/have-your-say_en). Rather than scraping HTML pages directly, the package queries the underlying API, which makes data collection more reliable, reproducible, and easier to maintain over time.

The package supports a complete acquisition pipeline:

1. Retrieving consultation metadata by topic or keyword
2. Collecting stakeholder feedback submitted through the portal
3. Downloading attached documents
4. Extracting text from those attachments
5. Exporting the resulting corpus as structured JSON data

## Environment Setup

Because the package's dependencies can conflict with an existing base Python/Jupyter environment, it is recommended to use an isolated environment managed with [`uv`](https://github.com/astral-sh/uv):

```bash
# Install uv
pip install uv

# Clone the package repository
git clone https://github.com/marioangst/eu_consultations.git
cd eu_consultations

# Create an isolated environment and install exact dependency versions from the lockfile
uv sync

# Add Jupyter support and register a dedicated kernel
uv add ipykernel
uv run python -m ipykernel install --user --name=eu_consultations --display-name "Python (eu_consultations)"
```

Then select the **"Python (eu_consultations)"** kernel in Jupyter before running any notebook in this repository.

> **Note:** Installation issues encountered during setup were reported upstream — see [Issue #1 — Installation Errors](https://github.com/marioangst/eu_consultations/issues/1). Check that thread for the latest fixes before installing.

## Usage

### 1. Explore available topics

```python
from eu_consultations.scrape import show_available_topics

show_available_topics()
```

### 2. Scrape consultations for a given topic and keywords

Example: scraping consultations tagged **"ENV"** (Environment) mentioning **"EUDR"** or **"deforestation"**:

```python
from eu_consultations.scrape import scrape

initiatives_data = scrape(
    topic_list=["ENV"],
    text_list=["EUDR", "deforestation"],
    max_pages=None,
    max_feedback=None,
    output_folder="Project2",
    filename="EUDR_scrapping.json"
)
```

### 3. Convert the raw JSON export to a flat CSV of feedback entries

```python
import pandas as pd

df = pd.read_json("Project2/EUDR_scrapping.json")

rows = []
for _, row in df.iterrows():
    for consultation in row["consultations"]:
        feedbacks = consultation.get("feedback") or []
        for feedback in feedbacks:
            rows.append({
                "initiative_id": row["id"],
                "initiative_title": row["shortTitle"],
                "consultation_id": consultation.get("id"),
                "consultation_title": consultation.get("title"),
                "feedback_id": feedback.get("id"),
                "date": feedback.get("dateFeedback"),
                "country": feedback.get("country"),
                "language": feedback.get("language"),
                "userType": feedback.get("userType"),
                "surname": feedback.get("surname"),
                "status": feedback.get("status"),
                "content": feedback.get("feedback"),
            })

df_feedback = pd.DataFrame(rows)
df_feedback.to_csv("Project2/EUDR_feedback.csv", index=False)
```

### 4. Verify completeness against the public register

The raw Better Regulation API can be queried directly (without the package) to cross-check the total number of results shown on the public website:

```python
import httpx

url = "https://ec.europa.eu/info/law/better-regulation/brpapi/searchInitiatives?"
params = {"topic": "ENV", "page": 0, "size": 10, "language": "en"}  # no text filter

r = httpx.get(url, params=params, timeout=None)
data = r.json()

print(data["initiativeResultDtoPage"]["totalElements"])
```

This value should match the number of results displayed when filtering by the same topic on the [Have Your Say portal](https://ec.europa.eu/info/law/better-regulation).

## Example Output Sample

After running the extraction pipeline, `EUDR_feedback.csv` contains one row per stakeholder feedback entry, with columns such as:

| initiative_id | initiative_title | consultation_id | feedback_id | date | country | language | userType | status | content |
|---|---|---|---|---|---|---|---|---|---|
| 13123 | Deforestation-free products regulation | 45678 | 987654 | 2023-06-12 | BE | en | NGO | PUBLISHED | "We welcome the proposed regulation but call for..." |
| 13123 | Deforestation-free products regulation | 45678 | 987655 | 2023-06-14 | DE | de | COMPANY | PUBLISHED | "Die vorgeschlagene Verordnung stellt eine..." |

*(Sample rows shown for illustration; actual content and volume depend on the scrape parameters used.)*

## Repository Structure

```
.
├── README.md
├── LICENSE
├── scrape_eu_consultations.py   # Reusable, generic scraping/export script
└── Project2/                    # Example output folder (JSON/CSV exports)
```

## Data Source & Credits

- Data source: [European Commission — Have Your Say portal](https://ec.europa.eu/info/law/better-regulation/have-your-say_en)
- Scraping package: [`eu_consultations`](https://github.com/marioangst/eu_consultations) (GitHub) by Mario Angst

## License

This project is released under the MIT License — see [LICENSE](LICENSE) for details.
