import openai
import json
import random
import requests

from decouple import config
from fastapi import APIRouter
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import JSONResponse,StreamingResponse

# Retrieve Enviornment Variables
openai.organization = config("OPEN_AI_ORG")
openai.api_key = config("OPEN_AI_KEY")


# Open AI - Whisper
# Convert audio to text
def convert_audio_to_text(audio_file):
  try:
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    message_text = transcript["text"]
    return message_text
  except Exception :
    #return
    return "Hello!! My name is Tanvi.How can i help you ??" 


# Open AI - Chat GPT
# Convert audio to text
def get_chat_response(message_input):

  messages = get_recent_messages()
  user_message = {"role": "user", "content": message_input + " Only say doctor's name and requirement of appointment slot."}
  messages.append(user_message)
  print(messages)

  try:
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=messages
    )
    message_text = response["choices"][0]["message"]["content"]
    return message_text
  except Exception as e:
    return


# Save messages for retrieval later on
def get_recent_messages():
  # Define the file name
  file_name = "stored_data.json"
  learn_instruction = {"role": "system", 
                       "content": "You have to book an appointment for user and your name is Rachel, the user is called Alize. Keep responses under 30 words. "}
  
  # Initialize messages
  messages = []

  # Add Random Element
  x = random.uniform(0, 1)
  if x < 0.2:
    learn_instruction["content"] = learn_instruction["content"] + "Your response will have some light humour. "
  elif x < 0.5:
    learn_instruction["content"] = learn_instruction["content"] + "Your response will include an interesting new fact about Spain. "
  else:
    learn_instruction["content"] = learn_instruction["content"] + "Your response will recommend another word to learn. "

  # Append instruction to message
  messages.append(learn_instruction)

  # Get last messages
  try:
    with open(file_name) as user_file:
      data = json.load(user_file)
      
      # Append last 5 rows of data
      if data:
        if len(data) < 5:
          for item in data:
            messages.append(item)
        else:
          for item in data[-5:]:
            messages.append(item)
  except:
    pass

  
  # Return messages
  return messages


# Save messages for retrieval later on
def store_messages(request_message, response_message):
  # Define the file name
  file_name = "stored_data.json"
  # Get recent messages
  messages = get_recent_messages()[1:]
  # Add messages to data
  user_message = {"role": "user", "content": request_message}
  assistant_message = {"role": "assistant", "content": response_message}
  messages.append(user_message)
  messages.append(assistant_message)
  # Save the updated file
  with open(file_name, "w") as f:
    json.dump(messages, f)


# Save messages for retrieval later on
def reset_messages():
  # Define the file name
  file_name = "stored_data.json"
  # Write an empty file
  open(file_name, "w")


ELEVEN_LABS_API_KEY = config("ELEVEN_LAB_API_KEY")

# Eleven Labs
# Convert text to speech
def convert_text_to_speech(message):
  body = {
    "text": message,
    "voice_settings": {
        "stability": 0,
        "similarity_boost": 0
    }
  }

  voice_shaun = "mTSvIrm2hmcnOvb21nW2"
  voice_rachel = "21m00Tcm4TlvDq8ikWAM"
  voice_antoni = "ErXwobaYiN019PkySvjV"

  # Construct request headers and url
  headers = { "xi-api-key": ELEVEN_LABS_API_KEY, "Content-Type": "application/json", "accept": "audio/mpeg" }
  endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_rachel}"

  try:
    response = requests.post(endpoint, json=body, headers=headers)
  except Exception as e:
     return

  if response.status_code == 200:
      # with open("output.wav", "wb") as f:
      #     f.write(audio_data)
      return response.content
  else:
    return





#api call starts from here
router = APIRouter()

'''
 * Upload Voice Recording File 
 * @route POST /api/openai
 * @group OPENAI APIs
 * @returns JSON Object 200 - Ok
 * @returns JSON Object 422 - Unprocessable Entity
 * @returns JSON Object 500 - Internal server error
'''
@router.post("/openai")
async def post_audio(file: UploadFile = File(...)):
    try :
        # Convert audio to text - production
        # Save the file temporarily
        with open(file.filename, "wb") as buffer:
            buffer.write(file.file.read())
        audio_input = open(file.filename, "rb")
        # Decode audio
        message_decoded = convert_audio_to_text(audio_input)
        if not message_decoded :
            return JSONResponse(status_code=400, content={"status":False,"errors":[{"message":"Unable to decode audio.","code":"WN400"}]})
        # Get chat response
        chat_response = get_chat_response(message_decoded)
        # Store messages
        return store_messages(message_decoded, chat_response)
        
        # Guard: Ensure output
        if not chat_response:
            raise HTTPException(status_code=400, detail="Failed chat response")

        # Convert chat response to audio
        audio_output = convert_text_to_speech(chat_response)

        # Guard: Ensure output
        if not audio_output:
            raise HTTPException(status_code=400, detail="Failed audio output")

        # Create a generator that yields chunks of data
        def iterfile():
            yield audio_output

        # Use for Post: Return output audio
        return StreamingResponse(iterfile(), media_type="application/octet-stream")
    except Exception as e :
        return JSONResponse(tatus_code=500, content={"status":False,"errors":[{"message":str(e),"code":"WN500"}]})