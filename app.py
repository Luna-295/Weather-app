import streamlit as st
from groq import Groq
import os
import requests
from dotenv import load_dotenv
import json
import time

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
api_key = os.getenv("OPENWEATHERMAP_API_KEY")
def get_current_weather(location, unit):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units={unit}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return (f"The current weather in {json.dumps(data['name'])} is {json.dumps(data['weather'][0]['description'])}. The temperature is {json.dumps(data['main']['temp'])} degrees.")
    else:
        return (f"Error: {response.status_code} - {response.reason}")



tools = [
        {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather or temperature in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                    },
                },   

                "required": ["location"],
            },
        },
    }
]
print("Initializing session state...")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hey, how can I help you?"}]
print("Session state initialized.")
st.title("💬 Weather Chatbot")
st.caption("🚀 A streamlit chatbot powered by Llama LLM")
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Write Something"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    time.sleep(2)
    response = client.chat.completions.create(
        model="mixtral-8x7b-32768", 
        messages=[
            {"role": "system", 
             "content": "You are a helpful assistant? Incase the user asks for weather update you trigger the function get_current_weather() to get the current weather. Do not use any historical data"
            }, *st.session_state.messages
        ],
        tool_choice = "auto",
        tools = tools,
        max_tokens = 2048,
    )
    reply = response.choices[0].message.content    
    tool_calls = response.choices[0].message.tool_calls

    if tool_calls :
        available_functions = {
            "get_current_weather": get_current_weather
        }
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_params = json.loads(tool_call.function.arguments)
            # try:
            response = get_current_weather(
                location = function_params.get("location"),
                unit =  "metric",
            )
            st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response,
                    }
                )
                
            # except Exception as e:
            #     print(f"An error occurred while calling function {function_name}: {e}")
            #     response = f"An error occurred while calling function {function_name}: {e}"
            # # st.session_state.messages.append(
            #        {
            #             "role": "assistant",
            #             "content": response,
            #         }
            #     ) 
            st.chat_message("assistant").write(response)

    
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)
