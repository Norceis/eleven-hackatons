import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

load_dotenv(dotenv_path='.env')


client = ElevenLabs(
    api_key=os.getenv('ELEVENLABS_API_KEY')
)


def add_voice_clone(input_file_path, name):
    """Adds your voice clone to the
    list of available voices"""
    with open(input_file_path, "rb") as audio_file:
        response = client.voices.add(
            name=name,
            remove_background_noise=True,
            files=[(input_file_path, audio_file, 'mp3')]
        )

        return response.voice_id


def text_to_speech(text, voice_id):
    response = client.text_to_speech.convert(
        voice_id=voice_id, # Adam pre-made voice
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5", # use the turbo model for low latency
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # Generating a unique file name for the output MP3 file
    save_file_path = f"improved_speech.mp3"

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")

    # Return the path of the saved audio file
    return save_file_path


if __name__ == '__main__':
    voice_id = add_voice_clone('Record.mp3', name='Igor_2')
    print(voice_id)

    text = 'Presentation text improved by your public speaking coach'
    improved_path = text_to_speech(text, voice_id=voice_id)

    print(improved_path)
