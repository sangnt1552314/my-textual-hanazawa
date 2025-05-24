import os
import subprocess
import threading
from abc import ABC, abstractmethod


class AudioPlayer(ABC):
    @abstractmethod
    def play_stream_url(self, url: str) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


class VLCPlayer(AudioPlayer):
    def __init__(self):
        self.player = None
        self.instance = None
        try:
            import vlc
            import platform
            if platform.system() == 'Windows':
                os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')
            self.is_available = True
        except (ImportError, FileNotFoundError):
            self.is_available = False

    def play_stream_url(self, url: str) -> None:
        if not self.is_available:
            raise RuntimeError("VLC is not available. Cannot play audio.")

        if self.player is not None:
            self.player.stop()
            self.player.release()
        if self.instance is not None:
            self.instance.release()

        import vlc
        self.instance = vlc.Instance(['--no-video', '--quiet'])
        self.player = self.instance.media_player_new()
        media = self.instance.media_new(url)
        self.player.set_media(media)
        self.player.play()

    def stop(self) -> None:
        if self.player:
            self.player.stop()
            self.player.release()
            self.player = None
    
    def pause(self) -> None:
        if self.player:
            self.player.pause()


class WindowsMediaPlayer(AudioPlayer):
    def __init__(self):
        self.player_process = None
        self.player_thread = None
        self.wmp_path = r'C:\Program Files (x86)\Windows Media Player\wmplayer.exe'
        self.is_available = os.path.exists(self.wmp_path)
        import atexit
        atexit.register(self._cleanup)

    def _cleanup(self):
        """Ensure process is terminated when program exits"""
        try:
            if self.player_process:
                self.stop()
        except:
            # Ensure no exceptions during shutdown
            if self.player_process:
                try:
                    self.player_process.kill()
                except:
                    pass

    def _play_in_thread(self, url: str) -> None:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.player_process = subprocess.Popen(
            [self.wmp_path, '/play', '/close', url],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        self.player_process.wait()

    def play_stream_url(self, url: str) -> None:
        if not self.is_available:
            raise RuntimeError("Windows Media Player is not available. Cannot play audio.")

        # Stop any existing playback
        if self.player_process:
            self.stop()

        # Start new playback in a separate thread
        self.player_thread = threading.Thread(
            target=self._play_in_thread,
            args=[url]
        )
        # Thread will be terminated when main program exits
        self.player_thread.daemon = True
        self.player_thread.start()

    def stop(self) -> None:
        if self.player_process:
            # Try graceful termination first
            self.player_process.terminate()
            try:
                self.player_process.wait(timeout=2)  # Wait up to 2 seconds
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination fails
                self.player_process.kill()

            self.player_process = None
            self.player_thread = None
        else:
            raise RuntimeError("No player is currently playing.")
        
    def pause(self) -> None:
        """Windows Media Player does not support pause via command line, so this is a no-op."""
        if self.player_process:
            # No direct way to pause WMP from command line
            pass
        else:
            raise RuntimeError("No player is currently playing.")


class BasePlayer:
    def __init__(self):
        self.players = []
        self.current_player = None
        self.is_playing = False

        vlc_player = VLCPlayer()
        if vlc_player.is_available:
            self.players.append(vlc_player)

        wmp_player = WindowsMediaPlayer()
        if wmp_player.is_available:
            self.players.append(wmp_player)

        self.is_available = len(self.players) > 0

    def play_stream_url(self, url: str) -> None:
        """Play station in background using first available player."""
        if not self.is_available:
            raise RuntimeError("No audio players available. Install VLC or pygame.")

        if self.current_player:
            self.current_player.stop()

        for player in self.players:
            try:
                player.play_stream_url(url)
                self.current_player = player
                self.is_playing = True
                return
            except Exception as e:
                continue

        raise RuntimeError("All available players failed to play the stream")

    def stop(self) -> None:
        """Stop the current player."""
        self.is_playing = False

        if self.current_player:
            self.current_player.stop()
            self.current_player = None
        else:
            raise RuntimeError("No player is currently playing.")
        
    def pause(self) -> None:
        """Pause the current player."""
        if self.current_player:
            self.current_player.pause()
        else:
            raise RuntimeError("No player is currently playing.")


class ShoutcastRadioPlayer(BasePlayer):
    def __init__(self):
        super().__init__()


class YoutubeAudioPlayer(BasePlayer):
    def __init__(self):
        super().__init__()