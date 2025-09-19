import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage,SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Union, List
from selenium.webdriver.remote.webdriver import WebDriver

from web_search_facebook import facebook_searcher
from web_search_insta import insta_search
from web_search_linkedin import linkedin_searcher

from facebook import facebook_ID_searcher
from instagram import Insta_ID_searcher
from linkedin import linkedin_ID_searcher

from langchain_openai import ChatOpenAI

load_dotenv()

class InputState(TypedDict):
    Actual_name: str
    last_known_location: Optional[str]
    last_known_work: Optional[str]
    extra_meta_data: Optional[Union[str, dict]]

class OverallState(TypedDict, total=False):
    input: InputState
    fb_id: Optional[str]
    insta_id: Optional[str]
    linkedin_id: Optional[str]
    fb_profile_data: Optional[dict]
    insta_profile_data: Optional[dict]
    linkedin_profile_data: Optional[dict]
    output: Optional[dict]
    fb_driver: Optional[WebDriver]
    linkedin_driver: Optional[WebDriver]
    insta_driver: Optional[WebDriver]
    fb_username: Optional[List[str]]
    fb_reason: Optional[str]
    insta_username: Optional[List[str]]
    insta_reason: Optional[str]
    ld_username: Optional[List[str]]
    ld_reason: Optional[str]


def fb_id_node(state):
    query = f'{state["input"]["Actual_name"]} IITG Facebook'
    uid,driver,usernames,reason = facebook_searcher(query, state["input"],'58987')
    return {"fb_id": uid, "fb_driver":driver,"fb_username":usernames,"fb_reason":reason}

def insta_id_node(state):
    query = f'{state["input"]["Actual_name"]} IITG Instagram'
    uid,driver,usernames,reason = insta_search(query, state["input"],'59030')
    return {"insta_id": uid, "insta_driver": driver,"insta_username":usernames,"insta_reason":reason}

def linkedin_id_node(state):
    query = f'{state["input"]["Actual_name"]} IITG Linkedin'
    uid,driver,usernames,reason = linkedin_searcher(query, state["input"],'58904')
    return {"linkedin_id": uid, "linkedin_driver":driver,"ld_username":usernames,"ld_reason":reason}

def fb_scrape_node(state):
    search_id = state.get("fb_id")
    driver = state.get('fb_driver')
    if search_id and search_id!="None":
      try:  
        profile_data = facebook_ID_searcher(search_id,driver)
        return {"fb_profile_data": profile_data}
      except:
        return {"fb_profile_data": {}} 
    return {}

def insta_scrape_node(state):
    search_id = state.get("insta_id")
    driver = state.get('insta_driver')
    if search_id and search_id!="None":
       try: 
        profile_data = Insta_ID_searcher(search_id,driver)
        return {"insta_profile_data": profile_data}
       except:
        return {"insta_profile_data": {}}   
    return {}

def linkedin_scrape_node(state):
    search_id = state.get("linkedin_id")
    driver = state.get('linkedin_driver')
    if search_id and search_id!="None":
       try: 
        profile_data = linkedin_ID_searcher(search_id,driver)
        return {"linkedin_profile_data": profile_data}
       except:
        return {"linkedin_profile_data": {}}   
    return {}

