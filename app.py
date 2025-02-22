import streamlit as st
from streamlit import session_state as ss
from streamlit_pdf_viewer import pdf_viewer

import time

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
    if "selected_tones" not in st.session_state:
        st.session_state["selected_tones"] = []
    if "selected_audiences" not in st.session_state:
        st.session_state["selected_audiences"] = []
    if "topic" not in st.session_state:
        st.session_state["topic"] = ""

    # Display topic as a text input
    st.write("### Topic:")
    topic = st.text_input("Topic", value=st.session_state["topic"], placeholder="e.g., Artificial Intelligence in Healthcare", label_visibility='hidden')
    st.session_state["topic"] = topic

    # Display tone options as a segmented control
    st.write("### Tone:")
    selected_tones = st.segmented_control(
        "Tones", tone_options, default=st.session_state["selected_tones"], selection_mode="multi", label_visibility='hidden'
    )
    st.session_state["selected_tones"] = selected_tones

    # Display audience options as a segmented control
    st.write("### Audience Type:")
    selected_audiences = st.segmented_control(
        "Audiences", audience_options, default=st.session_state["selected_audiences"], selection_mode="multi", label_visibility='hidden'
    )
    st.session_state["selected_audiences"] = selected_audiences

    # Proceed to the next page
    if st.button("Next"):
        if st.session_state["selected_tones"] and st.session_state["selected_audiences"] and st.session_state["topic"]:
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
            st.audio(audio_file.read(), format="audio/wav")

            # Save the audio file
            try:
                # Reset the file pointer to the beginning
                audio_file.seek(0)
                # Read the audio data
                audio_bytes = audio_file.read()
                # Save the audio data to a file
                with open("recording.wav", "wb") as f:
                    f.write(audio_bytes)
                st.session_state["page"] = "feedback"
                st.rerun()  # Force rerun to immediately navigate to the next page
            except Exception as e:
                st.error(f"An error occurred while saving the audio file: {e}")

def feedback_page():
    _response = """Your presentation was clear and engaging. However, try to speak more slowly and emphasize key points.
    Your presentation was clear and engaging. However, try to speak more slowly and emphasize key points.
    Your presentation was clear and engaging. However, try to speak more slowly and emphasize key points."""

    # Function to stream the AI feedback
    def stream_data():
        for word in _response.split(" "):
            yield word + " "
            time.sleep(0.1)
        # Set a flag to indicate streaming is complete
        st.session_state["streaming_complete"] = True

    # Start streaming the AI feedback
    st.write_stream(stream_data)

    # Load and play the user_cloned_voice_speech.wav file

    if st.session_state.get("streaming_complete", False):

        st.write("### Your Cloned Voice Speech")
        try:
            with open("user_cloned_voice_speech.wav", "rb") as f:
                audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/wav")
        except FileNotFoundError:
            st.error("The cloned voice speech file was not found. Please ensure the file exists.")


        if st.button("Restart"):
            st.session_state.clear()
            st.session_state["page"] = "setup"
            st.rerun()  # Force rerun to immediately navigate to the setup page

# Page routing
if st.session_state["page"] == "setup":
    setup_page()
elif st.session_state["page"] == "upload_pdf":
    upload_pdf_page()
elif st.session_state["page"] == "slides":
    slides_page()
elif st.session_state["page"] == "feedback":
    feedback_page()
