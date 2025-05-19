import os
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

class ShoutcastRadioPlayer:
    def __init__(self):
        self.players = []
        self.current_player = None
        
        # Try to initialize VLC player
        vlc_player = VLCPlayer()
        if vlc_player.is_available:
            self.players.append(vlc_player)
            
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
                return
            except Exception as e:
                continue
                
        raise RuntimeError("All available players failed to play the stream")
    
    def stop(self) -> None:
        """Stop the current player."""
        if self.current_player:
            self.current_player.stop()
            self.current_player = None
        else:
            raise RuntimeError("No player is currently playing.")