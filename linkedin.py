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


######################################################################################################
def get_bio(user_name, driver, output_dir):
    import time, os
    from bs4 import BeautifulSoup

    url = f'https://in.linkedin.com/in/{user_name}/'
    driver.get(url)
    
    time.sleep(30)  # Wait for dynamic content to load

    html = driver.page_source

    # Save HTML
    with open(os.path.join(output_dir, f'{user_name}_front_page.html'), "w", encoding="utf-8") as f:
        f.write(html)

    soup = BeautifulSoup(html, 'html.parser')

    # -------- Extract Bio --------
    bio_div = soup.find('div', class_='artdeco-entity-lockup__subtitle')
    if bio_div is None:
        bio_div = soup.find('div', class_=lambda x: x and 'artdeco-entity-lockup__subtitle' in x)
    bio_text = bio_div.get_text(strip=True) if bio_div else None

    # -------- Extract Location --------
    location_span = soup.find('span', class_='text-body-small inline t-black--light break-words')
    location = location_span.get_text(strip=True) if location_span else None

    # Combine
    final_bio = ""
    if bio_text:
        final_bio += bio_text
    if location:
        final_bio += " | " + location if final_bio else location

    return final_bio




######################################################################################################  



def get_experience(user_name,driver,output_dir):

    url = f'https://www.linkedin.com/in/{user_name}/details/experience/'

    driver.get(url)

    time.sleep(30)

    html_exp = driver.page_source

    with open(os.path.join(output_dir,f'{user_name}_experience_page.html'), "w", encoding="utf-8") as f:
        f.write(html_exp)
    
    soup = BeautifulSoup(html_exp, 'html.parser')
    experience_blocks = soup.find_all('div', attrs={"data-view-name": "profile-component-entity"})

    experience_data = []

    for block in experience_blocks:
        try:
            spans = block.find_all('span', attrs={"aria-hidden": "true"})
            texts = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]

            if len(texts) < 3:
                continue

            role = texts[0]
            company_full = texts[1]
            if '·' in company_full:
                parts = [p.strip() for p in company_full.split('·')]
                company_name = parts[0]
                employment_type = parts[1] if len(parts) > 1 else None
            else:
                company_name = company_full
                employment_type = None

            if employment_type == '3rd+':
                continue

            timeline = texts[2] if len(texts) > 2 else None
            location = texts[3] if len(texts) > 3 else None

            a_tag = block.find("a", href=True)
            company_url = a_tag['href'] if a_tag else None

            img_tag = block.find("img", src=True)
            logo_url = img_tag['src'] if img_tag else None


            experience_data.append({
                    "Role": role,
                    "Company": company_name,
                    "Employment Type": employment_type,
                    "Timeline": timeline,
                    "Location": location,
                    "Company URL": company_url,
                    "Logo URL": logo_url
                })

        except Exception as e:
            print(f"Error parsing block: {e}")

    # Output or Save
    for i, exp in enumerate(experience_data, 1):
        print(f"\nExperience #{i}")
        for k, v in exp.items():
            print(f"{k}: {v}")

    with open(os.path.join(output_dir,f"{user_name}_experience.json"), "w", encoding="utf-8") as f:
        json.dump(experience_data, f, indent=2, ensure_ascii=False)

    return experience_data


######################################################################################################

def get_education(user_name,driver,output_dir):

    url = f'https://www.linkedin.com/in/{user_name}/details/education/'

    driver.get(url)

    time.sleep(30)

    html_edu = driver.page_source

    with open(os.path.join(output_dir,f'{user_name}_experience_page.html'), "w", encoding="utf-8") as f:
        f.write(html_edu)


    soup = BeautifulSoup(html_edu, 'html.parser')

    # Find all experience blocks
    experience_blocks = soup.find_all('div', attrs={"data-view-name": "profile-component-entity"})

    experience_data = []

    for block in experience_blocks:
        try:
            # Extract all span[aria-hidden="true"] inside the block
            spans = block.find_all('span', attrs={"aria-hidden": "true"})

            role = spans[0].get_text(strip=True) if len(spans) > 0 else None
            company = spans[1].get_text(strip=True) if len(spans) > 1 else None
            timeline = spans[2].get_text(strip=True) if len(spans) > 2 else None
            location = spans[3].get_text(strip=True) if len(spans) > 3 else None
            if company!='· 3rd+':
                experience_data.append({
                    "Role": role,
                    "Company": company,
                    "Timeline": timeline,
                    "Location": location
                })

        except Exception as e:
            print(f"Error parsing block: {e}")

    # Print or Save as JSON
    for idx, exp in enumerate(experience_data, 1):
        print(f"\nExperience #{idx}")
        for key, val in exp.items():
                print(f"{key}: {val}")

    with open(os.path.join(output_dir,f"{user_name}_education.json"), "w", encoding="utf-8") as f:
        json.dump(experience_data, f, indent=2, ensure_ascii=False)

    return experience_data


def initialize_web_driver(username,password):
    # Set up Chrome WebDriver
    # Set up Chrome WebDriver
    from webdriver_manager.chrome import ChromeDriverManager

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # Open the login page (replace with actual URL)
    driver.get("https://www.linkedin.com/login/")

    # Wait for fields to load
    wait = WebDriverWait(driver, 10)

    # Step 3: Find username field and enter email
    username_input = driver.find_element(By.ID, "username")
    username_input.send_keys(username)

    # Step 4: Find password field and enter password
    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys(password)

    # Step 5: Click on Sign In button
    sign_in_button = driver.find_element(By.XPATH, '//button[@type="submit" and contains(@class, "btn__primary--large")]')
    sign_in_button.click()

    # Optional: wait and print page title
    time.sleep(120)
    print("Login attempted. Current page title:", driver.title)

    return driver


def linkedin_ID_searcher(search_id,driver):
    
    load_dotenv()

    username = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')


    #driver = initialize_web_driver(username,password)
    
    time.sleep(40)

    # search_id = 'sendeepin'


    output_dir = f"{search_id}_data_linkedin"  # Folder name

    os.makedirs(output_dir, exist_ok=True)  # Create folder if it doesn't exist

    bio = get_bio(search_id,driver,output_dir)
    
    time.sleep(20)
    experience = get_experience(search_id,driver,output_dir)

    time.sleep(20)
    education = get_education(search_id,driver,output_dir)

    profile_data = {
        "User ID": search_id,
        "Bio": bio,
        "Experience": experience,
        "Education": education
    }

    # Save to single JSON
    output_file = os.path.join(output_dir, f"{search_id}_profile_data.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2, ensure_ascii=False)

    print(f"\nProfile data saved to: {output_file}")

    return profile_data


def main():

    search_id = 'sendeepin'
    final_data = linkedin_ID_searcher(search_id)



if __name__ == "__main__":
    main()    




