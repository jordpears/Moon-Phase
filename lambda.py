import time
import urllib.request, json
import datetime



# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'SSML': '<speak>' + str(output) + '</speak>'
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': "Please ask me about when the next full or new moon is or ask me what is the phase of the current moon."
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'SSML',
                'SSML': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Moon Phase Alexa skill. " \
                    "Please ask me when the next moon is by saying, " \
                    "When is the next full moon or when is the next new moon."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please ask me when the next moon is by saying, " \
                    "When is the next full moon or when is the next new moon."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Moon Phase Alexa skill. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def stripmoon(moontype):
    if moontype in ['full','maximim','total','whole','bright']:
        return "full"
    if moontype in ['new','minimum','no','zero','dead']:
        return "new"
    else:
        return False

def currentPhase(intent):
    with urllib.request.urlopen("http://api.burningsoul.in/moon/"+str(time.time())) as url:
        phase = json.loads(url.read().decode())["stage"]
    speech_output = "The current moon phase is " + phase + "."
    should_end_session = True
    reprompt_text = None
    card_title = "Moon Phase"
    session_attributes = {}
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def nextPhase(intent):
    if 'moonPhase' in intent['slots']:
        if 'value' in intent['slots']['moonPhase'] and stripmoon(intent['slots']['moonPhase']['value']) != False:
            moontype = stripmoon(intent['slots']['moonPhase']['value'])
            with urllib.request.urlopen("http://api.burningsoul.in/moon/"+str(time.time())) as url:
                data = json.loads(url.read().decode())

            if moontype == "full":
                outputtalk = datetime.datetime.fromtimestamp(data["FM"]["UT"]).strftime('????'+'%m%d')
            if moontype == "new":
                outputtalk = datetime.datetime.fromtimestamp(data["NNM"]["UT"]).strftime('????'+'%m%d')


            speech_output = "The next "+moontype+" moon is on <say-as interpret-as=\"date\">" + outputtalk + "</say-as>."
            should_end_session = True
            reprompt_text = None
        else:
            speech_output = "I didn't understand your request. " + \
                            "Please try again."
            reprompt_text = "I didn't understand your request. " + \
                            "Please ask me when the next moon is by saying, " \
                            "When is the next full moon or when is the next new moon."
            should_end_session = False
    else:
        speech_output = "You didn't give me a moon phase. " + \
                        "Please try again."
        reprompt_text = "I didn't understand your request. " + \
                        "Please ask me when the next moon is by saying, " \
                        "When is the next full moon or when is the next new moon."
        should_end_session = False

    card_title = "Moon Phase"
    session_attributes = {}
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "currentPhase":
        return currentPhase(intent)
    if intent_name == "nextPhaseIntent":
        return nextPhase(intent)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.056bf519-1100-4703-a623-3e5618e79d82"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
