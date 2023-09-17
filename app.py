import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from metaphor_python import Metaphor
from twilio.rest import Client
from metaphor_python import Metaphor
import boto3
from boto.s3.key import Key
from elevenlabs import generate, save, Voice, VoiceSettings
import replicate
metaphor = Metaphor("METAPHOR_API_KEY")
load_dotenv()

# Set the API endpoint and your API key
url = "https://api.openai.com/v1/completions"

api_key = os.environ.get('OPENAI_API_KEY')

news_link = st.text_input('Enter a news URL link, please')
user_num = st.text_input("Enter your phone # to get the mp3 file played, please")
if st.button('Enter'):
    resp1 = requests.get(news_link)
    soup = BeautifulSoup(resp1.text, 'html.parser')

    # Extract text data from website
    text_data = ''
    for tag in soup.find_all(['p']):
        text_data += tag.get_text()

    print('text_data' , text_data)
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
    print(response_data)
    text = response_data['choices'][0]['text']
    print(text)
    st.text_area(label ="Response",value=text, height =500)
    st.write("Text: ", text)

    output = replicate.run(
        "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
        input={"prompt": "Offer hot takes on the following article from the perspective of a Gen Z tiktoker for a new tiktok series called 'for the girlies' using the most stereotypical gen z slang terms. Do not use emojis or hashtags. Use metaphors that would be very relatable to gen Z. The first line should be 'heyyyy girlies!!!'. The article to summarize: " + text,
               "max_new_tokens":2000}
    )
    genz_resp_data = ''
    for item in output:
        genz_resp_data+=item
        print(item, end="")
    print("genz_resp_data ", genz_resp_data)

    audio = generate(
        text=genz_resp_data,
        api_key= os.environ.get('ELEVEN_API_KEY'),
        voice=Voice(
            voice_id='5Rfw7GYjcN1FJLU7i8je',
            settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
        ),
        model='eleven_monolingual_v1'
    )

    save(audio, 'genz.wav')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

    bucket_name = os.environ.get('AWS_BUCKET_NAME')
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    s3 = session.resource('s3')
    # Filename - File to upload
    # Bucket - Bucket to upload to (the top level directory under AWS S3)
    # Key - S3 object name (can contain subdirectories). If not specified then file_name is used
    s3.meta.client.upload_file(Filename='genz.wav', Bucket=bucket_name, Key='genz.wav', ExtraArgs={
        "ContentType":"audio/mpeg"
    })
 
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)
    twiml = "<Response><Play>https://hackathon12345.s3.amazonaws.com/genz.wav</Play></Response>"
    call = client.calls.create( 
        twiml = twiml,
        to=user_num,
        from_='+18668453916'
    )
    print(call.sid)




