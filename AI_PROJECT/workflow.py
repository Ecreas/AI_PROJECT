import streamlit as st
import json
import re
import os  


@st.cache_data
def get_menu_items(filename="menu_items.json"):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    
    try:
        with open(file_path, 'r') as f:
            menu_items = json.load(f)
        return menu_items
    except FileNotFoundError:
        st.error(f"Error: The data file was not found at {file_path}.")
        return []
    except json.JSONDecodeError:
        st.error(f"Error: Could not read {filename}. Make sure it is a valid JSON.")
        return []

# --- PHASE 2: AI RECOMMENDATION (Objective 1) ---
def get_recommendations(all_items, preferences):
    
    recommended_items = all_items
    
    # 1. Filter by Budget
    if preferences.get('budget'):
        recommended_items = [
            item for item in recommended_items if item['price'] <= preferences['budget']
        ]

    # 2. Filter by Category
    if preferences.get('category') and preferences['category'] != 'any':
        recommended_items = [
            item for item in recommended_items 
            if item['category'].lower() == preferences['category']
        ]

    # 3. Filter by Dietary Needs
    if preferences.get('is_vegan'):
        recommended_items = [item for item in recommended_items if item['is_vegan']]
    if preferences.get('is_vegetarian'):
        recommended_items = [item for item in recommended_items if item['is_vegetarian']]
    if preferences.get('is_gluten_free'):
        recommended_items = [item for item in recommended_items if item['is_gluten_free']]

    # 4. Filter by Allergies (Avoid)
    if preferences.get('avoid_nuts'):
        recommended_items = [item for item in recommended_items if not item['contains_nuts']]
    if preferences.get('avoid_dairy'):
        recommended_items = [item for item in recommended_items if not item['contains_dairy']]

    return recommended_items

# --- PHASE 3: STREAMLIT CHATBOT INTERFACE (Objective 2) ---

# Helper function to add a message to the chat
def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

# Helper function to get the next bot question and update state
def ask_next_question(user_prompt):
    current_question = st.session_state.current_question
    preferences = st.session_state.preferences

    # State 1: Start
    if current_question == 'start':
        add_message("bot", "Let me hel you to find the perfect meal, but first I need to ask you a few quick questions.")
        add_message("bot", "Do you have any dietary needs? (e.g., vegan, vegetarian, gluten-free, or just 'none')")
        st.session_state.current_question = 'diet'

    # State 2: Parse Diet, Ask Allergies
    elif current_question == 'diet':
        prompt = user_prompt.lower()
        if "vegan" in prompt: preferences['is_vegan'] = True
        if "vegetarian" in prompt: preferences['is_vegetarian'] = True
        if "gluten" in prompt: preferences['is_gluten_free'] = True
        
        add_message("bot", "Roger that. Any allergies to avoid? (e.g., nuts, dairy, or 'none')")
        st.session_state.current_question = 'allergies'

    # State 3: Parse Allergies, Ask Budget
    elif current_question == 'allergies':
        prompt = user_prompt.lower()
        if "nut" in prompt: preferences['avoid_nuts'] = True
        if "dairy" in prompt: preferences['avoid_dairy'] = True
        
        add_message("bot", "What's your budget? (e.g., '10', '15', or 'no budget')")
        st.session_state.current_question = 'budget'

    # State 4: Parse Budget, Ask Category
    elif current_question == 'budget':
        prompt = user_prompt.lower()
        # Use regex to find the first number in the string
        match = re.search(r'\d+\.?\d*', prompt)
        if match:
            preferences['budget'] = float(match.group())
        
        add_message("bot", "Last question: are you looking for a 'Main' course, 'Snack', 'Drink', or 'Any'?")
        st.session_state.current_question = 'category'

    # State 5: Parse Category, Run Search
    elif current_question == 'category':
        prompt = user_prompt.lower()
        if 'main' in prompt: preferences['category'] = 'main'
        elif 'snack' in prompt: preferences['category'] = 'snack'
        elif 'drink' in prompt: preferences['category'] = 'drink'
        else: preferences['category'] = 'any'
        
        # --- Run the AI Search ---
        add_message("bot", "perfect, searching for recommendations based on your preferences...")
        
        results = get_recommendations(st.session_state.menu_data, preferences)
        
        if not results:
            add_message("bot", "Sorry, I couldn't find any items that match all your preferences. Try searching again!")
        else:
            message = f"I found {len(results)} option(s) for you:\n"
            for item in results:
                message += f"\n- **{item['item_name']}** at {item['outlet_name']} (RM{item['price']:.2f})"
            add_message("bot", message)

        add_message("bot", "Would you like to start a new search? (Just say 'hi' or 'yes')")
        # Reset for the next conversation
        st.session_state.current_question = 'start'
        st.session_state.preferences = {}


# --- Main App Execution ---

st.set_page_config(page_title="UTP Food Bot", layout="centered")
st.title("🤖 UTP Food Chatbot")

# Load data once
if "menu_data" not in st.session_state:
    st.session_state.menu_data = get_menu_items()

# Initialize chat history and state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.current_question = 'start'
    st.session_state.preferences = {}
    add_message("bot", "Hi! I'm the UTP Food Bot. I can help you find daily meal options on campus. Are you looking for a recommendation?")

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get new user input
if prompt := st.chat_input("What's up?"):
    # Add user message to chat history
    add_message("user", prompt)
    
    # Handle the user's response and ask the next question
    if st.session_state.menu_data:
        ask_next_question(prompt)
    else:
        add_message("bot", "Sorry, the menu data isn't loaded. I can't help right now.")

    # Rerun the app to display the new messages immediately

    st.rerun()
