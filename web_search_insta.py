from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import quote_plus
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from pydantic import BaseModel,Field
from typing import List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import json
from html import unescape
import re
from typing import Optional
from langchain_openai import ChatOpenAI
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
import requests
from webdriver_manager.chrome import ChromeDriverManager


###########################################################################################################
def fetch_all_bing_pages(query, driver, delay=5, max_pages=1):
    encoded_query = quote_plus(query)
    base_url = f"https://duckduckgo.com/search?q={encoded_query}"
    driver.get(base_url)
    time.sleep(delay)

    all_html = []
    current_page = 1

    while current_page <= max_pages:
        print(f" Capturing page {current_page}")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        html = driver.page_source
        all_html.append(html)

        try:
            wait = WebDriverWait(driver, 5)
            more_button = wait.until(
                EC.presence_of_element_located((By.XPATH, "//button[@id='more-results']"))
            )

            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
                time.sleep(0.5)
                more_button.click()
            except StaleElementReferenceException:
                print(" Stale element. Retrying...")
                try:
                    more_button = driver.find_element(By.XPATH, "//button[@id='more-results']")
                    driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
                    more_button.click()
                except Exception as e:
                    print(f" Failed to recover from stale element: {e}")
                    break
            except ElementClickInterceptedException:
                print(" Click intercepted. Trying JS click.")
                try:
                    driver.execute_script("arguments[0].click();", more_button)
                except Exception as e:
                    print(f" JS click failed: {e}")
                    break

        except (TimeoutException, NoSuchElementException):
            print(" No more results button found.")
            break

        time.sleep(delay)
        current_page += 1

    return all_html
# def search_serper(query: str, max_results: int = 20):
#     """Search Google using Serper API and return filtered URLs."""
#     headers = {
#         "X-API-KEY": "a59045f240301ef17c7adc710b64d68b5bab36a0",
#         "Content-Type": "application/json"
#     }
#     payload = {"q": query, "gl": "in", "hl": "en", "num": max_results}
#     res = requests.post("https://google.serper.dev/search", headers=headers, json=payload)
#     res.raise_for_status()
#     data = res.json()
#     return [
#         item["link"] for item in data.get("organic", [])
#         if item.get("link") and not any(
#             x in item["link"] for x in ["reddit", "quora", "youtube", "pinterest"]
#         )
#     ]

###########################################################################################################

def fecth_insta_urls(html_text):

    soup = BeautifulSoup(html_text, "html.parser")

    # Extract all links
    links = soup.find_all('a')
    
    urls=[]
    # Print filtered hrefs (optional)
    for link in links:
        href = link.get('href')
        if href and "instagram.com" in href:
            urls.append(href)

    return urls        


###########################################################################################################


def filter_usernames(urls):

    usernames = []
    seen = set()

    for url in urls:
        path = urlparse(url).path.strip("/")
        parts = path.split("/")

        if parts[0] in ("reel", "p"):
            continue

        username = parts[0]
        if username and username not in seen:
            usernames.append(username)
            seen.add(username)

    usernames = usernames[:5]    
    return usernames


###########################################################################################################


def get_overall_details(user_id,driver):    
    driver.get(f'https://www.instagram.com/{user_id}/')
    time.sleep(10)
    html = driver.page_source

    # with open(os.path.join(ouput_dir,f"{user_id}_first_profile.html"), "w", encoding="utf-8") as f:
    #     f.write(html)
    soup = BeautifulSoup(html, "html.parser")

    # --- Name ---
    name_tag = soup.find("meta", property="og:title")
    name = None
    if name_tag and "content" in name_tag.attrs:
        raw_name = name_tag["content"]
        match = re.match(r"^(.*?)\s+\(", raw_name)
        if match:
            name = match.group(1).strip()
        else:
            name = raw_name.strip()

    # --- Bio / Description ---
    meta_desc = soup.find("meta", attrs={"name": "description"})
    bio = None
    if meta_desc and "content" in meta_desc.attrs:
        content = unescape(meta_desc["content"])
        if ":" in content:
            bio = content.split(":", 1)[1].strip().strip('"')

    # --- Privacy Status ---
    privacy_status = "Public"
    private_tag = soup.find("span", string="This account is private")
    if private_tag:
        privacy_status = "Private"

    # --- Number of Posts ---
    posts = None
    if meta_desc and "content" in meta_desc.attrs:
        content = unescape(meta_desc["content"])
        posts_match = re.search(r"(\d+(?:[.,]\d+)?[MK]?)\s+Posts", content)
        if posts_match:
            posts = posts_match.group(1)

    output={}
    output['name'] = name
    output['bio'] = bio
    output['privacy_status'] = privacy_status
    output['no_of_post'] = posts
    return output    




###########################################################################################################



def initialize_web_driver(username,password):
    # Set up Chrome WebDriver
    from webdriver_manager.chrome import ChromeDriverManager

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # Open the login page (replace with actual URL)
    driver.get("https://www.instagram.com/accounts/login/")

    # Wait for fields to load
    wait = WebDriverWait(driver, 10)

    # Input username
    username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    username_field.send_keys(username)

    # Input password 
    password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    password_field.send_keys(password)

    # Wait for the login button to be clickable
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
    login_button.click()

    # Optional: wait for next page to load
    time.sleep(30)
    
    return driver


