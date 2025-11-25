import streamlit as st
import json
import re
import os
from thefuzz import process, fuzz 

#getting the json
@st.cache_data
def get_menu_items(filename="menu_items.json"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    try:
        with open(file_path, 'r') as file:
            menu_items = json.load(file)
        return menu_items
    except FileNotFoundError:
        st.error(f"Error: The data file was not found at: {file_path}")
        return []
    except json.JSONDecodeError:
        st.error(f"Error: Could not read {filename}. Make sure it is a valid JSON.")
        return []

# main filter
def get_recommendations(all_items, preferences):
    recommended_items = all_items
    
    # Budget filter
    if preferences.get('budget'):
        recommended_items = [item for item in recommended_items if item['price'] <= preferences['budget']]

    # Category filter
    if preferences.get('category') and preferences['category'] != 'any':
        recommended_items = [item for item in recommended_items if item['category'].lower() == preferences['category']]

    # Diet filters
    if preferences.get('is_vegan'):
        recommended_items = [item for item in recommended_items if item['is_vegan']]
    if preferences.get('is_vegetarian'):
        recommended_items = [item for item in recommended_items if item['is_vegetarian']]
    if preferences.get('is_gluten_free'):
        recommended_items = [item for item in recommended_items if item['is_gluten_free']]

    # Allergy filters
    if preferences.get('avoid_nuts'):
        recommended_items = [item for item in recommended_items if not item['contains_nuts']]
    if preferences.get('avoid_dairy'):
        recommended_items = [item for item in recommended_items if not item['contains_dairy']]
    if preferences.get('avoid_shellfish'):
        recommended_items = [item for item in recommended_items if not item['contains_shellfish']]   

    return recommended_items

# interface

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

def ask_next_question(user_prompt):
    current_question = st.session_state.current_question
    preferences = st.session_state.preferences

    
    if current_question == 'start':
        add_message("bot", "First, I want to understand you better. First, any dietary needs? (e.g., vegan, gluten-free, or just 'none')")
        st.session_state.current_question = 'diet'

    
    elif current_question == 'diet':
        
        prompt = user_prompt.lower()
        
        if fuzz.partial_ratio("vegan", prompt) > 80: 
            preferences['is_vegan'] = True
        if fuzz.partial_ratio("gluten free", prompt) > 80: 
            preferences['is_gluten_free'] = True
        
        add_message("bot", "Got it. Any allergies? (e.g., nuts, dairy, shellfish, or 'none')")
        st.session_state.current_question = 'allergies'

    
    elif current_question == 'allergies':
        prompt = user_prompt.lower()
        
        
        if fuzz.partial_ratio("nuts", prompt) > 80: 
            preferences['avoid_nuts'] = True
        if fuzz.partial_ratio("dairy", prompt) > 80: 
            preferences['avoid_dairy'] = True
        if fuzz.partial_ratio("shellfish", prompt) > 80: 
            preferences['avoid_shellfish'] = True
        
        add_message("bot", "What's your budget? (e.g., '10', '15')")
        st.session_state.current_question = 'budget'

    
    elif current_question == 'budget':
        match = re.search(r'\d+\.?\d*', user_prompt)
        if match:
            preferences['budget'] = float(match.group())
        
        add_message("bot", "Last question: What are you in the mood for? (e.g., 'lunch', 'coffee', 'fries')")
        st.session_state.current_question = 'category'


    elif current_question == 'category':
        
        keyword_map = {
            "main course": "main", "lunch": "main", "dinner": "main", "rice": "main", "chicken": "main", "heavy": "main",
            "snack": "snack", "fries": "snack", "bite": "snack", "light food": "snack",
            "drink": "drink", "coffee": "drink", "tea": "drink", "beverage": "drink", "latte": "drink", "thirsty": "drink", "sip": "drink",
            "anything": "any", "whatever": "any", "surprise": "any"
        }
        
        possible_keywords = list(keyword_map.keys())
        best_match, score = process.extractOne(user_prompt, possible_keywords)
        
        if score > 60:
            detected_category = keyword_map[best_match]
            preferences['category'] = detected_category
            add_message("bot", f"so you want **'{best_match}'**. Got it! Searching for **{detected_category.upper()}** options...")
        else:
            preferences['category'] = 'any'
            add_message("bot", "Sorry but I don't quite understand your request, I'll instead search for **ANYTHING**.")


        #search
        results = get_recommendations(st.session_state.menu_data, preferences)
        
        if not results:
            add_message("bot", "Sorry, I couldn't find any items. Try searching again!")
        else:
            msg = f"I found {len(results)} option(s):\n"
            for item in results:
                outlet = item.get('outlet_name', 'Unknown Outlet')
                price = item.get('price', 0.0)
                msg += f"\n- **{item['item_name']}** at {outlet} (RM{price:.2f})"
            add_message("bot", msg)

        add_message("bot", "Type 'reset' to start over.")
        st.session_state.current_question = 'start'
        st.session_state.preferences = {}

# main 

st.set_page_config(page_title="UTP Food Bot", layout="centered")
st.title("🤖 UTP Food Chatbot")

if "menu_data" not in st.session_state:
    st.session_state.menu_data = get_menu_items()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.current_question = 'start'
    st.session_state.preferences = {}
    add_message("bot", "Hi! I'm the UTP Food Bot. Ready to find food?")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Type here..."):
    add_message("user", prompt)
    
    if prompt.lower() in ['reset', 'restart', 'start over']:
        st.session_state.current_question = 'start'
        st.session_state.preferences = {}
        st.session_state.messages = []
        add_message("bot", "Let's start over! Do you have any dietary needs?")
        st.rerun()
    
    if st.session_state.menu_data:
        ask_next_question(prompt)
    else:
        add_message("bot", "Error: Menu data not loaded.")
    
    st.rerun()
