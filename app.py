from dotenv import load_dotenv
from flask import Flask, jsonify, request

from eventfinder.extract import fetch_and_extract
from eventfinder.search import search_event_urls

load_dotenv()

app = Flask(__name__)


@app.route("/")
def hello_world() -> str:
    return "EventFinder API"


@app.route("/events")
def events() -> tuple:
    speaker = request.args.get("speaker", "").strip()
    if not speaker:
        return jsonify({"error": "speaker query parameter is required"}), 400

    urls = search_event_urls(speaker)
    events_data = fetch_and_extract(urls)
    return jsonify({"speaker": speaker, "events": events_data}), 200


if __name__ == '__main__':
    app.run()
