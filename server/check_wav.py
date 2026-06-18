import sys
try:
    from pydub import AudioSegment
    audio = AudioSegment.from_file('Y:/PrintBot/server/voice_library/84c480612f4c4838bc7c962fe5aaa3a0_Sebastien.wav')
    print(f'Duration: {len(audio)}ms')
    print(f'Channels: {audio.channels}')
    print(f'FrameRate: {audio.frame_rate}')
except Exception as e:
    print(f'Error: {e}')
