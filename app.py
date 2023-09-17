import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()
# Set the API endpoint and your API key
url = "https://api.openai.com/v1/completions"

api_key = os.environ.get('OPENAI_API_KEY')
print(api_key)

news_link = st.text_input('Enter a news URL link, please')

resp1 = requests.get(news_link)
soup = BeautifulSoup(resp1.text, 'html.parser')

# Extract text data from website
text_data = ''
for tag in soup.find_all(['p']):
    text_data += tag.get_text()

print(text_data)
# Set the request headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
}

# Set the request data
data = { 
    "model": "text-davinci-003",
    "prompt": "Parse the following from a webpage to get the main body of the webpage: " + text_data,
    "suffix": "python",
    "max_tokens": 1000,
    "temperature": 0.1,
}
# Send the request and store the response
response = requests.post(url, headers=headers, json=data)
# Parse the response
response_data = response.json()
text = response_data['choices'][0]['text']
st.text_area(label ="Response",value=text, height =500)

