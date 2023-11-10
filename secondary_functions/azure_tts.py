import azure.cognitiveservices.speech as speechsdk
import discord
import utils.tools as t
import pathlib
from icecream import ic
import random
import asyncio
from os import close

base_path = pathlib.Path(__file__).parent.parent.resolve()
temp_path = base_path / "data_holder/speech_key.txt"

with open(temp_path, "r") as f:
    _lines_ = f.readlines()

speech_key = _lines_[0].strip()
# noinspection SpellCheckingInspection
speech_region = "northeurope"


def message_cutter():
    pass


async def azure_tts(message: discord.Message, voice_client: discord.VoiceClient):
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription = speech_key, region = speech_region)
    filename = f"tts{random.randint(1000, 9999)}.wav"
    audio_config = speechsdk.audio.AudioOutputConfig(filename = str(base_path / "secondary_functions" / filename))

    # The language of the voice that speaks.
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config = speech_config, audio_config = audio_config)

    # Get text from the console and synthesize to the default speaker.

    text = str(message.clean_content)

    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    voice_client.play(discord.FFmpegPCMAudio(
        executable = str(base_path / "secondary_functions" / "ffmpeg/bin/ffmpeg.exe"),
        source = str(base_path / "secondary_functions" / filename)
    ))

    while voice_client.is_playing():
        await asyncio.sleep(1)
    pathlib.Path.unlink(base_path / "secondary_functions" / filename)

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