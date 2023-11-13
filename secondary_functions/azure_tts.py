import azure.cognitiveservices.speech as speechsdk
import discord
import pathlib
from icecream import ic
import random
import asyncio
import classes as c

base_path = pathlib.Path(__file__).parent.parent.resolve()
temp_path = base_path / "data_holder/speech_key.txt"

with open(temp_path, "r") as f:
    _lines_ = f.readlines()

speech_key = _lines_[0].strip()
# noinspection SpellCheckingInspection
speech_region = "northeurope"


async def azure_tts(message: discord.Message, voice_client: discord.VoiceClient, person: c.Person = None):
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription = speech_key, region = speech_region)
    filename = f"tts{random.randint(1000, 9999)}.wav"
    audio_config = speechsdk.audio.AudioOutputConfig(filename = str(base_path / "secondary_functions/voice_temp" / filename))

    # The language of the voice that speaks.
    if person:
        speech_config.speech_synthesis_voice_name = f"en-US-{person.tts_perms}Neural"
    else:
        speech_config.speech_synthesis_voice_name = f"en-US-GuyNeural"

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config = speech_config, audio_config = audio_config)

    # Get text from the console and synthesize to the default speaker.

    text = str(message.clean_content)

    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    voice_client.play(discord.FFmpegPCMAudio(
        executable = str(base_path / "secondary_functions/ffmpeg/bin/ffmpeg.exe"),
        source = str(base_path / "secondary_functions/voice_temp" / filename)
    ))

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        ic(f"Speech synthesized for text [{text}]")
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        ic(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                ic(f"Error details: {cancellation_details.error_details}")
                ic("Did you set the speech resource key and region values?")


pass