def summarize_node(state):
    llm = ChatOpenAI(api_key=os.environ['OPEN_AI_API_KEY'], model='gpt-4.1')

    input_data = state["input"]
    fb = state.get("fb_profile_data")
    insta = state.get("insta_profile_data")
    linkedin = state.get("linkedin_profile_data")
    summarize_sys_message = f'''
     You are tasked to find the the person's last known location based on the dates mentioned 
     on various social media profile, thus sort the events based on the dates and then, find out 
     the most recent time along with the dates. Also do note that the data from the various social media
     may not directly associated to the person and can be misleading, so cross check the data with the 
     initial meta_data provided and then give the answer. List down all the Locations with dates you get,
     and finally make a suitable decision.
'''
    summary_prompt = f"""
Given the following inputs:
- Name: {input_data['Actual_name']}
- Last Known Location: {input_data.get('last_known_location', 'Unknown')}
- Last Known Work: {input_data.get('last_known_work', 'Unknown')}
- Extra Metadata: {input_data.get('extra_meta_data', 'None')}
- Current Date: {input_data.get('Current_date', 'None')}

And scraped social data:
Facebook: {fb}
Instagram: {insta}
LinkedIn: {linkedin}

Summarize the person’s most recent location, activity, and risk level.
"""

    result = llm.invoke([SystemMessage(content=summary_prompt),HumanMessage(content=summary_prompt)])
    return {"output": {"summary": result.content}}


def control_id_fetch(state):
    branches = []
    if "fb_id" not in state or not state["fb_id"]:
        branches.append("fb_id_node")
    if "insta_id" not in state or not state["insta_id"]:
        branches.append("insta_id_node")
    if "linkedin_id" not in state or not state["linkedin_id"]:
        branches.append("linkedin_id_node")
    return branches if branches else ["scrape_control_node"]

def start_node(state):
    return state  # Just passes state forward

def safe_node(func, default_return=None):
    def wrapper(state):
        try:
            return func(state)
        except Exception as e:
            print(f"⚠️ Error in {func.__name__}: {e}")
            return default_return or {}
    return wrapper    

def build_graph():
    builder = StateGraph(OverallState)

    # Dummy start node
    builder.add_node("start_node", RunnableLambda(start_node))

    # ID nodes
    builder.add_node("fb_id_node", RunnableLambda(safe_node(fb_id_node, {})))
    builder.add_node("insta_id_node", RunnableLambda(safe_node(insta_id_node, {})))
    builder.add_node("linkedin_id_node", RunnableLambda(safe_node(linkedin_id_node, {})))
    builder.add_node("fb_scrape_node", RunnableLambda(safe_node(fb_scrape_node, {"fb_profile_data": {}})))
    builder.add_node("insta_scrape_node", RunnableLambda(safe_node(insta_scrape_node, {"insta_profile_data": {}})))
    builder.add_node("linkedin_scrape_node", RunnableLambda(safe_node(linkedin_scrape_node, {"linkedin_profile_data": {}})))
    builder.add_node("summarize_node", RunnableLambda(safe_node(summarize_node, {"output": {"summary": "Summary unavailable"}})))


    # Set entry point to start_node
    builder.set_entry_point("start_node")

    # Fan out to all 3 ID nodes
    builder.add_edge("start_node", "fb_id_node")
    builder.add_edge("start_node", "insta_id_node")
    builder.add_edge("start_node", "linkedin_id_node")

    # Each ID to its scraper
    builder.add_edge("fb_id_node", "fb_scrape_node")
    builder.add_edge("insta_id_node", "insta_scrape_node")
    builder.add_edge("linkedin_id_node", "linkedin_scrape_node")

    # All scrape nodes converge to summarization
    builder.add_edge("fb_scrape_node", "summarize_node")
    builder.add_edge("insta_scrape_node", "summarize_node")
    builder.add_edge("linkedin_scrape_node", "summarize_node")

    # Final
    builder.add_edge("summarize_node", END)

    return builder.compile()



if __name__ == "__main__":

    graph = build_graph()
    
    input_data = {
        "Actual_name": "Subbiah Senthil Murugan",
        "last_known_location": "Bangalore",
        "last_known_work": "ABB Corporate Research",
        "extra_meta_data": "Studied from IIT Delhi, from Chennai",
        "Current_date": "8th August, 2025"
    }

    result = graph.invoke({"input": input_data})
    with open('Final_analysis.txt','w',encoding='utf-8') as f:
        f.write(result["output"]["summary"])

    print("\nFinal Output:")
    print(result["output"]["summary"])