###########################################################################################################


def insta_search(query,initial_metadata_user,port):

    load_dotenv()
    username = os.getenv('USERNAME_IG')
    password = os.getenv('PASSWORD_IG')

    # chrome_options = Options()
    # chrome_options.debugger_address = f"127.0.0.1:{port}"

    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver = initialize_web_driver(username,password)

    time.sleep(10)

    html_pages=fetch_all_bing_pages(query,driver)

    #urls = search_serper(query)

    urls=[]
    for html_page in html_pages:
        
        urls.extend(fecth_insta_urls(html_page))

    unique_usernames = filter_usernames(urls)    

    extracted_data=[]

    for user_id in unique_usernames:
        try:
            user_data=get_overall_details(user_id,driver)
            user_data['username'] = user_id
            extracted_data.append(user_data)

        except:
            print(f"Couldn't Fetch the ID : {user_id}")  
        
        time.sleep(20)
    
    # name_verified_users=[]
    # for extracted_users in extracted_data:
    #     if extracted_users['name']==initial_metadata_user['Actual_name']:
    #         name_verified_users.append(extracted_users)

    # from langchain_groq import ChatGroq

    llm = ChatOpenAI(api_key=os.environ['OPEN_AI_API_KEY'],model='gpt-4.1')

    class user_location_resp(BaseModel):
        places: Optional[List[str]] = Field(description='List of Places displayed in the Bio')
        username: str
        name: Optional[str] = Field(description='Name displayed on the profile')
        bio: Optional[str] = Field(description='Initial bio on the profile')

    sys_message = SystemMessage(content='Provided a Dictionary, Read the Bio Field and extract if any info about a place is given, The places can be ' \
    'either directly mentioned or mentioned via an Airport Terminal code, decode the Place they are reffering to, The places are going ' \
    'to be mostly in India, So incase of any conflict give first priority to place in India, also Observe carefully ""multiple places"" might be mentioned.' \
    'If No location found return None' \
    'If you do not interpret any of the output field return None')

    resp_llm_model=[]

    for user in extracted_data:
        resp = llm.with_structured_output(user_location_resp).invoke([sys_message,HumanMessage(content=f'The user ID is {user["username"]} and the Bio is {user["bio"]} and the Name is {user["name"]}')])
        resp_llm_model.append(resp)
        time.sleep(30)

    class Selected_ID(BaseModel):
          insta_ID : str = Field(description='Most Suitable ID based on the details provided')
          reasoning : str = Field(description='Reasoning for Accepting or rejecting the ID')

    sys_message_1 = SystemMessage(content=(
        "You are provided with a list of Insta user data. "
        "Each entry contains the user's name, username, and list of places associated with them and the Bio. "
        "From this list, extract the ID (username) of the user whose list of places best matches "
        "the last known location provided in the initial metadata. "
        "Only return the ID (username) — no additional data and also return the initial Bio. If none of the candidates match to a significant extent, return None."
    ))

    # Format the human message
    location_summary = '\n'.join(
    f"ID: {u.username}\nName: {u.name}\nPlaces: {', '.join(u.places) if u.places else 'None'}\nBio: {u.bio}"
    for u in resp_llm_model
    )

    human_message_1 = HumanMessage(
        content=(
            f"Initial Metadata:\n"
            f"- Name: {initial_metadata_user['Actual_name']}\n"
            f"- Last Known Location: {initial_metadata_user['last_known_location']}\n"
            f"- Last Known Job: {initial_metadata_user['last_known_work']}\n"
            f"- Additional Data: {initial_metadata_user['extra_meta_data']}\n\n"
            f"Facebook Users:\n{location_summary}"
        )
    )
    # Invoke LLM
    most_suitable_id_response = llm.with_structured_output(Selected_ID).invoke([sys_message_1, human_message_1])

    # Store everything to JSON
    output_location_selection = {
        "query": query,
        "initial_metadata": initial_metadata_user,
        "candidates_with_places": [
            {
                "user_id": u.username,
                "name": u.name,
                "places": u.places,
                "bio": u.bio
            }
            for u in resp_llm_model
        ],
        "llm_selected_id": most_suitable_id_response.insta_ID,
        "Reasoning": most_suitable_id_response.reasoning
    }

    # Save to file
    os.makedirs("Insta_filtering", exist_ok=True)
    file_name = query.replace(" ", "_")[:50] + "_location.json"
    file_path = os.path.join("Insta_filtering", file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(output_location_selection, f, ensure_ascii=False, indent=4)

    print(f" Stored location-based result to {file_path}")

    return most_suitable_id_response.insta_ID,driver,unique_usernames,output_location_selection['Reasoning']


def main():
    query='Lohit Patnaik IITG Instagram'
    initial_metadata_user={}
    initial_metadata_user['Actual_name']='Lohit Pattnaik'
    initial_metadata_user['last_known_location']='Guwahati'
    initial_metadata_user['last_known_work']='DS at Nation with Namo'
    initial_metadata_user['extra_meta_data']='Studied at Visakhapatnam'
    insta_search(query,initial_metadata_user)



if __name__ == "__main__":
    main()   