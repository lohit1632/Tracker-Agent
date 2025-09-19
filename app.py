from flask import Flask, render_template, request, jsonify
import threading
import time
from typing import List, Optional
from main import build_graph

app = Flask(__name__)

# Keep-alive to prevent idling
def keep_alive():
    while True:
        print("🔄 Keep-alive ping to prevent sleeping...")
        time.sleep(300)

threading.Thread(target=keep_alive, daemon=True).start()

# Build the graph once
graph = build_graph()

# Store job status and results, extended for social media info
job_status = {
    "done": False,
    "summary": None,
    # Facebook
    "fb_username": [],
    "fb_id": None,
    "fb_reason": None,
    "fb_profile_data": None,
    # Instagram
    "insta_username": [],
    "insta_id": None,
    "insta_reason": None,
    "insta_profile_data": None,
    # LinkedIn
    "ld_username": [],
    "ld_id": None,
    "ld_reason": None,
    "linkedin_profile_data": None,
}

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_job():
    input_data = {
        "Actual_name": request.form.get("name"),
        "last_known_location": request.form.get("location"),
        "last_known_work": request.form.get("work"),
        "extra_meta_data": request.form.get("meta"),
        "Current_date": request.form.get("date")
    }

    # Reset all job_status fields before starting
    job_status.update({
        "done": False,
        "summary": None,
        "fb_username": [],
        "fb_id": None,
        "fb_reason": None,
        "fb_profile_data": None,
        "insta_username": [],
        "insta_id": None,
        "insta_reason": None,
        "insta_profile_data": None,
        "ld_username": [],
        "ld_id": None,
        "ld_reason": None,
        "linkedin_profile_data": None,
    })

    def run_job():
        # Run your graph or long process
        result = graph.invoke({"input": input_data})

        # Extract summary text
        summary = result["output"].get("summary", "")

        # Extract social media info if available, otherwise fallback to empty/defaults
        # social_data = result["output"].get("social_media", {})
        social_data=result

        job_status["summary"] = summary

        job_status["fb_username"] = social_data.get("fb_username", [])
        job_status["fb_id"] = social_data.get("fb_id")
        job_status["fb_reason"] = social_data.get("fb_reason")
        job_status["fb_profile_data"] = social_data.get("fb_profile_data")

        job_status["insta_username"] = social_data.get("insta_username", [])
        job_status["insta_id"] = social_data.get("insta_id")
        job_status["insta_reason"] = social_data.get("insta_reason")
        job_status["insta_profile_data"] = social_data.get("insta_profile_data")

        job_status["ld_username"] = social_data.get("ld_username", [])
        job_status["ld_id"] = social_data.get("linkedin_id")
        job_status["ld_reason"] = social_data.get("ld_reason")
        job_status["linkedin_profile_data"] = social_data.get("linkedin_profile_data")

        # Save summary to file
        with open(f'{input_data["Actual_name"]}_Final_analysis.txt', 'w', encoding='utf-8') as f:
            f.write(summary)

        job_status["done"] = True

    threading.Thread(target=run_job).start()
    return jsonify({"status": "started"})

@app.route("/status", methods=["GET"])
def status():
    # Return the entire job_status dict, including social media info
    return jsonify(job_status)

@app.route("/health")
def health():
    return jsonify({"status": "running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
