import json
import time
import os

import fal_client
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import streamlit as st
from streamlit import session_state as ss
from streamlit_pdf_viewer import pdf_viewer
from dotenv import load_dotenv

load_dotenv(dotenv_path='/home/ikolasa/Projects/eleven-hackatons/.env')

SPEECH_FPATH = 'speech_recording.mp3'
IMPROVED_SPEECH_FPATH = 'speech_improved.mp3'

TEMPLATE_UNIQUE_KEYNAMES = {
    "goal",
    "tone",
    "audience",
    "general_opinion"
}

TEMPLATE_UNIQUE_KEYNAMES_NESTED = {
    "achieved",
    "comment"
}


CLIENT_ELEVEN = ElevenLabs(
    api_key='sk_8a685af1bfce270f039376f3374a64caafadfb478514be87'  #os.getenv('ELEVENLABS_API_KEY')
)
print(os.getenv('ELEVENLABS_API_KEY'))


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

def overwrite_prompt_instructions(instructions):
    llm_instructions = (
    f"Please give me feedback about my speech and how I can improve it. Respond in JSON format with the following keys: goal, tone, audience, general_opinion."
    f"The goal of the presentation is {instructions["goal"]}. "
    f"The tone of the presentation should be {instructions["tone"]}. "
    f"The audience for the presentation is {instructions["audience"]}. "
    #f"Additional information: {data['additional information']}. "
    f"The template for your response should be as follows:"
    f"{{"
    f"  \"goal\": {{"
    f"    \"achieved\": true/false,"
    f"    \"comment\": \"\""
    f"  }},"
    f"  \"tone\": {{"
    f"    \"achieved\": true/false,"
    f"    \"comment\": \"\""
    f"  }},"
    f"  \"audience\": {{"
    f"    \"achieved\": true/false,"
    f"    \"comment\": \"\""
    f"  }},"
    #f"  \"additional_information\": {{"
    #f"    \"comment\": \"\""
    #f"  }},"
    f"  \"general_opinion\": {{"
    f"    \"comment\": \"\""
    f"  }}"
    f"}}"
    f"The speech is as follows: {instructions['speech']}"
    )
    return llm_instructions


