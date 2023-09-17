import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import spacy
from spacy.lang.en.stop_words import STOP_WORDS #python -m spacy download en_core_web_sm
from string import punctuation
from heapq import nlargest 

load_dotenv()

def summarize(text, per):
    nlp = spacy.load('en_core_web_sm')
    doc= nlp(text)
    tokens=[token.text for token in doc]
    word_frequencies={}
    for word in doc:
        if word.text.lower() not in list(STOP_WORDS):
            if word.text.lower() not in punctuation:
                if word.text not in word_frequencies.keys():
                    word_frequencies[word.text] = 1
                else:
                    word_frequencies[word.text] += 1
    max_frequency=max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word]=word_frequencies[word]/max_frequency
    sentence_tokens= [sent for sent in doc.sents]
    sentence_scores = {}
    for sent in sentence_tokens:
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if sent not in sentence_scores.keys():                            
                    sentence_scores[sent]=word_frequencies[word.text.lower()]
                else:
                    sentence_scores[sent]+=word_frequencies[word.text.lower()]
    select_length=int(len(sentence_tokens)*per)
    summary=nlargest(select_length, sentence_scores,key=sentence_scores.get)
    final_summary=[word.text for word in summary]
    summary=''.join(final_summary)
    return summary

# Set the API endpoint and your API key
url = "https://api.openai.com/v1/completions"

api_key = os.environ.get('OPENAI_API_KEY')
print(api_key)

news_link = st.text_input('Enter a news URL link, please')
if st.button('Enter'):
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
    summary_from_spacy = summarize(text, 0.05)
    st.text_area(label ="Response",value=text, height =500)
    st.write("summary: ", summary_from_spacy)



