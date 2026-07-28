"""
scrape_eu_consultations.py

Generic, reusable script to scrape consultation data from the European
Commission's "Have Your Say" portal using the `eu-consultations` package,
export it to JSON/CSV, and verify completeness against the public API.

Requirements:
    pip install eu-consultations httpx pandas
    (see README.md for the recommended isolated environment setup with uv)

Usage:
    python scrape_eu_consultations.py --topic ENV --text EUDR deforestation \
        --output-folder Project2 --filename EUDR_scrapping.json
"""

import argparse
import os
import httpx
import pandas as pd

from eu_consultations.scrape import scrape, show_available_topics

BASE_URL = "https://ec.europa.eu/info/law/better-regulation/brpapi/searchInitiatives?"


def list_topics():
    """Print the topics available on the Have Your Say portal."""
    show_available_topics()


def scrape_consultations(topic_list, text_list, output_folder, filename,
                          max_pages=None, max_feedback=None):
    """
    Scrape consultations matching the given topics/keywords and save
    the raw result as a JSON file inside `output_folder`.
    """
    os.makedirs(output_folder, exist_ok=True)
    data = scrape(
        topic_list=topic_list,
        text_list=text_list,
        max_pages=max_pages,
        max_feedback=max_feedback,
        output_folder=output_folder,
        filename=filename,
    )
    return data


def json_to_feedback_csv(json_path, csv_path):
    """
    Flatten the raw scraped JSON export into a tabular CSV,
    with one row per stakeholder feedback entry.
    """
    df = pd.read_json(json_path)

    rows = []
    for _, row in df.iterrows():
        for consultation in row.get("consultations", []):
            feedbacks = consultation.get("feedback") or []
            for feedback in feedbacks:
                rows.append({
                    "initiative_id": row.get("id"),
                    "initiative_title": row.get("shortTitle"),
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
    df_feedback.to_csv(csv_path, index=False)
    return df_feedback


def verify_total_results(topic, text_list=None, language="en"):
    """
    Query the public Better Regulation API directly to check the total
    number of results for a topic (optionally filtered by keywords),
    so it can be compared against the public portal's displayed count.
    """
    params = {"topic": topic, "page": 0, "size": 10, "language": language}
    if text_list:
        # Note: the public API only accepts a single "text" value per call.
        params["text"] = text_list[0]

    response = httpx.get(BASE_URL, params=params, timeout=None)
    response.raise_for_status()
    data = response.json()
    total = data["initiativeResultDtoPage"]["totalElements"]
    return total


def main():
    parser = argparse.ArgumentParser(description="Scrape EU 'Have Your Say' consultations.")
    parser.add_argument("--topic", nargs="+", required=True, help="One or more topic codes (e.g. ENV)")
    parser.add_argument("--text", nargs="*", default=None, help="Optional keyword(s) to filter consultations")
    parser.add_argument("--output-folder", default="output", help="Folder to store the exported files")
    parser.add_argument("--filename", default="scrapping.json", help="Output JSON filename")
    parser.add_argument("--max-pages", type=int, default=None, help="Maximum number of pages to scrape")
    parser.add_argument("--max-feedback", type=int, default=None, help="Maximum number of feedback entries per consultation")
    parser.add_argument("--list-topics", action="store_true", help="List available topics and exit")
    args = parser.parse_args()

    if args.list_topics:
        list_topics()
        return

    scrape_consultations(
        topic_list=args.topic,
        text_list=args.text,
        output_folder=args.output_folder,
        filename=args.filename,
        max_pages=args.max_pages,
        max_feedback=args.max_feedback,
    )

    json_path = os.path.join(args.output_folder, args.filename)
    csv_path = os.path.join(args.output_folder, args.filename.replace(".json", "_feedback.csv"))
    df_feedback = json_to_feedback_csv(json_path, csv_path)
    print(f"Exported {len(df_feedback)} feedback entries to {csv_path}")

    for topic in args.topic:
        total = verify_total_results(topic, text_list=None)  # unfiltered count for comparison
        print(f"Total results on the public portal for topic '{topic}' (no keyword filter): {total}")


if __name__ == "__main__":
    main()