def generate_and_validate_speech_json(llm_instructions):
    while True:
        unique_keynames=set()
        unique_keynames_nested=set()
        # for i in tqdm(range(100)):
        result = fal_client.subscribe(
            "fal-ai/any-llm",
            arguments={
                "prompt": llm_instructions
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )

        try:
            json_string = result['output'][7:-4]

            json_object = json.loads(json_string)
            # print(json_object)
            unique_keynames.update(json_object.keys())
            for key in json_object.keys():
                if isinstance(json_object[key], dict):
                    unique_keynames_nested.update(json_object[key].keys())
            # print(unique_keynames)
            # print(TEMPLATE_UNIQUE_KEYNAMES)
            # print(unique_keynames_nested)
            # print(TEMPLATE_UNIQUE_KEYNAMES_NESTED)
            if unique_keynames == TEMPLATE_UNIQUE_KEYNAMES and unique_keynames_nested == TEMPLATE_UNIQUE_KEYNAMES_NESTED:
                break
        except json.JSONDecodeError:
            continue

    return json_object


def create_refine_prompt(json_object, instructions):
    refining_prompt = (
    f"Please refine the speech according to these suggestions"
    f"{json_object}"
    f"\n"
    f"Try to keep the length of the refined text similar to the original"
    f"The speech is as follows: {instructions['speech']}"
    )
    return refining_prompt


def refine_speech(refining_prompt):
    result = fal_client.subscribe(
        "fal-ai/any-llm",
        arguments={
            "prompt": refining_prompt
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    return result['output'][7:-4]


def add_voice_clone(input_file_path, name):
    """Adds your voice clone to the
    list of available voices"""
    with open(input_file_path, "rb") as audio_file:
        response = CLIENT_ELEVEN.voices.add(
            name=name,
            remove_background_noise=True,
            files=[(input_file_path, audio_file, 'mp3')]
        )

        return response.voice_id


def text_to_speech(text, voice_id):
    response = CLIENT_ELEVEN.text_to_speech.convert(
        voice_id=voice_id,
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # Writing the audio to a file
    with open(IMPROVED_SPEECH_FPATH, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{IMPROVED_SPEECH_FPATH}: A new audio file was saved successfully!")

    # Return the path of the saved audio file
    return IMPROVED_SPEECH_FPATH


# Initialize session state keys
if 'pdf_ref' not in ss:
    ss.pdf_ref = None
if 'page' not in ss:
    ss.page = "setup"

def setup_page():
    st.title("SPEECH 2.0")

    # Define options for tone and audience
    tone_options = ["Formal", "Casual", "Persuasive", "Informative", "Inspirational"]
    audience_options = ["Students", "Professionals", "Executives", "General Public", "Technical Experts"]

    # Initialize session state for selected options
    if "tone" not in st.session_state:
        st.session_state["tone"] = []
    if "audience" not in st.session_state:
        st.session_state["audience"] = []
    if "goal" not in st.session_state:
        st.session_state["goal"] = ""

    # Display goal as a text input
    st.write("### Topic:")
    goal = st.text_input("Topic", value=st.session_state["goal"], placeholder="e.g., Artificial Intelligence in Healthcare", label_visibility='hidden')
    st.session_state["goal"] = goal

    # Display tone options as a segmented control
    st.write("### Tone:")
    tone = st.segmented_control(
        "Tones", tone_options, default=st.session_state["tone"], selection_mode="multi", label_visibility='hidden'
    )
    st.session_state["tone"] = tone

    # Display audience options as a segmented control
    st.write("### Audience Type:")
    audience = st.segmented_control(
        "Audiences", audience_options, default=st.session_state["audience"], selection_mode="multi", label_visibility='hidden'
    )
    st.session_state["audience"] = audience

    #print(data)

    # Proceed to the next page
    if st.button("Next"):
        if st.session_state["tone"] and st.session_state["audience"] and st.session_state["goal"]:
            st.session_state["page"] = "upload_pdf"
            st.rerun()  # Force rerun to immediately navigate to the next page
        else:
            st.error("Please fill out all fields.")

def upload_pdf_page():
    st.title("UPLOAD YOUR SLIDES")

    # Access the uploaded ref via a key.
    uploaded_pdf = st.file_uploader("Upload PDF file", type=('pdf'), key='pdf', label_visibility='hidden')

    if uploaded_pdf:
        ss.pdf_ref = uploaded_pdf  # Store the uploaded PDF in session state
        st.session_state["page"] = "slides"  # Move to the slides page
        st.rerun()  # Force rerun to immediately navigate to the next page

def slides_page():
    if ss.pdf_ref:
        # Display the uploaded PDF
        binary_data = ss.pdf_ref.getvalue()
        pdf_viewer(input=binary_data, width='100%', height=500)

        # Audio recording
        audio_file = st.audio_input("audio input", label_visibility='hidden')

        if audio_file:
            # Play the recorded audio
            st.audio(audio_file.read(), format="audio/mpeg")

            # Save the audio file
            try:
                # Reset the file pointer to the beginning
                audio_file.seek(0)
                # Read the audio data
                audio_bytes = audio_file.read()
                # Save the audio data to a file
                with open(SPEECH_FPATH, "wb") as f:
                    f.write(audio_bytes)

                # voice cloning
                voice_id = add_voice_clone(SPEECH_FPATH, name='TEST_CLONE')

                audio_url = fal_client.upload_file(SPEECH_FPATH)
                handler = fal_client.submit(
                    "fal-ai/whisper",
                    arguments={
                        "audio_url": audio_url
                    },
                )

                request_id = handler.request_id
                result = fal_client.result("fal-ai/whisper", request_id)

                st.session_state["speech_instructions"] = {
                "goal": st.session_state["goal"],
                "tone": st.session_state["tone"],
                "audience": st.session_state["audience"],
                #"additional information": "make sure i sound smart",
                "speech": result['text']
                }
                llm_instructions = overwrite_prompt_instructions(st.session_state["speech_instructions"])
                validated_json_review = generate_and_validate_speech_json(llm_instructions)
                #print(validated_json_review)  # DO TABELKI
                st.session_state["feedback"] = validated_json_review

                refining_prompt = create_refine_prompt(validated_json_review, st.session_state["speech_instructions"])
                refined_speech = refine_speech(refining_prompt)

                # generate refined speech with your voice
                print(refine_speech)
                text_to_speech(refined_speech, voice_id)


                st.session_state["page"] = "feedback"
                st.rerun()  # Force rerun to immediately navigate to the next page
            except Exception as e:
                st.error(f"An error occurred while saving the audio file: {e}")

def feedback_page():
    feedback = st.session_state["feedback"] #{'test': {'achieved': True}}

    # Convert feedback data to a table format
    st.title("Speech Feedback Overview")

    # Display feedback in a nicely formatted way
    for key, value in feedback.items():
        if key != "general_opinion":
            st.subheader(f"{key.capitalize()} {'✅' if value['achieved'] else '❌'}")
            st.write(f"{value['comment']}")

    # Display General Opinion
    st.subheader("General Opinion")
    st.write(feedback['general_opinion']['comment'])

    # Load and play the improved file
    st.write("### Listen to your improved speech")

    try:
        with open(IMPROVED_SPEECH_FPATH, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mpeg")
    except FileNotFoundError:
        st.error("The cloned voice speech file was not found. Please ensure the file exists.")

    if st.button("Restart"):
        st.session_state.clear()
        st.session_state["page"] = "setup"
        st.rerun()  # Force rerun to immediately navigate to the setup page'''

# Page routing
if st.session_state["page"] == "setup":
    setup_page()
elif st.session_state["page"] == "upload_pdf":
    upload_pdf_page()
elif st.session_state["page"] == "slides":
    slides_page()
elif st.session_state["page"] == "feedback":
    feedback_page()
