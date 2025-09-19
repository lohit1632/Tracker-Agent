# Social Media Profile Extraction

This project is a web application for extracting and summarizing social media profile data (Facebook, Instagram, LinkedIn) for a given person, using automated search and scraping workflows.

## Features

- Web interface for entering user details
- Automated extraction of profile data from Facebook, Instagram, and LinkedIn
- Intelligent selection of the most relevant profiles
- Summarized output using LLM (OpenAI GPT-4.1)
- Real-time status updates

## Required Files

- [app.py](app.py): Main Flask web server.
- [main.py](main.py): Workflow graph and orchestration logic.
- [facebook.py](facebook.py): Facebook profile scraping utilities.
- [instagram.py](instagram.py): Instagram profile scraping utilities.
- [linkedin.py](linkedin.py): LinkedIn profile scraping utilities.
- [web_search_facebook.py](web_search_facebook.py): Facebook search logic.
- [web_search_insta.py](web_search_insta.py): Instagram search logic.
- [web_search_linkedin.py](web_search_linkedin.py): LinkedIn search logic.
- [templates/index.html](templates/index.html): Web UI template.
- [.env](.env): Environment variables (must include `OPEN_AI_API_KEY`).

## Getting Started

### Prerequisites

- Python 3.8+
- Chrome WebDriver (for Selenium)
- OpenAI API key (add to `.env` as `OPEN_AI_API_KEY`)
- Required Python packages (see below)

### Installation

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd <repo-directory>
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is missing, install: Flask, selenium, beautifulsoup4, python-dotenv, openai, langchain-openai, etc.)*

3. **Set up environment variables:**
   - Create a `.env` file in the root directory.
   - Add your OpenAI API key:
     ```
     OPEN_AI_API_KEY=your-openai-key
     ```

4. **Download and set up Chrome WebDriver**  
   Make sure `chromedriver` is in your PATH.

### Running the App

Start the Flask server:

```sh
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

## Usage

1. Fill in the form with the actual name, last known location, work, extra metadata, and current date.
2. Click "Start Extraction".
3. The app will search, extract, and summarize social media profiles.
4. View results and summary in the web interface.

## File Structure

- `app.py` — Flask server and API endpoints
- `main.py` — Workflow graph and orchestration
- `facebook.py`, `instagram.py`, `linkedin.py` — Scraping utilities
- `web_search_facebook.py`, `web_search_insta.py`, `web_search_linkedin.py` — Search logic
- `templates/index.html` — Web UI
- `.env` — Environment variables


**Note:**  
This project automates web scraping and uses LLMs. Use responsibly and comply with the terms of service of the target platforms.
