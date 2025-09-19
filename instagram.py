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

def get_overall_details(user_id,driver,ouput_dir):    
    driver.get(f'https://www.instagram.com/{user_id}/')
    time.sleep(10)
    html = driver.page_source

    with open(os.path.join(ouput_dir,f"{user_id}_first_profile.html"), "w", encoding="utf-8") as f:
        f.write(html)
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
    output['html'] = html
    return output    


def first_k_post_details(html,no_of_posts):
    soup = BeautifulSoup(html, "html.parser")
    post_anchors = soup.find_all("a", href=True)
    last_k_posts=[]
    first_post_anchor = None
    for anchor in post_anchors:
        # We're checking if it contains the expected class and nested structure
        post_div = anchor.find("div", class_="_aagu")  # This is the container for the post image
        if post_div:
            first_post_anchor = anchor
            last_k_posts.append(first_post_anchor)
            if len(last_k_posts)==5 or len(last_k_posts)==no_of_posts:
                break
    last_k_post_json = []
    for first_post_anchor in last_k_posts:
        output={}
        if first_post_anchor:
            print("Post URL:", "https://instagram.com" + first_post_anchor['href'])
            output['url'] = "https://instagram.com" + first_post_anchor['href']

            img_tag = first_post_anchor.find("img", alt=True)
            if img_tag:
                caption = img_tag['alt']
                print("Caption:", caption)
                output['caption'] = caption

            last_k_post_json.append(output)                             
        else:
            print(" No post anchor with image found.")
    return last_k_post_json        



def get_last_post_details(url, driver, user_id,output_dir):
    driver.get(url)
    
    # Wait for time tag
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "time"))
        )
    except Exception as e:
        print(f"Error waiting for time tag: {e}")

    # Wait for location anchor tag if it exists
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/explore/locations/')]"))
        )
    except:
        pass  # Location may not be tagged — that's OK

    time.sleep(2)  # Let JavaScript fully render everything

    post_info = driver.page_source
    with open(os.path.join(output_dir, f"{user_id}_last_post.html"), "w", encoding="utf-8") as f:
        f.write(post_info)

    soup = BeautifulSoup(post_info, 'html.parser')
    time_tag = soup.find('time')

    iso_datetime = time_tag['datetime'] if time_tag else None
    title_text = time_tag.get('title') if time_tag else None
    display_text = time_tag.text if time_tag else None

    last_post_data = {
        'Exact_date_time': iso_datetime,
        'Date': title_text,
    }

    print("ISO Datetime:", iso_datetime)
    print("Title Text:", title_text)
    print("Displayed Text:", display_text)

    # Location tag
    location_tag = soup.find('a', href=lambda x: x and '/explore/locations/' in x)
    location_name = location_tag.text if location_tag else None
    location_url = location_tag['href'] if location_tag else None
    location_id='Default'
    try: 
     location_id = re.search(r'/locations/(\d+)', location_url).group(1) if location_url else None
    except:
     print("Couldn't find the Location ID")    

    last_post_data.update({
        'Location': location_name,
        'Location_url': location_url,
    })

    print("Location Name:", location_name)
    print("Location URL:", location_url)
    print("Location ID:", location_id)

    return last_post_data


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
    time.sleep(120)
    
    return driver


def Insta_ID_searcher(search_id,driver):
    
    load_dotenv()
    username = os.getenv('USERNAME_IG')
    password = os.getenv('PASSWORD_IG')
    #driver = initialize_web_driver(username,password)
    
    # search_id = input('Enter the user ID')


    output_dir = f"{search_id}_data"  # Folder name
    os.makedirs(output_dir, exist_ok=True)  # Create folder if it doesn't exist

    overall_details=get_overall_details(search_id,driver,output_dir)

    last_k_post_details=[]
    first_k_post=[]

    if int(overall_details['no_of_post'])>0:   #If Following or Public
        first_k_post = first_k_post_details(overall_details['html'],int(overall_details['no_of_post']))
        for post in first_k_post:
            try: 
                last_k_post_details.append(get_last_post_details(post['url'],driver,search_id,output_dir))
            except:
                print(f'Failed for {post["url"]}') 

            time.sleep(40)

    combined = []
    for last, first in zip(last_k_post_details, first_k_post):
        merged = {**last, **first}
        combined.append(merged)

    #Save to output directory
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{search_id}_post_details.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=4, ensure_ascii=False)

    return combined


def main():
    search_id = 'lohit__xd'
    final_data = Insta_ID_searcher(search_id)

if __name__ == "__main__":
    main()    

    


    
