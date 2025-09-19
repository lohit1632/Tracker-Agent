from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote_plus
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import json
import requests
import re
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

###########################################################################################################
def search_serper(query: str, max_results: int = 20):
    """Search Google using Serper API and return filtered URLs."""
    headers = {
        "X-API-KEY": "a59045f240301ef17c7adc710b64d68b5bab36a0",
        "Content-Type": "application/json"
    }
    payload = {"q": query, "gl": "in", "hl": "en", "num": max_results}
    res = requests.post("https://google.serper.dev/search", headers=headers, json=payload)
    res.raise_for_status()
    data = res.json()
    return [
        item["link"] for item in data.get("organic", [])
        if item.get("link") and not any(
            x in item["link"] for x in ["reddit", "quora", "youtube", "pinterest"]
        )
    ]

###########################################################################################################
def extract_linkedin_usernames(url_list):
    """Extract LinkedIn usernames from URLs."""
    usernames = []
    for url in url_list:
        match = re.search(r'linkedin\.com/in/([^/?#]+)', url)
        if match:
            usernames.append(match.group(1))
    return usernames

###########################################################################################################
def initialize_driver(username, password):
    """Login to LinkedIn and return driver."""
    from webdriver_manager.chrome import ChromeDriverManager

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    driver.get("https://www.linkedin.com/login/")
    wait = WebDriverWait(driver, 10)

    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
    username_input.send_keys(username)

    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys(password)

    sign_in_button = driver.find_element(By.XPATH, '//button[@type="submit" and contains(@class, "btn__primary--large")]')
    sign_in_button.click()

    time.sleep(30)
    return driver

###########################################################################################################
def get_basic_info(user_name, driver):
    """Get name and bio from LinkedIn profile."""
    url = f'https://in.linkedin.com/in/{user_name}/'
    driver.get(url)
    time.sleep(30)  # allow time for profile to load

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Extract Name
    name_tag = soup.find('h1')
    name = name_tag.text.strip() if name_tag and name_tag.text.strip() else None

    # Extract Bio / Job
    bio_div = soup.find('div', class_='artdeco-entity-lockup__subtitle')
    if bio_div is None:
        bio_div = soup.find('div', class_=lambda x: x and 'artdeco-entity-lockup__subtitle' in x)
    bio_text = bio_div.get_text(strip=True) if bio_div else None

    # Extract Location
    location_span = soup.find('span', class_='text-body-small inline t-black--light break-words')
    location = location_span.get_text(strip=True) if location_span else None

    # Combine
    final_bio = ""
    if bio_text:
        final_bio += bio_text
    if location:
        final_bio += " | " + location if final_bio else location

    return {"name": name, "bio": final_bio}

###########################################################################################################
def linkedin_searcher(query, initial_metadata_user, port):
    """Main LinkedIn search process."""
    load_dotenv()
    username = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')

    # chrome_options = Options()
    # chrome_options.debugger_address = f"127.0.0.1:{port}" 

    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver=initialize_driver(username,password)

    urls = search_serper(query)
    usernames = extract_linkedin_usernames(urls)[:5]  # limit to 5 profiles

    extracted_data = []
    for user in usernames:
        try:
            info = get_basic_info(user, driver)
            extracted_data.append({
                'linkedin_ID': user,
                'name': info['name'],
                'bio': info['bio']
            })
            time.sleep(20)
        except Exception as e:
            print(f"Could not fetch for {user}: {e}")
            continue

    # Setup LLM
    llm = ChatOpenAI(api_key=os.environ['OPEN_AI_API_KEY'], model='gpt-4.1')

    class llm_output_LinkedIn(BaseModel):
        user_id: str = Field(description='The most suitable ID out of the entire list')
        reasoning : str = Field(description='Reasoning for Accepting or rejecting the ID')

    sys_message = SystemMessage(content=(
        'Provided a Dictionary, which contains LinkedIn Bio, Location and Name of various users. '
        'Extract the most suitable ID which matches best with the initial metadata provided in the HumanMessage. '
        'Return only the ID in response — no additional data. If no ID matches to a significant extent, return None.'
    ))

    human_message = HumanMessage(
        content=(
            f"Initial Metadata:\n"
            f"- Name: {initial_metadata_user['Actual_name']}\n"
            f"- Location: {initial_metadata_user['last_known_location']}\n"
            f"- Last Known Job: {initial_metadata_user['last_known_work']}\n"
            f"- Last Known Job: {initial_metadata_user['extra_meta_data']}\n\n"
            f"LinkedIn Profiles:\n" +
            "\n".join([
                f"ID: {user['linkedin_ID']}\nName: {user['name']}\nBio: {user['bio']}\n"
                for user in extracted_data
            ])
        )
    )

    response = llm.with_structured_output(llm_output_LinkedIn).invoke([sys_message, human_message])

    # Save full extracted info to JSON
    output_data = {
        "query": query,
        "initial_metadata": initial_metadata_user,
        "candidates": extracted_data,
        "llm_selected_id": response.user_id,
        "Reasoning": response.reasoning
    }

    os.makedirs("linkedin_extractions", exist_ok=True)
    file_name = query.replace(" ", "_")[:50] + ".json"
    file_path = os.path.join("linkedin_extractions", file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print(f"Stored results to {file_path}")
    return response.user_id,driver,usernames,output_data['Reasoning']

###########################################################################################################
def main():
    query = 'Lohit Pattnaik IITG LinkedIn'
    initial_metadata_user = {
        "name": "Lohit Pattnaik",
        "last_known_location": "Guwahati",
        "last_job": "DS Intern at Nation with Namo"
    }
    linkedin_searcher(query, initial_metadata_user)

if __name__ == "__main__":
    main()   