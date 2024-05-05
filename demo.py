from autobahn.twisted.component import Component, run
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.util import sleep
import librosa
import os.path
import numpy as np
import random


@inlineCallbacks
def main(session, details):
    info = yield session.call("rom.sensor.hearing.info")
    # setting of standard language to English
    yield session.call("rie.dialogue.config.language", lang="en")

    # look at the user
    yield session.call("rie.vision.face.find")
    # smart starting question and keyword answers
    question = "Hi, I will teach you some musical notes, are you ready?"
    answers = {"Yes": ["yes", "jes", "yus", "ja"], "No": ["no", "nee", "nay"]}

    answer = yield session.call("rie.dialogue.ask",
                                question=question,
                                answers=answers)
    if answer == "Yes":
        # Message preceding the note showcase
        yield session.call("rie.dialogue.say",
                           text="All right, let me play all the notes for you to start with")
        showcase_notes(session)  # Note showcase (duh)
        correct_answers = main_loop(session)  # enters main game loop

        # Give the option to the user to play again:
        question = "You scored: " + str(correct_answers) + ", would you like to play again?"
        answers = {"Yes": ["yes", "jes", "yus", "ja"], "No": ["no", "nee", "nay"]}

        if correct_answers > 1:
            yield session.call("rom.optional.behavior.play", name="BlocklyDab")
        else:
            yield session.call("rom.optional.behavior.play", name="BlocklyShrug")
        answer = yield session.call("rie.dialogue.ask",
                                    question=question,
                                    answers=answers)
        if answer == "Yes":
            main_loop(session)  # run the main loop another 5 times
        elif answer == "No":
            yield session.call("rie.dialogue.say",
                           text="Oh, well maybe some other time.")
        else:
            yield session.call("rie.dialogue.say",
                           text="Sorry, but I didn't hear you properly.")

    elif answer == "No":
        yield session.call("rie.dialogue.say",
                           text="Oh, well maybe some other time.")
    else:
        yield session.call("rie.dialogue.say",
                           text="Sorry, but I didn't hear you properly.")

    session.leave()  # Close the connection with the robot


def main_loop(session):
    """ Main loop of our game, the robot announces that he will play a note,
        the player is supposed to then say out loud the note that he or she thinks was played.
        Only takes the current session as argument but needs the right .wav files in the Audio directory"""

    correct_answers = 0
    for i in range(5):
        # Now I will play a random note
        yield session.call("rie.dialogue.say", text="Now, let me play one of the notes, "
                                                    "please tell me what note you think it is")
        # generating random note
        random_note = random.randint(0, 5) + 65
        # Playing of random note
        if os.path.exists(os.path.abspath("Audio\\" + chr(random_note) + ".wav")):
            y, sr = librosa.load("Audio\\" + chr(random_note) + ".wav")
            yield session.call("rom.actuator.audio.play", data=y, rate=sr, sync=True)

        # Please tell me what note it is and listen for response, second smart question and keyword answers
        question = "Could you please tell me what Note I just played?"
        answers = {"A": ["A", "AA"], "B": ["B", "Bee"], "C": ["C", "see"],
                   "D": ["D", "Dee"], "E": ["E", "EE"], "F": ["F", "ehF"]}

        answer = yield session.call("rie.dialogue.ask",
                                    question=question,
                                    answers=answers)
        # Is this note correct?
        if answer == "A" and random_note == int('A'):
            correct_answer(session)
            correct_answers += 1
        elif answer == "B" and random_note == int('B'):
            correct_answer(session)
            correct_answers += 1
        elif answer == "C" and random_note == int('C'):
            correct_answer(session)
            correct_answers += 1
        elif answer == "D" and random_note == int('D'):
            correct_answer(session)
            correct_answers += 1
        elif answer == "E" and random_note == int('E'):
            correct_answer(session)
            correct_answers += 1
        elif answer == "F" and random_note == int('F'):
            correct_answer(session)
            correct_answers += 1

        else:
            # play a "negative" sound
            if os.path.exists(os.path.abspath("Audio\\negative.mp3")):
                y, sr = librosa.load("Audio\\" + chr(random_note) + ".wav")
                yield session.call("rom.actuator.audio.play", data=y, rate=sr, sync=True)

            # tell the user he/she sadly got it wrong
            yield session.call("rie.dialogue.say",
                               text="Sorry, but I don't think that was the answer."
                                    "I played the: " + chr(random_note) + "note")
    return correct_answers


def correct_answer(session):
    """ The goal of this function is to avoid code duplication,
        it is called anytime the user guesses the right note within the main game loop.
        The robot will congratulate the user with the correct answer and do a little robot dance"""
    # play a "negative" sound
    if os.path.exists(os.path.abspath("Audio\\positive.mp3")):
        y, sr = librosa.load("Audio\\" + chr(random_note) + ".wav")
        yield session.call("rom.actuator.audio.play", data=y, rate=sr, sync=False)
    yield session.call("rie.dialogue.say", text="Good you guessed the note! You get one point.")
    yield session.call("rom.optional.behavior.play", name="BlocklyRobotDance")


def showcase_notes(session):
    """ A small little function that just iterates through the audio files we have,
        The notes are then played by the robot one by one."""

    for i in range(6):
        # the 65th character in ASCII is 'A'
        note = 65 + i
        if os.path.exists(os.path.abspath("Audio\\" + chr(note) + ".wav")):
            y, sr = librosa.load("Audio\\" + chr(note) + ".wav")
            yield session.call("rom.actuator.audio.play", data=y, rate=sr, sync=True)


wamp = Component(
    transports=[{
        "url": "ws://wamp.robotsindeklas.nl",
        "serializers": ["msgpack"],
        "max_retries": 2
    }],
    realm="rie.<IP>",
)

wamp.on_join(main)

if __name__ == "__main__":
    run([wamp])
