from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
from html import unescape
import re
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from itertools import zip_longest
from bs4 import Tag

##################################################################################################################


def get_basic_info(user_id,driver,output_dir):

    url = f"https://www.facebook.com/{user_id}/"
    driver.get(url)

    time.sleep(30)

    intro_html = driver.page_source
    
    with open(os.path.join(output_dir,f'{user_id}_fb_intro.html'),'w',encoding='utf-8') as f:
        f.write(intro_html)


    soup = BeautifulSoup(intro_html, "html.parser")

    h1_tag = soup.findAll("h1")

    name = h1_tag[len(h1_tag)-1]

    target_class = [
    "x193iq5w", "xeuugli", "x13faqbe", "x1vvkbs", "x1xmvt09", "x1lliihq",
    "x1s928wv", "xhkezso", "x1gmr53x", "x1cpjm7i", "x1fgarty", "x1943h6x",
    "xudqn12", "x3x7a5m", "x6prxxf", "xvq8zen", "xo1l8bm", "xzsf02u", "x1yc453h"
    ]

    # Helper to match exact class
    def match_exact_class(tag):
        return tag.name == "span" and sorted(tag.get("class", [])) == sorted(target_class)

    profile_container = soup.find("div", class_="x9f619 x1ja2u2z x78zum5 x2lah0s x1n2onr6 x1qughib x1qjc9v5 xozqiw3 x1q0g3np xv54qhq xf7dkkf xyamay9 x1ws5yxj xw01apr x4cne27 xifccgj")  # update this to your actual container

    # Step 2: Find all matching spans *only inside that div*
    profile_info=[]
    if profile_container:
        scoped_spans = profile_container.find_all(match_exact_class)
        for span in scoped_spans:
            profile_info.append(span.get_text(strip=True))
    else:
        print("Container div not found.")

    output={}
    output['name'] = name
    output['basic_info'] = profile_info
    output['html'] = intro_html

    return output

##################################################################################################################
    

def post_related_info(user_id,intro_html,driver,output_dir):
    
    soup = BeautifulSoup(intro_html, "html.parser")

    # Match post containers using class starting with the given pattern
    post_divs = soup.find_all("div", class_=[
        "html-div", "xdj266r", "x14z9mp", "xat24cr",
        "x1lziwak", "xexx8yu", "xyri2b", "x18d9i69", "x1c1uobl"
    ])

    captions = []

    for post in post_divs:
        caption_div = post.find("div", dir="auto")
        if caption_div:
            text = caption_div.get_text(strip=True)
            captions.append(text)

    caption_set= set()
    final_captions=[]
    # Output all found captions
    for i, caption in enumerate(captions, 1):
        text = caption
        if text and text not in caption_set:
            caption_set.add(text)
            final_captions.append(text)



    hidden_divs = soup.find_all("div", hidden=True)

    dates = []

    # Extract date strings from hidden spans
    for div in hidden_divs:
        spans = div.find_all("span")
        for span in spans:
            text = span.get_text(strip=True)
            if any(month in text for month in [
                "January", "February", "March", "April", "May", "June", "July",
                "August", "September", "October", "November", "December"
            ]):
                try:
                    parsed_date = datetime.strptime(text, "%d %B %Y")
                    dates.append(parsed_date)
                except ValueError:
                    continue  # Skip if format doesn't match

    # Sort dates from most recent to oldest
    sorted_dates = sorted(dates, reverse=True)

    posts=[]

    for caption, date in zip_longest(final_captions, dates, fillvalue=None):
        post={'caption':caption,'Date':date.strftime("%d %B %Y") if date else None}
        posts.append(post)

    return posts

##################################################################################################################



def checked_in_logs(user_id,driver,output_dir):
    
    url = f"https://www.facebook.com/{user_id}/map/"
    driver.get(url)

    time.sleep(30)

    html_map = driver.page_source
    
    with open(os.path.join(output_dir,f'{user_id}_fb_check_in_logs.html'),'w',encoding='utf-8') as f:
        f.write(html_map)
   
    soup = BeautifulSoup(html_map, "html.parser")

    results = []

    # Each location+date pair is wrapped inside this div
    location_blocks = soup.find_all("div", class_="x1gslohp")

    for block in location_blocks:
        texts = block.stripped_strings
        texts = list(texts)
        if len(texts) >= 2:
            location = texts[0]
            date = texts[1]
            results.append((location, date))

    # Output

    logs=[]
    for location, date in results:
        log={'location':location ,
             'Date':date
             }
        logs.append(log)

    return logs

##################################################################################################################

def initialize_driver(username,password):
    # service = Service(executable_path="C:\\Users\\Lohit\\Downloads\\chromedriver-win32\\chromedriver-win32\\chromedriver.exe")
    # driver = webdriver.Chrome(service=service)
    from webdriver_manager.chrome import ChromeDriverManager

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    # Open Facebook login page
    driver.get("https://www.facebook.com/")

    # Wait for the page to load
    wait = WebDriverWait(driver, 10)

    # Enter username/email
    username_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    username_input.send_keys(username)

    # Enter password
    password_input = driver.find_element(By.ID, "pass")
    password_input.send_keys(password)

    # Click on login button
    login_button = driver.find_element(By.NAME, "login")
    login_button.click()

    # Optional: wait and print page title
    time.sleep(120)
    
    return driver

def facebook_ID_searcher(search_id,driver):
    # Load environment variables
    load_dotenv()

    username = os.getenv('EMAIL_FB')
    password = os.getenv('PASSWORD_FB')

    # # Initialize Selenium driver and login
    # driver = initialize_driver(username, password)

    # Let the profile load completely (adjust as necessary)
    # time.sleep(40)

    # ID of the profile to scrape
    # search_id = 'lohit.patnaik'

    # Output directory
    output_dir = f"{search_id}_data_FB"
    os.makedirs(output_dir, exist_ok=True)

    # Scrape basic info and HTML
    basic_info = get_basic_info(search_id, driver, output_dir)

    # Extract post-related info (captions, dates)
    post_info = post_related_info(search_id, basic_info['html'], driver, output_dir)

    # Extract check-in logs if any
    check_in_logs = checked_in_logs(search_id, driver, output_dir)

    # Extract name and bio from basic_info
    name = basic_info['name']
    bio = basic_info['basic_info']

    # Helper function to clean nested structures
    def clean(obj):
        if isinstance(obj, Tag):
            return obj.get_text(strip=True)
        elif isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean(item) for item in obj]
        else:
            return obj

    # Clean all components
    clean_name = clean(name)
    clean_bio = clean(bio)
    clean_posts = clean(post_info)
    clean_check_ins = clean(check_in_logs)

    # Final structured data
    final_data = {
        "search_id": search_id,
        "name": clean_name,
        "bio": clean_bio,
        "posts": clean_posts,
        "check_ins": clean_check_ins
    }

    # JSON output path
    output_path = os.path.join(output_dir, f"{search_id}_data_FB.json")

    # Write to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)

    print(f"Saved profile data to: {output_path}")

    return final_data

def main():
    search_id = 'lohit.patnaik'    
    extracted_data = facebook_ID_searcher(search_id,"") 

if __name__ == "__main__":
    main()    




    
    
        