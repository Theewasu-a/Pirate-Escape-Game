"""
sounds.py - Procedural pirate-themed sound effects for Pirate Escape.
All sounds synthesized with numpy — no copyrighted audio.
"""
import math
import pygame

try:
    import numpy as np
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False


SAMPLE_RATE = 22050


def _to_stereo_sound(mono: "np.ndarray") -> pygame.mixer.Sound:
    mono = np.clip(mono, -1.0, 1.0)
    mono_i16 = (mono * 28000).astype(np.int16)
    stereo = np.column_stack((mono_i16, mono_i16))
    return pygame.sndarray.make_sound(stereo)


def _env_adsr(length: int, attack=0.01, release=0.1) -> "np.ndarray":
    env = np.ones(length, dtype=np.float32)
    a = max(1, int(attack * SAMPLE_RATE))
    r = max(1, int(release * SAMPLE_RATE))
    env[:a] = np.linspace(0, 1, a)
    if r < length:
        env[-r:] = np.linspace(1, 0, r)
    return env


def make_coin_sound() -> pygame.mixer.Sound:
    """Short two-note 'ding!' for coin pickup."""
    dur = 0.18
    n = int(dur * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    # Two quick tones: ring-mod-ish chime
    wave = 0.35 * np.sin(2*math.pi*880*t) + 0.25 * np.sin(2*math.pi*1320*t)
    # quick decay
    decay = np.exp(-t * 12)
    return _to_stereo_sound(wave * decay * 0.9)


def make_crash_sound() -> pygame.mixer.Sound:
    """Low wooden thud + splash for rock collision."""
    dur = 0.5
    n = int(dur * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    # Low frequency drop (wood thud)
    freq = 120 * np.exp(-t * 6) + 40
    phase = 2*math.pi*np.cumsum(freq)/SAMPLE_RATE
    thud = np.sin(phase) * np.exp(-t * 5) * 0.9
    # Noise splash
    noise = np.random.uniform(-1, 1, n) * np.exp(-t * 10) * 0.3
    return _to_stereo_sound((thud + noise) * 0.8)


def make_shield_break_sound() -> pygame.mixer.Sound:
    """Glass shatter-style sound for shield break."""
    dur = 0.55
    n = int(dur * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    # High frequency crackle
    out = np.zeros(n, dtype=np.float32)
    for f in (1800, 2400, 3200, 4200, 5600):
        out += np.sin(2*math.pi*f*t) * 0.12 * np.exp(-t * (6 + f/1000))
    # Shimmer noise
    noise = np.random.uniform(-1, 1, n) * np.exp(-t * 4) * 0.35
    out += noise
    out *= _env_adsr(n, attack=0.002, release=0.3)
    return _to_stereo_sound(out)


def make_powerup_sound() -> pygame.mixer.Sound:
    """Ascending chime for powerup pickup."""
    notes = [523.25, 659.25, 783.99, 1046.50]  # C5 E5 G5 C6
    dur = 0.28
    n_per = int(dur / len(notes) * SAMPLE_RATE)
    total_n = n_per * len(notes)
    out = np.zeros(total_n, dtype=np.float32)
    for i, f in enumerate(notes):
        t = np.arange(n_per) / SAMPLE_RATE
        seg = 0.45 * np.sin(2*math.pi*f*t) * np.exp(-t * 6)
        out[i*n_per:(i+1)*n_per] = seg
    return _to_stereo_sound(out * 0.9)


def make_police_sound() -> pygame.mixer.Sound:
    """Police siren warble (short)."""
    dur = 0.8
    n = int(dur * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    # Two-tone siren
    freq = 700 + 200 * np.sin(2*math.pi*4*t)
    phase = 2*math.pi*np.cumsum(freq)/SAMPLE_RATE
    out = 0.5 * np.sin(phase) * _env_adsr(n, attack=0.02, release=0.2)
    return _to_stereo_sound(out * 0.7)


def make_wave_ambient() -> pygame.mixer.Sound:
    """Soft looping ocean-wave ambient."""
    dur = 4.0
    n = int(dur * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    # Filtered noise with slow amplitude modulation
    noise = np.random.uniform(-1, 1, n)
    # Simple low-pass: running average
    kernel = 40
    smooth = np.convolve(noise, np.ones(kernel)/kernel, mode='same')
    mod = 0.5 + 0.5 * np.sin(2*math.pi*0.2*t)
    out = smooth * mod * 0.25
    return _to_stereo_sound(out)


class SoundBank:
    """
    Container for all game SFX.  Gracefully no-ops if numpy/mixer unavailable.
    """
    def __init__(self):
        self.enabled = False
        self.coin = self.crash = self.shield_break = None
        self.powerup = self.police = self.wave = None
        if not _HAS_NUMPY:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            self.coin         = make_coin_sound()
            self.crash        = make_crash_sound()
            self.shield_break = make_shield_break_sound()
            self.powerup      = make_powerup_sound()
            self.police       = make_police_sound()
            self.wave         = make_wave_ambient()
            # Reasonable volumes
            self.coin.set_volume(0.35)
            self.crash.set_volume(0.6)
            self.shield_break.set_volume(0.55)
            self.powerup.set_volume(0.45)
            self.police.set_volume(0.5)
            self.wave.set_volume(0.25)
            self.enabled = True
        except Exception:
            self.enabled = False

    def play(self, name: str):
        if not self.enabled:
            return
        snd = getattr(self, name, None)
        if snd is not None:
            try:
                snd.play()
            except Exception:
                pass

    _wave_channel = None
    def start_ambient(self):
        if self.enabled and self.wave is not None and self._wave_channel is None:
            try:
                self._wave_channel = self.wave.play(loops=-1)
            except Exception:
                pass

    def stop_ambient(self):
        if self._wave_channel is not None:
            try:
                self._wave_channel.stop()
            except Exception:
                pass
            self._wave_channel = None
