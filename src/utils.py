import datetime
import json
import os
import random
import sys
from typing import AnyStr, Optional

import numpy as np
import pygame

from src.constants import DEBUG

# ---------------------------------------------------------------------------
# Persistent Tk root — clipboard ownership on X11 is tied to the owning
# window; creating and immediately destroying a Tk() drops the clipboard
# before anything can paste it.  One long-lived hidden root avoids this.
# ---------------------------------------------------------------------------
_persistent_tk_root = None


def _get_persistent_tk_root():
    """Return a single hidden Tk root, created once and kept alive."""
    global _persistent_tk_root
    if _persistent_tk_root is None:
        import tkinter as tk
        _persistent_tk_root = tk.Tk()
        _persistent_tk_root.withdraw()
    return _persistent_tk_root

# --- Global Audio State ---
MASTER_VOLUME = 0.5
IS_MUTED = False

# Global SFX & Music Variables
button_hover_sound = None
button_click_sound = None
dungeon_theme_sound = None
dungeon_theme_channel = None


def get_assets_path() -> AnyStr:
    """Returns the absolute path to the assets folder, handling PyInstaller and Dev environments."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets")

    # DEV: Path based on the main file module
    try:
        main_file = sys.modules["__main__"].__file__
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(main_file)))
    except (KeyError, AttributeError):
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

    return os.path.join(project_root, "assets")


def get_current_volume():
    """Helper to dynamically fetch the exact volume from JSON right now."""
    try:
        opts_path = os.path.join(os.path.dirname(__file__), "options.json")
        with open(opts_path, "r") as f:
            opts = json.load(f)
        if opts.get("is_muted", False):
            return 0.0
        return opts.get("master_volume", 0.5)
    except Exception:
        return 0.5  # Safe fallback


def load_sfx():
    global button_hover_sound, button_click_sound
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    sfx_path = os.path.join(get_assets_path(), "sfx")
    try:
        button_hover_sound = pygame.mixer.Sound(
            os.path.join(sfx_path, "button_hover.mp3")
        )
        button_click_sound = pygame.mixer.Sound(
            os.path.join(sfx_path, "button_click.mp3")
        )
        print("[Audio] SFX loaded successfully")
    except Exception as e:
        print(f"[Audio] SFX loading warning: {e}")

    apply_global_volume()


def apply_global_volume(vol_override=None):
    """Applies volume to Pygame mixer, cached Sound objects, and active channels."""
    if not pygame.mixer.get_init():
        return

    vol = vol_override if vol_override is not None else get_current_volume()
    pygame.mixer.music.set_volume(vol)

    if button_hover_sound:
        button_hover_sound.set_volume(vol)
    if button_click_sound:
        button_click_sound.set_volume(vol)
    if dungeon_theme_channel:
        dungeon_theme_channel.set_volume(vol)


def apply_volume():
    """Reads settings from options.json and triggers apply_global_volume."""
    apply_global_volume()


# --- Sound Triggers & SFX ---

def play_button_hover():
    if button_hover_sound:
        button_hover_sound.play()


def play_button_click():
    if button_click_sound:
        button_click_sound.play()


# --- Procedural Sounds & Music Pipeline ---

def play_retro_woosh():
    vol = get_current_volume()
    if vol <= 0.0 or not pygame.mixer.get_init():
        return

    duration = 0.3
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    freq = np.linspace(800, 200, len(t))

    wave = 0.5 * vol * np.sin(2 * np.pi * freq * t)
    audio_data = np.int16(wave * 32767)
    stereo_data = np.column_stack((audio_data, audio_data))

    try:
        sound = pygame.sndarray.make_sound(stereo_data)
        sound.set_volume(vol)
        sound.play()
    except Exception:
        pass


def typewriter_sound():
    vol = get_current_volume()
    if vol <= 0.0 or not pygame.mixer.get_init():
        return

    sample_rate = 44100
    duration = 0.02
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    wave = np.random.uniform(-1, 1, len(t)) * 0.1 * vol
    audio_data = np.int16(wave * 32767)
    stereo_data = np.column_stack((audio_data, audio_data))

    try:
        sound = pygame.sndarray.make_sound(stereo_data)
        sound.set_volume(vol)
        sound.play()
    except Exception:
        pass


def _synth_female_ohh_stab(n_samples, sample_rate, note_freq=523.25, attack=0.015, decay=0.30, release=0.40):
    """Synthesizes a retro Game Boy-style feminine 'Ohh' vocal stab:
    Fast attack, pitch scoop, 'Ohh' formant harmonic weighting, and breath tremolo."""
    t = np.arange(n_samples) / sample_rate

    # Natural vocal pitch scoop (inflection) + pitch vibrato
    scoop = np.exp(-t * 50) * -0.04  # Slight upward pitch scoop at onset
    vibrato = 0.012 * np.sin(2 * np.pi * 6.0 * t)
    freq = note_freq * (1.0 + scoop + vibrato)
    phase = np.cumsum(freq) / sample_rate

    # 'Ohh' vowel formant distribution (concentrated low-mid harmonic resonance)
    ohh_formants = [(1, 1.00), (2, 0.80), (3, 0.25), (4, 0.45), (5, 0.15)]
    voice = np.zeros(n_samples)
    for harmonic, weight in ohh_formants:
        voice += weight * np.sin(2 * np.pi * phase * harmonic)
    voice /= sum(w for _, w in ohh_formants)

    # Subtle vocal breath modulation
    vocal_breath = 1.0 + 0.10 * np.sin(2 * np.pi * 4.5 * t)
    voice *= vocal_breath

    # Fast attack -> sustain -> smooth release envelope
    env = np.ones(n_samples)
    a_len = min(int(attack * sample_rate), n_samples)
    d_len = min(int(decay * sample_rate), n_samples - a_len)
    r_start = a_len + d_len
    r_len = max(n_samples - r_start, 0)

    if a_len > 0:
        env[:a_len] = np.linspace(0, 1, a_len) ** 0.5  # ~15ms fast attack
    if d_len > 0:
        env[a_len:a_len + d_len] = np.linspace(1, 0.75, d_len)
    if r_len > 0:
        env[r_start:] = np.linspace(0.75, 0, r_len)

    return voice * env


def generate_dungeon_synth_sound() -> pygame.mixer.Sound:
    """Fluid GameBoy-style dungeon theme:
    - Repeats 3 times.
    - Pass 1 & 2: Harmonica Lead + Bass.
    - Pass 3: Harmonica Lead + Retro Wheeled Organ Layer + Bass.
    - Ending: Feminine 'Ohh' Retro Vocal Stab on final tail.
    """
    speed = 1.5
    single_duration = 9.0 / speed
    sample_rate = 44100
    n_single = int(sample_rate * single_duration)

    raw_melody_notes = [
        (246.94, 0.0, 0.95),   # Si3 (B3)
        (220.00, 0.90, 0.95),  # Lá3 (A3)
        (246.94, 1.80, 0.95),  # Si3 (B3)
        (261.63, 2.70, 0.95),  # Dó4 (C4)
        (196.00, 3.60, 1.90),  # Sol3 (G3) - sustained
        (0.0,    5.50, 0.50),  # Rest
        (174.61, 6.00, 1.10),  # Fá3 (F3)
        (155.56, 7.00, 1.30),  # Mi♭3 (E♭3)
    ]
    melody_notes = [(freq, start / speed, dur / speed) for freq, start, dur in raw_melody_notes]

    # ---- 1. Build Single-Pass Frequency & Gate Tracks ----
    freq_track_1 = np.full(n_single, melody_notes[0][0] if melody_notes[0][0] > 0 else 220.0)
    gate_track_1 = np.ones(n_single)

    portamento_time = 0.045
    rest_fade = 0.06
    prev_freq = melody_notes[0][0] if melody_notes[0][0] > 0 else 220.0
    was_resting = False

    boundaries = [start for _, start, _ in melody_notes] + [single_duration]

    for i, (freq, start_time, _dur) in enumerate(melody_notes):
        s_idx = int(start_time * sample_rate)
        e_idx = min(int(boundaries[i + 1] * sample_rate), n_single)
        if e_idx <= s_idx:
            continue

        if freq == 0.0:
            fade_len = min(int(rest_fade * sample_rate), e_idx - s_idx)
            gate_track_1[s_idx:s_idx + fade_len] = np.linspace(1, 0, fade_len)
            gate_track_1[s_idx + fade_len:e_idx] = 0
            freq_track_1[s_idx:e_idx] = prev_freq
            was_resting = True
            continue

        glide_len = min(int(portamento_time * sample_rate), e_idx - s_idx)
        if glide_len > 0:
            freq_track_1[s_idx:s_idx + glide_len] = np.linspace(prev_freq, freq, glide_len)
        freq_track_1[s_idx + glide_len:e_idx] = freq

        if was_resting:
            fade_len = min(int(rest_fade * sample_rate), e_idx - s_idx)
            gate_track_1[s_idx:s_idx + fade_len] = np.linspace(0, 1, fade_len)
            was_resting = False

        prev_freq = freq

    # ---- 2. Repeat 3 Times with Seamless Continuous Phase ----
    freq_track = np.tile(freq_track_1, 3)
    gate_track = np.tile(gate_track_1, 3)
    n_samples = len(freq_track)

    t = np.arange(n_samples) / sample_rate
    freq_track_mod = freq_track * (1.0 + 0.006 * np.sin(2 * np.pi * 5.5 * t))
    breath_tremolo = 1.0 + 0.12 * np.sin(2 * np.pi * 5.0 * t)

    phase = np.cumsum(freq_track_mod) / sample_rate

    # ---- 3. Harmonica Lead Synthesis ----
    harmonica_wave = (
        1.00 * np.sin(2 * np.pi * phase) +
        0.70 * np.sin(2 * np.pi * phase * 2.0) +
        0.50 * np.sin(2 * np.pi * phase * 3.0) +
        0.30 * np.sin(2 * np.pi * phase * 4.0) +
        0.20 * np.sin(2 * np.pi * phase * 5.0)
    ) / 2.70

    lead_wave = harmonica_wave * breath_tremolo * gate_track

    # ---- 4. Retro Wheeled Organ Layer (Pass 3 Only) ----
    p3_start = 2 * n_single
    p3_end = 3 * n_single
    phase_p3 = phase[p3_start:p3_end]
    t_p3 = t[p3_start:p3_end]

    # Drawbar harmonics spectrum (8', 4', 2-2/3', 2', 1-1/3')
    wheeled_organ_p3 = (
        1.00 * np.sin(2 * np.pi * phase_p3) +
        0.80 * np.sin(2 * np.pi * phase_p3 * 2.0) +
        0.60 * np.sin(2 * np.pi * phase_p3 * 3.0) +
        0.40 * np.sin(2 * np.pi * phase_p3 * 4.0) +
        0.25 * np.sin(2 * np.pi * phase_p3 * 6.0)
    ) / 3.05

    # Rotary Leslie Speaker modulation (6Hz amplitude swirl)
    rotary_leslie = 1.0 + 0.18 * np.sin(2 * np.pi * 6.0 * t_p3)
    wheeled_organ_p3 *= rotary_leslie * gate_track[p3_start:p3_end]

    # Mix organ into lead track on the 3rd pass
    lead_wave[p3_start:p3_end] += wheeled_organ_p3 * 0.45

    # Buffer edge fade
    edge = np.ones(n_samples)
    edge_len = int(0.05 * sample_rate)
    edge[:edge_len] = np.linspace(0, 1, edge_len)
    edge[-edge_len:] = np.linspace(1, 0, edge_len)
    lead_wave *= edge

    # ---- 5. Deep Triangle Bassline (3 Repeats) ----
    bass_freqs = [82.41, 123.47, 110.00, 77.78]
    step_dur = 0.5 / speed
    n_steps = int(np.ceil((single_duration * 3) / step_dur))
    bass_freq_track = np.zeros(n_samples)
    prev_b = bass_freqs[0]
    bass_glide = int(0.02 * sample_rate)

    for i in range(n_steps):
        b_start = int(i * step_dur * sample_rate)
        b_end = min(int((i + 1) * step_dur * sample_rate), n_samples)
        if b_start >= n_samples:
            break
        bfreq = bass_freqs[i % len(bass_freqs)]
        glide_len = min(bass_glide, b_end - b_start)
        if glide_len > 0:
            bass_freq_track[b_start:b_start + glide_len] = np.linspace(prev_b, bfreq, glide_len)
        bass_freq_track[b_start + glide_len:b_end] = bfreq
        prev_b = bfreq

    bass_phase = np.cumsum(bass_freq_track) / sample_rate
    bass_wave = (2 * np.abs(2 * (bass_phase - np.floor(bass_phase + 0.5))) - 1) * 0.35

    mixed_signal = (lead_wave * 0.5) + (bass_wave * 0.3)

    # Cavern Echo / Delay
    delay_samples = int((0.28 / speed) * sample_rate)
    echo_signal = np.zeros(n_samples)
    if delay_samples < n_samples:
        echo_signal[delay_samples:] = mixed_signal[:-delay_samples] * 0.35
    final_signal = mixed_signal + echo_signal

    fade_len = int(0.1 * sample_rate)
    if fade_len < n_samples:
        final_signal[-fade_len:] *= np.linspace(1, 0, fade_len)

    # ---- 6. Feminine "Ohh" Retro Vocal Stab (Appears ONLY at end of 3rd pass) ----
    choir_dur = 0.85
    n_choir = int(sample_rate * choir_dur)
    ohh_wave = _synth_female_ohh_stab(n_choir, sample_rate, note_freq=523.25)  # Soprano C5 "Ohh"

    final_signal = np.concatenate([final_signal, np.zeros(n_choir)])
    final_signal[-n_choir:] += ohh_wave * 0.60  # Mix level

    # ---- 7. 8-bit Quantization (Bit-Crush) & Stereo Export ----
    final_signal = np.round(final_signal * 16) / 16
    final_signal = np.clip(final_signal, -1.0, 1.0) * 0.4

    audio_data = np.int16(final_signal * 32767)
    stereo_data = np.column_stack((audio_data, audio_data))
    return pygame.sndarray.make_sound(stereo_data)


def play_dungeon_synth_theme():
    """Triggers looping playback (-1) of the generated synth theme."""
    global dungeon_theme_sound, dungeon_theme_channel

    vol = get_current_volume()
    if not pygame.mixer.get_init():
        return

    if dungeon_theme_channel and dungeon_theme_channel.get_busy():
        dungeon_theme_channel.set_volume(vol)
        return

    if dungeon_theme_sound is None:
        try:
            dungeon_theme_sound = generate_dungeon_synth_sound()
        except Exception as e:
            print(f"[Audio] Error generating procedural theme: {e}")
            return

    try:
        dungeon_theme_channel = dungeon_theme_sound.play(loops=-1)
        if dungeon_theme_channel:
            dungeon_theme_channel.set_volume(vol)
    except Exception as e:
        print(f"[Audio] Failed to play dungeon synth theme: {e}")


def stop_dungeon_synth_theme():
    """Stops the main menu synth playback."""
    global dungeon_theme_channel
    if dungeon_theme_channel:
        dungeon_theme_channel.stop()
        dungeon_theme_channel = None


def log_to_session(text: str):
    """Appends adventure text to a daily session log file in backups/."""
    try:
        if not os.path.exists("backups"):
            os.makedirs("backups")

        filename = os.path.join(
            "backups", f"session_{datetime.date.today().strftime('%Y%m%d')}.txt"
        )
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")
    except Exception as e:
        print(f"[Logger] Error: {e}")


# ---------------------------------------------------------------------------
# Clipboard helpers — shared by TextInput, FixedMultilineInput, and
# SelectableOutputView so that platform-specific fallback logic lives in
# exactly one place.
# ---------------------------------------------------------------------------

def copy_to_clipboard(text: str) -> bool:
    """Copy *text* to the OS clipboard.

    Tries ``pygame.scrap`` first; falls back to a persistent Tk root so that
    clipboard ownership is not dropped immediately on X11/Linux (the old
    pattern of creating and destroying a fresh Tk() every call silently
    produced empty pastes on those platforms).

    Returns ``True`` on success, ``False`` on failure.
    """
    if not text:
        return False
    # --- pygame.scrap attempt ---
    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))
        return True
    except Exception:
        pass
    # --- Persistent Tk fallback ---
    try:
        root = _get_persistent_tk_root()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        return True
    except Exception:
        return False


def paste_from_clipboard() -> Optional[str]:
    """Return the current OS clipboard text, or ``None`` on failure.

    Mirrors the same two-stage strategy as :func:`copy_to_clipboard`.
    """
    # --- pygame.scrap attempt ---
    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        raw = pygame.scrap.get(pygame.SCRAP_TEXT)
        if raw is not None:
            return raw.decode("utf-8").strip("\x00")
    except Exception:
        pass
    # --- Persistent Tk fallback ---
    try:
        root = _get_persistent_tk_root()
        return root.clipboard_get()
    except Exception:
        return None


# --- Utility Graphics/System Helpers ---

def get_default_font(size: int) -> pygame.font.Font:
    return pygame.font.Font(os.path.join(get_assets_path(), "font.ttf"), size)


def get_image(image: AnyStr) -> pygame.Surface:
    return pygame.image.load(os.path.join(get_assets_path(), image))


def print_debug(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def get_center_x(screen: pygame.Surface, image_width: int) -> int:
    return (screen.get_width() - image_width) // 2


def get_mod(attrib: int) -> int:
    return (attrib - 10) // 2


def grid_position(
    index,
    start_x,
    start_y,
    item_width,
    item_height,
    columns,
    h_spacing=20,
    v_spacing=8,
):
    col = index % columns
    row = index // columns
    x = start_x + col * (item_width + h_spacing)
    y = start_y + row * (item_height + v_spacing)
    return x, y


if __name__ == "__main__":
    pygame.init()
    print(f"Asset Path: {get_assets_path()}")
    load_sfx()
    typewriter_sound()
    play_retro_woosh()