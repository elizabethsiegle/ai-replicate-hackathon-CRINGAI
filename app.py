import streamlit as st
import os
import re
import requests
from PIL import Image
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from metaphor_python import Metaphor
from twilio.rest import Client
from metaphor_python import Metaphor
import boto3
from boto.s3.key import Key
from elevenlabs import generate, save, Voice, VoiceSettings
import replicate
metaphor = Metaphor(os.environ.get("METAPHOR_API_KEY"))
load_dotenv()
st.title('for the girlies🫶')

image = Image.open('trisha.jpeg')
st.image(image, caption='Trisha Paytas (Lizzie does not know who this is)')

# Set the API endpoint and your API key
url = "https://api.openai.com/v1/completions"

api_key = os.environ.get('OPENAI_API_KEY')

news_link = st.text_input('Enter a news link, please') # news_link = "https://www.sfexaminer.com/news/housing/state-grants-favor-fewer-cars-more-housing-for-sf/article_55465cbc-533a-11ee-bcd6-4fea207c4ac9.html" #st.text_input('Enter a news URL link, please')
news_options = st.multiselect(
    'What news are you interested in?',
    ['tennis', 'pop culture', 'urbanism', 'politics','Housing', 'San Francisco'],
    ['Housing', 'San Francisco'])

st.write('You selected:', news_options)
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
    metaphor_sim_res = metaphor.find_similar( #find similar
        news_link,
        num_results=1,
        start_published_date="2023-09-01", #hard-coded Sept 1
        end_published_date="2023-09-17", #hard-coded to day of hackathon
    )

    # Define a regular expression pattern to match URLs
    url_pattern = r"https?://\S+"

    # Use the findall function to extract all URLs from the input string
    urls = re.findall(url_pattern, str(metaphor_sim_res))

    # Check if any URLs were found
    met_url = ''
    if urls:
        # Print the first URL found in the string
        print("Metaphor URL:", urls[0])
        met_url=urls[0]
    else:
        met_url = 0
        print("No URL found in the input string.")
    # Set the request data
    data = { 
        "model": "text-davinci-003",
        "prompt": "Summarize this article contained in the main body of the webpage: " + text_data,
        "max_tokens": 2400,
        "temperature": 0.1,
    }
    resp2 = requests.get(met_url)
    soup2 = BeautifulSoup(resp2.text, 'html.parser')

    # Extract text data from website
    text_data2 = ''
    for tag in soup2.find_all(['p']):
        text_data2 += tag.get_text()

    print('text_data2' , text_data2)
    data2 = { 
        "model": "text-davinci-003",
        "prompt": "Summarize this article contained in the main body of this text on housing: " + text_data2,
        "max_tokens": 2400,
        "temperature": 0.1,
    }
    data.update(data2) #combine 2 articles
    # Send the request and store the response
    response = requests.post(url, headers=headers, json=data)
    # Parse the response
    response_data = response.json()
    text = response_data['choices'][0]['text']
    print("response_data['choices'][0]['text'] ", text)

    output = replicate.run(
        "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
        input={"prompt": "Offer hot takes on the following articles from the perspective of a Gen Z tiktoker for a new tiktok series called 'for the girlies' using the most stereotypical gen z slang terms. Do not use emojis or hashtags. Use metaphors that would be very relatable to gen Z. The first line should be 'heyyyy girlies!!!'. The article to summarize: " + text,
               "max_new_tokens":3000}
    )
    summary = replicate.run( "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
        input={"prompt": "Summarize the following in 1 sentences:" + text,
               "max_new_tokens":1000})

    genz_resp_data = ''
    for item in output:
        genz_resp_data+=item
        print(item, end="")
    print("genz_resp_data ", genz_resp_data)
    genz_resp_data.replace('.', '!') #replace periods with exclamation points for phone call
    st.write("GenZ-ified text: ", genz_resp_data)
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
        to=user_num, #user input
        from_='+18668453916' #twilio num
    )
    
    print(call.sid)
st.write('Made w/ ❤️ by Daniel Kim && Lizzie Siegle in SF 🌁')
st.write("check out this [GitHub repo](https://github.com/elizabethsiegle/ai-replicate-hackathon-CRINGAI)")