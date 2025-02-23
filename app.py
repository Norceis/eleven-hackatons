import json
import os

import streamlit as st
import fal_client
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from streamlit_pdf_viewer import pdf_viewer
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env', override=True)

AUDIO_DPATH = 'audio'
os.makedirs(AUDIO_DPATH, exist_ok=True)

SPEECH_FPATH = os.path.join(AUDIO_DPATH, 'speech_recording.mp3')
IMPROVED_SPEECH_FPATH = os.path.join(AUDIO_DPATH, 'speech_improved.mp3')

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
    api_key=os.getenv('ELEVENLABS_API_KEY')
)


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
    f"  \"general_opinion\": {{"
    f"    \"comment\": \"\""
    f"  }}"
    f"}}"
    f"The speech is as follows: {instructions['speech']}"
    )
    return llm_instructions


def generate_and_validate_speech_json(llm_instructions):
    with st.spinner(text="Painting the grass green..."):
        while True:
            unique_keynames=set()
            unique_keynames_nested=set()
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
                unique_keynames.update(json_object.keys())
                for key in json_object.keys():
                    if isinstance(json_object[key], dict):
                        unique_keynames_nested.update(json_object[key].keys())
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
    with st.spinner(text="Looking at the sun..."):
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
        with st.spinner(text="Swimming through molass..."):
            response = CLIENT_ELEVEN.voices.add(
                name=name,
                remove_background_noise=True,
                files=[(input_file_path, audio_file, 'mp3')]
            )

        return response.voice_id


def text_to_speech(text, voice_id):
    with st.spinner(text="Counting sheep..."):
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

    # Return the path of the saved audio file
    return IMPROVED_SPEECH_FPATH


# Initialize session state keys
if 'pdf_ref' not in st.session_state:
    st.session_state.pdf_ref = None
if 'page' not in st.session_state:
    st.session_state.page = "setup"

def setup_page():
    st.markdown("<h1 style='text-align: center;'>Speech Coach</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Provide the details about your speech</h3>", unsafe_allow_html=True)

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
    st.write("### Audience:")
    audience = st.segmented_control(
        "Audiences", audience_options, default=st.session_state["audience"], selection_mode="multi", label_visibility='hidden'
    )
    st.session_state["audience"] = audience

    # Proceed to the next page
    if st.button("Next"):
        if st.session_state["tone"] and st.session_state["audience"] and st.session_state["goal"]:
            st.session_state["page"] = "upload_pdf"
            st.rerun()  # Force rerun to immediately navigate to the next page
        else:
            st.error("Please fill out all fields.")

def upload_pdf_page():
    st.markdown("<h1 style='text-align: center;'>Upload slides and speech</h1>", unsafe_allow_html=True)

    # Access the uploaded ref via a key.
    uploaded_pdf = st.file_uploader("Upload PDF file", type=('pdf'), key='pdf', label_visibility='hidden')

    if uploaded_pdf:
        st.session_state.pdf_ref = uploaded_pdf  # Store the uploaded PDF in session state
        st.session_state["page"] = "slides"  # Move to the slides page
        st.rerun()  # Force rerun to immediately navigate to the next page

def slides_page():
    if st.session_state.pdf_ref:
        # Display the uploaded PDF
        binary_data = st.session_state.pdf_ref.getvalue()
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

                with st.spinner(text="Catching wind..."):
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
                text_to_speech(refined_speech, voice_id)


                st.session_state["page"] = "feedback"
                st.rerun()  # Force rerun to immediately navigate to the next page
            except Exception as e:
                st.error(f"An error occurred while saving the audio file: {e}")

def feedback_page():
    feedback = st.session_state["feedback"] #{'test': {'achieved': True}}

    # Convert feedback data to a table format
    st.markdown("<h1 style='text-align: center;'>Speech feedback</h1>", unsafe_allow_html=True)

    # Display feedback in a nicely formatted way
    for key, value in feedback.items():
        if key != "general_opinion":
            st.subheader(f"{key.capitalize()} {'✅' if value['achieved'] else '❌'}")
            st.write(f"{value['comment']}")

    # Display General Opinion
    st.subheader("General Opinion")
    st.write(feedback['general_opinion']['comment'])

    # Load and play the improved file
    st.write("### Listen to your refined speech")

    try:
        with open(IMPROVED_SPEECH_FPATH, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mpeg")
    except FileNotFoundError:
        st.error("The cloned voice speech file was not found. Please ensure the file exists.")


# Page routing
if st.session_state["page"] == "setup":
    setup_page()
elif st.session_state["page"] == "upload_pdf":
    upload_pdf_page()
elif st.session_state["page"] == "slides":
    slides_page()
elif st.session_state["page"] == "feedback":
    feedback_page()
