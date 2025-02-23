# Speech Coach // ElevenLabs x 16z Worldwide Hackathon
## The goal
The goal of this app is to help people practice their speech and presentation skills by introducing AI Agent that provides feedback according to pre-defined settings.

The app gathers a sample of your speech, refines it, and reads it in your own voice. 

## Env creation
In order to run the app please provide your own API keys to ElevenLabs and FAL modules in ```.env``` 
and run
```source activate_env.sh```
. The environment was built on Ubuntu.

## App
Execute
```streamlit run app.py```
and proceed with the in-app instructions. 
The app requires you to:
- choose the context of the speech out of the predefined tone and audience types
- upload a PDF file to help you perform the speech - it is not used in any other way than just for display.
- upload a speech sample that is gathered in-app

The app offers:
-  text feedback based on the desired characteristics that were specified on the first page
- a voice sample of refined speech in user's own voice.

## Future work 
Features that will be added in the future:
- Expand on the current pool of customizable settings
- Analysis of pronunciation of the speech
- Analysis of the content of the PDF slides and whether they fit the speech
- Ability to have a conversation with the agents that will further refine the output speech
- Multiple language support
- Analysis of body language from a video
