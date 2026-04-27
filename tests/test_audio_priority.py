import time
from modules.output.audio import AudioPlayer


def test_audio_player_enqueue_empty_no_crash():
    player = AudioPlayer()
    player.enqueue(b"")
    time.sleep(0.05)
    player.shutdown()

