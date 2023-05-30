import streamlit as st
import speech_recognition as sr
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
import openai
import time
import sounddevice as sd
import soundfile as sf
import tempfile


# Set up your OpenAI API credentials
openai.api_key = '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'

# Create a recognizer object
r = sr.Recognizer()

# Function to transcribe audio from microphone
# def transcribe_audio():
#     # Use the default system microphone as the audio source
#     with sr.Microphone() as source:
#         st.write("Listening...")

#         # Adjust ambient noise for better recognition (if needed)
#         r.adjust_for_ambient_noise(source)

#         # Listen for audio input
#         audio = r.listen(source)

#         st.write("Transcribing...")

#         try:
#             # Transcribe the audio using the Google Web Speech API
#             text = r.recognize_google(audio)
#             return text
#         except sr.UnknownValueError:
#             st.write("Could not understand audio")
#         except sr.RequestError as e:
#             st.write("Error: {0}".format(e))

def transcribe_audio():
    fs = 44100  # Sample rate
    seconds = 10  # Duration of recording
    # Start recording
    recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    st.write('Listening .........')
    sd.wait()  # Wait until recording is finished
    # Save the recording to a file or process it as per your requirements
    # For this example, we'll just display the recorded audio as a waveform
    st.write("Recording finished!")
    # st.write("Recorded audio waveform:")
    # st.line_chart(recording)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        audio_file = tmpfile.name
        sf.write(tmpfile.name, recording, fs)
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
    return text

def generate_quiz(response,num_questions):
    # Set up your OpenAI API credentials
    prompt = f"Create a quiz contains {num_questions} questions quiz about {response} using this format , this structure = [ ['Question (i)', 'Option 1', 'Option 2', 'Option 3', 'Option 4', 'Correct Answer'],['Question (i+1)', 'Option 1', 'Option 2', 'Option 3', 'Option 4', 'Correct Answer'],......['last question','option 1','option 2','option 3','Correct Answer']] in one line:\n"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.7,
        max_tokens=500,
        n=1,  # Number of questions to generate
        stop=None,
        frequency_penalty=0.5,
        presence_penalty=0.0
         )
    questions = response.choices
    # Format the generated questions
    quiz = ""
    for i, question in enumerate(questions):
        if 'text' in question:
            quiz += f"{question['text'].strip()}\n"
    return quiz





def home_page():
    st.title("Auto Quiz Generator - Home")
    st.markdown("<div class='decorative-line'></div>", unsafe_allow_html=True)
    st.write("Welcome to the Auto Quiz Generator!")
    st.write("This application allows you to transcribe audio and generate quizzes based on the transcription.")
    st.write("To get started, click on the 'Auto Quiz' page from the sidebar.")

# Create the Streamlit app
def auto_quiz_page():
    # Add custom CSS styling
    st.markdown(
        """
        <style>
        .header-text {
            color: #3366FF;
            font-size: 32px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 24px;
        }

        .decorative-line {
            height: 2px;
            background-color: #CCCCCC;
            margin: 24px 0;
        }

        .generated-quiz {
            background-color: #F5F5F5;
            border-radius: 8px;
            padding: 16px;
            margin-top: 24px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Add a header
    st.markdown("<h1 class='header-text'>Auto Quiz Generator</h1>", unsafe_allow_html=True)
    st.markdown("<div class='decorative-line'></div>", unsafe_allow_html=True)
    # Add a decorative separator
    #st.markdown("<div class='decorative-line'></div>", unsafe_allow_html=True)
    # Add a box for inputting integer values
    num_questions = st.number_input("Number of Questions", min_value=1, max_value=10, value=5, step=1)
    start_recording = st.button("Start Recording")
    record_again = False
    if start_recording :
        # Record audio and transcribe it
        response = transcribe_audio()
        st.write("Transcription:")
        st.write(response)
        # User validation step
        st.write("Please verify if the transcription is correct.")
        st.write("If it is not correct, click the button to Record Again.")
        st.write("If it is correct, just wait...")
        st.markdown("---")
        record_again = st.button("Record Again")
        if record_again:
            # Call the main function recursively to restart the process
            auto_quiz_page()
        # Generate the quiz based on the transcription
        generated_quiz = generate_quiz(response=response,num_questions=num_questions)
        st.write(f"A Quiz with {num_questions} questions about {response} will be generated")
        # Print the generated quiz
        #st.write("Generated Quiz:")
        #st.write(generated_quiz)
        quiz_list = eval(generated_quiz)
        # Render the quiz using Streamlit form components
        st.header("Quiz")
        st.subheader(f"Topic: {response}")

        # Display each question with options
        for question in quiz_list:
            st.write(question[0])  # Display the question
            options = question[1:4]  # Get the options
            st.write("Options:")
            for option in options:
                st.write(f"- {option}")  # Display each option on a new line
            st.write("")  # Add an empty line between questions

        # Add a decorative separator
        st.markdown("---")

        SCOPES = "https://www.googleapis.com/auth/forms.body"
        DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
        store = file.Storage('token.json')
        creds = None
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('C://Users/user/Desktop/Data__Mining/deep_p/credentials.json', SCOPES)
            creds = tools.run_flow(flow, store)

        form_service = discovery.build('forms', 'v1', http=creds.authorize(Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)
                
        # Request body for creating a form
        NEW_FORM = {
                    "info": {
                        "title": f"Auto form about {response}",
                    }
                }

        # Creates the initial form
        result = form_service.forms().create(body=NEW_FORM).execute()

        # Adds the question to the form
        quiz_questions = []
        i = 0
        for quiz_item in quiz_list:
            question = {
                        "createItem": {
                            "item": {
                                "title": quiz_item[0],
                                "questionItem": {
                                    "question": {
                                        "required": True,
                                        "choiceQuestion": {
                                            "type": "RADIO",
                                            "options": [
                                                {"value": quiz_item[1]},
                                                {"value": quiz_item[2]},
                                                {"value": quiz_item[3]}
                                            ],
                                            "shuffle": True
                                        }
                                    }
                                },
                            },
                            "location": {
                                "index": i
                            }
                        }
                    }
            i = i + 1
            quiz_questions.append(question)
        questions = {"requests": quiz_questions}
        question_setting = form_service.forms().batchUpdate(formId=result["formId"], body=questions).execute()
        form_id = result['formId']
        form_url = f"https://docs.google.com/forms/d/{form_id}/viewform"
        st.write("Form URL:", form_url)
        # Print the result to show the question has been added
        get_result = form_service.forms().get(formId=result["formId"]).execute()
        #print(get_result)  # Uncomment this line if you want to see the result


# Create the Streamlit app
def main():
    # Set page title and favicon
    #st.set_page_config(page_title="Auto Quiz Generator", page_icon=":pencil2:")
    # Add custom CSS styling
    st.markdown(
        """
        <style>
        .header-text {
            color: #3366FF;
            font-size: 32px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 24px;
        }

        .decorative-line {
            height: 2px;
            background-color: #CCCCCC;
            margin: 24px 0;
        }

        .generated-quiz {
            background-color: #F5F5F5;
            border-radius: 8px;
            padding: 16px;
            margin-top: 24px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Add a header
    #st.markdown("<h1 class='header-text'>Auto Quiz Generator</h1>", unsafe_allow_html=True)

    # Add a decorative separator
    #st.markdown("<div class='decorative-line'></div>", unsafe_allow_html=True)

    # Create a sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ("Home", "Auto Quiz"))
    if page == "Home":
        home_page()
    elif page == "Auto Quiz":
        auto_quiz_page()
    # Render pages based on the selected option
# Run the app
if __name__ == "__main__":
    main()