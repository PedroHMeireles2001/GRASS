from typing import Tuple, Callable, Optional, List

import pygame

from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.UIElement import UIElement
from src.utils import get_default_font, typewriter_sound, copy_to_clipboard, paste_from_clipboard


class TextInput(UIElement):
    """Single-line (auto-growing height) text input with a full cursor+anchor
    editing state machine.

    Features
    --------
    * Cursor and anchor model: ``self.cursor`` is the insertion point;
      ``self.anchor`` is the other end of the selection.  When they are equal
      there is no active selection.
    * ``_replace_selection(text)`` is the single primitive for all insertions
      and deletions, keeping state consistent at all times.
    * Left / Right arrow navigation; Shift+arrow extends the selection.
    * Mouse click translates to the nearest character index via the same
      word-wrap mapping used for rendering.
    * Ctrl+A / Ctrl+C / Ctrl+V clipboard via the centralised utils helpers.
    * ``pygame.key.set_repeat`` is managed on focus gain/loss so held keys
      repeat smoothly.
    """

    def __init__(
        self,
        position: Tuple[int, int],
        width: int,
        height: int = 24,
        initial_text: str = "",
        background_color: Tuple[int, int, int] = (255, 255, 255),
        focus_background_color: Tuple[int, int, int] = (50, 100, 255),
        text_size: int = 12,
        text_color: Tuple[int, int, int] = (255, 255, 255),
        padding: int = 6,
        border_width: int = 1,
        label_str: str = None,
        label_top: bool = True,
        label_size: int = 24,
        on_change: Optional[Callable[[str], None]] = None,
        on_submit: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(None, position)
        self.width = width
        self.base_height = height
        self.padding = padding
        self.text_size = text_size
        self.text_color = text_color
        self.background_color = background_color
        self.focus_background_color = focus_background_color
        self.focus = False
        self.border_width = border_width
        self.font = get_default_font(text_size)
        self.text_str = initial_text
        self.rect = pygame.Rect(position[0], position[1], width, height)
        self.base_y = position[1]

        self.on_change = on_change
        self.on_submit = on_submit
        self.label = None
        if label_str:
            self.label = SimpleText(
                size=label_size,
                text_color=text_color,
                position=(
                    (position[0], position[1] - height)
                    if label_top
                    else (
                        position[0] - get_default_font(label_size).size(label_str)[0] - 5,
                        position[1],
                    )
                ),
                text=label_str,
            )

        # ── Cursor / anchor editing state ──────────────────────────────────
        # ``cursor`` is the insertion caret; ``anchor`` is the *other* end of
        # any selection.  When cursor == anchor there is no selection.
        self.cursor: int = len(initial_text)
        self.anchor: int = len(initial_text)

        self._update_rect()

    # ── Selection helpers ──────────────────────────────────────────────────

    @property
    def selection(self) -> Tuple[int, int]:
        """Return (lo, hi) ordered selection indices."""
        return (min(self.cursor, self.anchor), max(self.cursor, self.anchor))

    def has_selection(self) -> bool:
        return self.cursor != self.anchor

    def _replace_selection(self, replacement: str) -> None:
        """Core editing primitive.

        Replaces the currently selected range (or inserts at ``cursor`` when
        there is no selection) with *replacement*, then advances ``cursor``
        and ``anchor`` to the end of the inserted text.
        """
        lo, hi = self.selection
        self.text_str = self.text_str[:lo] + replacement + self.text_str[hi:]
        self.cursor = self.anchor = lo + len(replacement)

    # ── Layout helpers ─────────────────────────────────────────────────────

    def _wrap_text(self) -> List[Tuple[str, int]]:
        """Word-wrap ``text_str`` into ``(line_text, start_index)`` tuples.

        ``start_index`` is the offset of ``line_text[0]`` in ``text_str``,
        so cursor positions can be mapped to screen coordinates and vice-versa.
        """
        max_w = self.width - (2 * self.padding)
        words = self.text_str.split(" ")
        lines: List[Tuple[str, int]] = []
        current_line = ""
        current_start = 0
        char_offset = 0

        for word in words:
            # +1 for the space separator (except at the very start)
            sep = " " if current_line else ""
            candidate = current_line + sep + word
            if self.font.size(candidate)[0] <= max_w:
                current_line = candidate
            else:
                lines.append((current_line, current_start))
                current_start = char_offset
                current_line = word
            char_offset += len(sep) + len(word)

        lines.append((current_line, current_start))
        return lines if lines else [("", 0)]

    def _update_rect(self):
        lines = self._wrap_text()
        line_height = self.font.get_height()
        new_height = max(self.base_height, len(lines) * line_height + (self.padding * 2))
        self.rect.height = new_height
        # Grow upwards
        self.rect.y = self.base_y - (new_height - self.base_height)

    def _char_x_in_line(self, line_text: str, char_index_in_line: int) -> int:
        """Return the pixel x offset of a character index within a single line."""
        return self.font.size(line_text[:char_index_in_line])[0]

    def _cursor_line_and_col(self):
        """Return (line_index, col_in_line) for ``self.cursor``."""
        lines = self._wrap_text()
        for i, (line_text, line_start) in enumerate(lines):
            line_end = line_start + len(line_text)
            # cursor sits on this line if it is within the range, or if this
            # is the last line and cursor == total length
            if self.cursor <= line_end or i == len(lines) - 1:
                return i, self.cursor - line_start, lines
        return 0, 0, lines

    def _char_index_from_pos(self, pos: Tuple[int, int]) -> int:
        """Translate a screen position to the nearest character index."""
        lines = self._wrap_text()
        line_height = self.font.get_height()
        rel_y = pos[1] - (self.rect.y + self.padding)
        line_idx = max(0, min(len(lines) - 1, int(rel_y // line_height)))
        line_text, line_start = lines[line_idx]
        rel_x = pos[0] - (self.rect.x + self.padding)
        # Scan characters to find closest
        best = 0
        for k in range(1, len(line_text) + 1):
            w = self.font.size(line_text[:k])[0]
            if w >= rel_x:
                prev_w = self.font.size(line_text[: k - 1])[0]
                best = (k - 1) if (rel_x - prev_w) < (w - rel_x) else k
                break
        else:
            best = len(line_text)
        return min(line_start + best, len(self.text_str))

    # ── Internal helpers ───────────────────────────────────────────────────

    def _on_change(self):
        typewriter_sound()
        self._update_rect()
        if self.on_change:
            self.on_change(self.text_str)

    def _gain_focus(self):
        self.focus = True
        pygame.key.start_text_input()
        pygame.key.set_repeat(400, 35)

    def _lose_focus(self):
        self.focus = False
        pygame.key.stop_text_input()
        pygame.key.set_repeat()  # Clear repeat

    # ── Rendering ──────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Background / border
        color = self.focus_background_color if self.focus else self.background_color
        pygame.draw.rect(surface, color, self.rect, width=self.border_width)

        lines = self._wrap_text()
        line_height = self.font.get_height()
        y = self.rect.y + self.padding

        blink_on = self.focus and (pygame.time.get_ticks() % 1000 < 500)
        lo, hi = self.selection

        for i, (line_text, line_start) in enumerate(lines):
            line_end = line_start + len(line_text)
            x_base = self.rect.x + self.padding

            # ── Selection highlight ─────────────────────────────────────
            if self.has_selection() and lo < line_end and hi > line_start:
                hl_start = max(lo, line_start) - line_start
                hl_end = min(hi, line_end) - line_start
                x0 = x_base + self.font.size(line_text[:hl_start])[0]
                x1 = x_base + self.font.size(line_text[:hl_end])[0]
                pygame.draw.rect(
                    surface, (70, 100, 160), (x0, y, max(2, x1 - x0), line_height)
                )

            # ── Text ───────────────────────────────────────────────────
            txt_surf = self.font.render(line_text, True, self.text_color)
            surface.blit(txt_surf, (x_base, y))

            # ── Cursor ─────────────────────────────────────────────────
            if blink_on and line_start <= self.cursor <= line_end:
                col = self.cursor - line_start
                cx = x_base + self.font.size(line_text[:col])[0]
                pygame.draw.line(
                    surface, self.text_color, (cx, y), (cx, y + line_height - 2)
                )

            y += line_height

        if self.label:
            self.label.render(surface)

    # ── Event handling ─────────────────────────────────────────────────────

    def update(self, event: pygame.event.Event, mouse_position: Tuple[int, int]):
        if not event:
            return

        # ── Focus via mouse click ───────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_position):
                if not self.focus:
                    self._gain_focus()
                # Click-to-position cursor; collapse any selection
                new_idx = self._char_index_from_pos(mouse_position)
                self.cursor = self.anchor = new_idx
            else:
                if self.focus:
                    self._lose_focus()

        if not self.focus:
            return

        # ── Text input (IME-safe, handles all printable characters) ────
        if event.type == pygame.TEXTINPUT:
            self._replace_selection(event.text)
            self._on_change()

        elif event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            ctrl = bool(mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META)
            shift = bool(mods & pygame.KMOD_SHIFT)

            # ── Clipboard shortcuts ─────────────────────────────────────
            if event.key == pygame.K_a and ctrl:
                # Select all
                self.anchor = 0
                self.cursor = len(self.text_str)

            elif event.key == pygame.K_c and ctrl:
                lo, hi = self.selection
                payload = self.text_str[lo:hi] if self.has_selection() else self.text_str
                copy_to_clipboard(payload)

            elif event.key == pygame.K_v and ctrl:
                pasted = paste_from_clipboard()
                if pasted:
                    self._replace_selection(pasted)
                    self._on_change()

            elif event.key == pygame.K_x and ctrl:
                if self.has_selection():
                    lo, hi = self.selection
                    copy_to_clipboard(self.text_str[lo:hi])
                    self._replace_selection("")
                    self._on_change()

            # ── Deletion ────────────────────────────────────────────────
            elif event.key == pygame.K_BACKSPACE:
                if self.has_selection():
                    self._replace_selection("")
                elif self.cursor > 0:
                    lo = self.cursor - 1
                    self.text_str = self.text_str[:lo] + self.text_str[self.cursor:]
                    self.cursor = self.anchor = lo
                self._on_change()

            elif event.key == pygame.K_DELETE:
                if self.has_selection():
                    self._replace_selection("")
                elif self.cursor < len(self.text_str):
                    self.text_str = (
                        self.text_str[: self.cursor] + self.text_str[self.cursor + 1:]
                    )
                    # cursor stays in place
                self._on_change()

            # ── Submission ──────────────────────────────────────────────
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                if self.on_submit:
                    self.on_submit(self.text_str)
                    self.text_str = ""
                    self.cursor = self.anchor = 0
                    self._on_change()

            # ── Arrow key navigation ─────────────────────────────────────
            elif event.key == pygame.K_LEFT:
                if self.has_selection() and not shift:
                    # Collapse to the left end of the selection
                    self.cursor = self.anchor = self.selection[0]
                elif self.cursor > 0:
                    self.cursor -= 1
                    if not shift:
                        self.anchor = self.cursor

            elif event.key == pygame.K_RIGHT:
                if self.has_selection() and not shift:
                    # Collapse to the right end of the selection
                    self.cursor = self.anchor = self.selection[1]
                elif self.cursor < len(self.text_str):
                    self.cursor += 1
                    if not shift:
                        self.anchor = self.cursor

            elif event.key == pygame.K_HOME:
                # Find start of current wrapped line
                lines = self._wrap_text()
                for line_text, line_start in lines:
                    if line_start <= self.cursor <= line_start + len(line_text):
                        self.cursor = line_start
                        break
                if not shift:
                    self.anchor = self.cursor

            elif event.key == pygame.K_END:
                # Find end of current wrapped line
                lines = self._wrap_text()
                for line_text, line_start in lines:
                    line_end = line_start + len(line_text)
                    if line_start <= self.cursor <= line_end:
                        self.cursor = line_end
                        break
                if not shift:
                    self.anchor = self.cursor

    # ── Public API ─────────────────────────────────────────────────────────

    def change_text(self, text: str):
        self.text_str = text
        self.cursor = self.anchor = len(text)
        self._on_change()

    @property
    def text(self):
        """Backwards-compatible shim for code that uses ``input.text.text``."""
        class _TextProxy:
            def __init__(self, parent):
                self._p = parent

            @property
            def text(self):
                return self._p.text_str

            @text.setter
            def text(self, val):
                self._p.text_str = val
                self._p.cursor = self._p.anchor = len(val)

            def change_text(self, val):
                self._p.change_text(val)

        return _TextProxy(self)
