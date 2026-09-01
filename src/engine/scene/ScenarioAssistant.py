import os
import queue
import re
import threading
import pygame
from src.engine.scene.Scene import Scene
from src.engine.ui.Button import Button
from src.engine.ui.SimpleText import SimpleText
from src.engine.ui.UIElement import UIElement
from src.utils import get_default_font, copy_to_clipboard, paste_from_clipboard


def wrap_text_indexed(text, font, max_w):
    """Word-wrap *text* to fit *max_w* px.

    Returns ``[(line_text, start_index), ...]`` where *start_index* maps each
    wrapped line back to its offset in the original string, so that clicks /
    selections on a wrapped line can be translated back to a global text index.
    """
    lines = []
    n = len(text)
    i = 0
    cur = ""
    cur_start = 0
    while i <= n:
        if i == n or text[i] == '\n':
            lines.append((cur, cur_start))
            cur = ""
            cur_start = i + 1
            i += 1
            continue
        j = i
        while j < n and text[j] not in (' ', '\n'):
            j += 1
        word = text[i:j]
        candidate = cur + (' ' if cur else '') + word
        if not cur or font.size(candidate)[0] <= max_w:
            cur = candidate
        else:
            lines.append((cur, cur_start))
            cur = word
            cur_start = i
        i = j
        if i < n and text[i] == ' ':
            i += 1
    if not lines:
        lines.append(("", 0))
    return lines


def char_index_from_x(line_text, font, rel_x):
    """Return the char index within *line_text* closest to pixel offset *rel_x*."""
    if rel_x <= 0 or not line_text:
        return 0
    for k in range(1, len(line_text) + 1):
        w = font.size(line_text[:k])[0]
        if w >= rel_x:
            prev_w = font.size(line_text[:k - 1])[0]
            return k - 1 if (rel_x - prev_w) < (w - rel_x) else k
    return len(line_text)


class FixedMultilineInput(UIElement):
    """Fixed-size multiline input box with a full cursor+anchor editing state
    machine.

    Features
    --------
    * ``cursor`` / ``anchor`` model with explicit ``selection`` property and
      ``_replace_selection`` primitive — all insertions and deletions go
      through this single entry-point.
    * Left / Right arrow navigation; Shift+arrow extends the selection.
    * Mouse-drag text selection (same as before).
    * Ctrl+A / C / X / V clipboard via the centralised utils helpers.
    * ``pygame.key.set_repeat`` is managed on focus gain/loss.
    * Draggable scrollbar thumb.
    """

    def __init__(self, position, width, height, text_size=14, label_str=""):
        super().__init__(None, position)
        self.rect = pygame.Rect(position[0], position[1], width, height)
        self.padding = 8
        self.text_size = text_size
        self.font = get_default_font(text_size)
        self.label_str = label_str

        self.text_str = ""
        self.focus = False
        self.scroll_y = 0

        # ── Cursor / anchor editing state ──────────────────────────────────
        # ``cursor``  = insertion caret (where the next character will go)
        # ``anchor``  = opposite end of the selection
        # When cursor == anchor there is no active selection.
        self.cursor: int = 0
        self.anchor: int = 0
        self.is_selecting = False   # True while LMB is held inside the box

        # Scrollbar thumb drag state
        self.scroll_dragging = False
        self._drag_start_mouse_y = 0
        self._drag_start_scroll = 0

    def update(self, event=None, mouse_pos=None):
        """Satisfies the abstract base-class requirement (no-op)."""
        pass

    # ── Selection helpers ──────────────────────────────────────────────────

    @property
    def selection(self):
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

    # ── Backwards-compat .text property (mirrors old TextWrapper pattern) ──

    @property
    def text(self):
        class _TextWrapper:
            def __init__(self, parent):
                self.parent = parent

            @property
            def text(self):
                return self.parent.text_str

            @text.setter
            def text(self, val):
                self.parent.text_str = val
                self.parent.cursor = self.parent.anchor = len(val)

        return _TextWrapper(self)

    # ── Layout / metrics helpers ───────────────────────────────────────────

    def _wrap_text(self):
        max_w = self.rect.width - (2 * self.padding) - 10
        return wrap_text_indexed(self.text_str, self.font, max_w)

    def _content_metrics(self):
        lines = self._wrap_text()
        line_h = self.font.get_height() + 2
        total_h = len(lines) * line_h
        visible_h = self.rect.height - (2 * self.padding)
        return lines, line_h, total_h, visible_h

    def _scrollbar_thumb_rect(self):
        """Return ``(thumb_rect, track_rect, max_scroll)`` or ``None``."""
        lines, line_h, total_h, visible_h = self._content_metrics()
        if total_h <= visible_h:
            return None
        track = pygame.Rect(self.rect.right - 10, self.rect.y + 2, 6, self.rect.height - 4)
        thumb_h = max(20, int(track.height * (visible_h / total_h)))
        max_scroll = total_h - visible_h
        fraction = self.scroll_y / max_scroll if max_scroll > 0 else 0
        thumb_y = track.y + int(fraction * (track.height - thumb_h))
        return pygame.Rect(track.x, thumb_y, track.width, thumb_h), track, max_scroll

    def _char_index_at(self, pos):
        """Translate a screen position to the nearest character index."""
        lines = self._wrap_text()
        line_h = self.font.get_height() + 2
        rel_y = pos[1] - (self.rect.y + self.padding - self.scroll_y)
        idx = max(0, min(len(lines) - 1, int(rel_y // line_h)))
        line_text, line_start = lines[idx]
        rel_x = pos[0] - (self.rect.x + self.padding)
        local = char_index_from_x(line_text, self.font, rel_x)
        return min(line_start + local, len(self.text_str))

    def _cursor_screen_x(self, line_text: str, line_start: int) -> int:
        """Return the pixel x of the cursor within *line_text*."""
        col = self.cursor - line_start
        col = max(0, min(col, len(line_text)))
        return self.rect.x + self.padding + self.font.size(line_text[:col])[0]

    # ── Focus management ───────────────────────────────────────────────────

    def _gain_focus(self):
        self.focus = True
        pygame.key.start_text_input()
        pygame.key.set_repeat(400, 35)

    def _lose_focus(self):
        self.focus = False
        pygame.key.stop_text_input()
        pygame.key.set_repeat()

    # ── Rendering ──────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Label above the box
        if self.label_str:
            lbl_surf = get_default_font(14).render(self.label_str, True, (220, 220, 220))
            surface.blit(lbl_surf, (self.rect.x, self.rect.y - 20))

        # Background and border
        bg_color = (25, 25, 35) if self.focus else (15, 15, 22)
        border_color = (100, 150, 255) if self.focus else (60, 60, 80)
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)

        # Clip to the box interior
        old_clip = surface.get_clip()
        surface.set_clip(self.rect.inflate(-4, -4))

        lines, line_h, total_h, visible_h = self._content_metrics()

        max_scroll = max(0, total_h - visible_h)
        if self.scroll_y > max_scroll:
            self.scroll_y = max_scroll

        lo, hi = self.selection
        blink_on = self.focus and not self.has_selection() and (pygame.time.get_ticks() % 1000 < 500)

        y = self.rect.y + self.padding - self.scroll_y
        for i, (line_text, line_start) in enumerate(lines):
            if y + line_h >= self.rect.y and y <= self.rect.bottom:
                line_end = line_start + len(line_text)

                # ── Selection highlight ─────────────────────────────────
                if self.has_selection() and lo < line_end and hi > line_start:
                    hl_start = max(lo, line_start) - line_start
                    hl_end = min(hi, line_end) - line_start
                    x0 = self.rect.x + self.padding + self.font.size(line_text[:hl_start])[0]
                    x1 = self.rect.x + self.padding + self.font.size(line_text[:hl_end])[0]
                    pygame.draw.rect(surface, (70, 100, 160), (x0, y, max(2, x1 - x0), line_h))

                # ── Text ───────────────────────────────────────────────
                surf = self.font.render(line_text, True, (240, 240, 240))
                surface.blit(surf, (self.rect.x + self.padding, y))

                # ── Cursor ─────────────────────────────────────────────
                if blink_on and line_start <= self.cursor <= line_end:
                    cx = self._cursor_screen_x(line_text, line_start)
                    pygame.draw.line(surface, (240, 240, 240), (cx, y), (cx, y + line_h - 2))

            y += line_h

        surface.set_clip(old_clip)

        # Draggable scrollbar (rendered unclipped so it stays on top)
        thumb_info = self._scrollbar_thumb_rect()
        if thumb_info:
            thumb_rect, track, _ = thumb_info
            pygame.draw.rect(surface, (40, 40, 55), track, border_radius=3)
            pygame.draw.rect(surface, (150, 150, 180), thumb_rect, border_radius=3)

    # ── Event handling ─────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if not self.visible:
            return

        # ── Mouse down ─────────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            inside = self.rect.collidepoint(event.pos)
            if inside:
                if not self.focus:
                    self._gain_focus()
                # Check scrollbar first
                thumb_info = self._scrollbar_thumb_rect()
                if thumb_info:
                    thumb_rect, track, max_scroll = thumb_info
                    if thumb_rect.collidepoint(event.pos):
                        self.scroll_dragging = True
                        self._drag_start_mouse_y = event.pos[1]
                        self._drag_start_scroll = self.scroll_y
                        return
                    if track.collidepoint(event.pos):
                        frac = (event.pos[1] - track.y) / max(1, track.height)
                        self.scroll_y = max(0, min(max_scroll, int(frac * max_scroll)))
                        return
                # Click-to-position cursor; collapse any selection
                new_idx = self._char_index_at(event.pos)
                self.cursor = self.anchor = new_idx
                self.is_selecting = True
            else:
                if self.focus:
                    self._lose_focus()
                self.is_selecting = False

        # ── Mouse up ───────────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_selecting = False
            self.scroll_dragging = False

        # ── Mouse motion (drag-select / scrollbar drag) ─────────────────
        if event.type == pygame.MOUSEMOTION:
            if self.scroll_dragging:
                thumb_info = self._scrollbar_thumb_rect()
                if thumb_info:
                    _, track, max_scroll = thumb_info
                    dy = event.pos[1] - self._drag_start_mouse_y
                    self.scroll_y = max(0, min(max_scroll, self._drag_start_scroll + dy))
            elif self.is_selecting and pygame.mouse.get_pressed()[0]:
                # Extend selection by moving cursor; anchor stays put
                self.cursor = self._char_index_at(event.pos)

        if not self.focus:
            return

        # ── Mouse wheel ────────────────────────────────────────────────
        if event.type == pygame.MOUSEWHEEL:
            _, _, total_h, visible_h = self._content_metrics()
            max_scroll = max(0, total_h - visible_h)
            self.scroll_y = max(0, min(max_scroll, self.scroll_y - event.y * 15))

        # ── Text input (printable characters) ─────────────────────────
        elif event.type == pygame.TEXTINPUT:
            self._replace_selection(event.text)

        # ── Key events ─────────────────────────────────────────────────
        elif event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            ctrl = bool(mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META)
            shift = bool(mods & pygame.KMOD_SHIFT)

            # ── Clipboard shortcuts ─────────────────────────────────────
            if event.key == pygame.K_a and ctrl:
                self.anchor = 0
                self.cursor = len(self.text_str)

            elif event.key == pygame.K_c and ctrl:
                lo, hi = self.selection
                payload = self.text_str[lo:hi] if self.has_selection() else self.text_str
                copy_to_clipboard(payload)

            elif event.key == pygame.K_x and ctrl:
                if self.has_selection():
                    lo, hi = self.selection
                    copy_to_clipboard(self.text_str[lo:hi])
                    self._replace_selection("")

            elif event.key == pygame.K_v and ctrl:
                pasted = paste_from_clipboard()
                if pasted:
                    self._replace_selection(pasted)

            # ── Deletion ────────────────────────────────────────────────
            elif event.key == pygame.K_BACKSPACE:
                if self.has_selection():
                    self._replace_selection("")
                elif self.cursor > 0:
                    lo = self.cursor - 1
                    self.text_str = self.text_str[:lo] + self.text_str[self.cursor:]
                    self.cursor = self.anchor = lo

            elif event.key == pygame.K_DELETE:
                if self.has_selection():
                    self._replace_selection("")
                elif self.cursor < len(self.text_str):
                    self.text_str = (
                        self.text_str[: self.cursor] + self.text_str[self.cursor + 1:]
                    )
                    # cursor stays in place

            # ── Return / newline ─────────────────────────────────────────
            elif event.key == pygame.K_RETURN:
                self._replace_selection("\n")

            # ── Arrow key navigation ─────────────────────────────────────
            elif event.key == pygame.K_LEFT:
                if self.has_selection() and not shift:
                    self.cursor = self.anchor = self.selection[0]
                elif self.cursor > 0:
                    self.cursor -= 1
                    if not shift:
                        self.anchor = self.cursor

            elif event.key == pygame.K_RIGHT:
                if self.has_selection() and not shift:
                    self.cursor = self.anchor = self.selection[1]
                elif self.cursor < len(self.text_str):
                    self.cursor += 1
                    if not shift:
                        self.anchor = self.cursor

            elif event.key == pygame.K_UP:
                # Move to the same horizontal position on the line above
                lines = self._wrap_text()
                line_h = self.font.get_height() + 2
                cur_line_idx, cur_col, _ = self._find_cursor_line(lines)
                if cur_line_idx > 0:
                    prev_text, prev_start = lines[cur_line_idx - 1]
                    # Try to keep the same pixel column
                    cur_x = self.font.size(lines[cur_line_idx][0][:cur_col])[0]
                    new_col = char_index_from_x(prev_text, self.font, cur_x)
                    self.cursor = prev_start + new_col
                    if not shift:
                        self.anchor = self.cursor

            elif event.key == pygame.K_DOWN:
                lines = self._wrap_text()
                cur_line_idx, cur_col, _ = self._find_cursor_line(lines)
                if cur_line_idx < len(lines) - 1:
                    next_text, next_start = lines[cur_line_idx + 1]
                    cur_x = self.font.size(lines[cur_line_idx][0][:cur_col])[0]
                    new_col = char_index_from_x(next_text, self.font, cur_x)
                    self.cursor = next_start + new_col
                    if not shift:
                        self.anchor = self.cursor

            elif event.key == pygame.K_HOME:
                lines = self._wrap_text()
                cur_line_idx, _, _ = self._find_cursor_line(lines)
                _, line_start = lines[cur_line_idx]
                self.cursor = line_start
                if not shift:
                    self.anchor = self.cursor

            elif event.key == pygame.K_END:
                lines = self._wrap_text()
                cur_line_idx, _, _ = self._find_cursor_line(lines)
                line_text, line_start = lines[cur_line_idx]
                self.cursor = line_start + len(line_text)
                if not shift:
                    self.anchor = self.cursor

    def _find_cursor_line(self, lines):
        """Return ``(line_index, col_in_line, lines)`` for ``self.cursor``."""
        for i, (line_text, line_start) in enumerate(lines):
            line_end = line_start + len(line_text)
            if self.cursor <= line_end or i == len(lines) - 1:
                return i, max(0, self.cursor - line_start), lines
        return 0, 0, lines


class SelectableOutputView(UIElement):
    """Scrollable, read-only iframe-like view with a draggable scrollbar,
    mouse-drag text selection, and Ctrl+A (select all) / Ctrl+C (copy) support.

    This class is intentionally kept read-only — no keyboard editing, no
    cursor state machine. Clipboard copy uses the centralised util helper.
    """

    def __init__(self, position, width, height, text=""):
        super().__init__(None, position)
        self.rect = pygame.Rect(position[0], position[1], width, height)
        self.padding = 10
        self.font = get_default_font(13)
        self._text = text
        self.scroll_y = 0
        self.focused = False

        # Selection state (global indices into self._text)
        self.sel_start = 0
        self.sel_end = 0
        self.is_selecting = False

        # Scrollbar thumb drag state
        self.scroll_dragging = False
        self._drag_start_mouse_y = 0
        self._drag_start_scroll = 0

    def update(self, event=None, mouse_pos=None):
        """Satisfies the abstract base-class requirement (no-op)."""
        pass

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, val):
        self._text = val
        self.scroll_y = 0
        self.sel_start = self.sel_end = 0

    def _get_wrapped_lines(self):
        max_w = self.rect.width - (2 * self.padding) - 12
        return wrap_text_indexed(self._text, self.font, max_w)

    def _selection_range(self):
        return (min(self.sel_start, self.sel_end), max(self.sel_start, self.sel_end))

    def _content_metrics(self):
        lines = self._get_wrapped_lines()
        line_h = self.font.get_height() + 2
        total_h = len(lines) * line_h
        visible_h = self.rect.height - (2 * self.padding)
        return lines, line_h, total_h, visible_h

    def _scrollbar_thumb_rect(self):
        """Return ``(thumb_rect, track_rect, max_scroll)`` or ``None``."""
        lines, line_h, total_h, visible_h = self._content_metrics()
        if total_h <= visible_h:
            return None
        track = pygame.Rect(self.rect.right - 10, self.rect.y + 2, 6, self.rect.height - 4)
        thumb_h = max(20, int(track.height * (visible_h / total_h)))
        max_scroll = total_h - visible_h
        fraction = self.scroll_y / max_scroll if max_scroll > 0 else 0
        thumb_y = track.y + int(fraction * (track.height - thumb_h))
        return pygame.Rect(track.x, thumb_y, track.width, thumb_h), track, max_scroll

    def _char_index_at(self, pos):
        lines = self._get_wrapped_lines()
        line_h = self.font.get_height() + 2
        rel_y = pos[1] - (self.rect.y + self.padding - self.scroll_y)
        idx = max(0, min(len(lines) - 1, int(rel_y // line_h)))
        line_text, line_start = lines[idx]
        rel_x = pos[0] - (self.rect.x + self.padding)
        local = char_index_from_x(line_text, self.font, rel_x)
        return min(line_start + local, len(self._text))

    def render(self, surface: pygame.Surface):
        if not self.visible:
            return

        # Outer frame
        pygame.draw.rect(surface, (12, 12, 18), self.rect)
        pygame.draw.rect(surface, (70, 70, 95), self.rect, 2)

        lines, line_h, total_h, visible_h = self._content_metrics()

        max_scroll = max(0, total_h - visible_h)
        if self.scroll_y > max_scroll:
            self.scroll_y = max_scroll

        sel_a, sel_b = self._selection_range()

        # Viewport clip
        old_clip = surface.get_clip()
        surface.set_clip(self.rect.inflate(-4, -4))

        y = self.rect.y + self.padding - self.scroll_y
        for line_text, line_start in lines:
            if y + line_h >= self.rect.y and y <= self.rect.bottom:
                line_end = line_start + len(line_text)
                if sel_a != sel_b and sel_a < line_end and sel_b > line_start:
                    hl_start = max(sel_a, line_start) - line_start
                    hl_end = min(sel_b, line_end) - line_start
                    x0 = self.rect.x + self.padding + self.font.size(line_text[:hl_start])[0]
                    x1 = self.rect.x + self.padding + self.font.size(line_text[:hl_end])[0]
                    pygame.draw.rect(surface, (70, 100, 160), (x0, y, max(2, x1 - x0), line_h))

                surf = self.font.render(line_text, True, (220, 220, 220))
                surface.blit(surf, (self.rect.x + self.padding, y))
            y += line_h

        surface.set_clip(old_clip)

        # Draggable scrollbar
        thumb_info = self._scrollbar_thumb_rect()
        if thumb_info:
            thumb_rect, track, _ = thumb_info
            pygame.draw.rect(surface, (30, 30, 42), track, border_radius=3)
            pygame.draw.rect(surface, (150, 150, 180), thumb_rect, border_radius=3)

    def handle_event(self, event: pygame.event.Event):
        if not self.visible:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            inside = self.rect.collidepoint(event.pos)
            self.focused = inside
            if inside:
                thumb_info = self._scrollbar_thumb_rect()
                if thumb_info:
                    thumb_rect, track, max_scroll = thumb_info
                    if thumb_rect.collidepoint(event.pos):
                        self.scroll_dragging = True
                        self._drag_start_mouse_y = event.pos[1]
                        self._drag_start_scroll = self.scroll_y
                        return
                    if track.collidepoint(event.pos):
                        frac = (event.pos[1] - track.y) / max(1, track.height)
                        self.scroll_y = max(0, min(max_scroll, int(frac * max_scroll)))
                        return
                self.sel_start = self.sel_end = self._char_index_at(event.pos)
                self.is_selecting = True
            else:
                self.is_selecting = False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_selecting = False
            self.scroll_dragging = False

        if event.type == pygame.MOUSEMOTION:
            if self.scroll_dragging:
                thumb_info = self._scrollbar_thumb_rect()
                if thumb_info:
                    _, track, max_scroll = thumb_info
                    dy = event.pos[1] - self._drag_start_mouse_y
                    self.scroll_y = max(0, min(max_scroll, self._drag_start_scroll + dy))
            elif self.is_selecting and pygame.mouse.get_pressed()[0]:
                self.sel_end = self._char_index_at(event.pos)

        if event.type == pygame.MOUSEWHEEL and self.focused:
            _, _, total_h, visible_h = self._content_metrics()
            max_scroll = max(0, total_h - visible_h)
            self.scroll_y = max(0, min(max_scroll, self.scroll_y - event.y * 20))

        if self.focused and event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            ctrl = bool(mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META)
            if event.key == pygame.K_a and ctrl:
                self.sel_start, self.sel_end = 0, len(self._text)
            elif event.key == pygame.K_c and ctrl:
                sel_a, sel_b = self._selection_range()
                payload = self._text[sel_a:sel_b] if sel_a != sel_b else self._text
                copy_to_clipboard(payload)


class ScenarioAssistant(Scene):
    def build_scene(self, game):
        self.game = game
        sw, sh = self.screen.get_width(), self.screen.get_height()

        self.modal_rect = pygame.Rect((sw - 850) // 2, (sh - 720) // 2, 850, 720)
        modal_x, modal_y = self.modal_rect.topleft

        # ── Thread-safe UI update queue ────────────────────────────────────
        # Worker threads must NOT mutate Pygame UI state directly.  They post
        # callables here and the main thread drains them in update().
        self._ui_queue: queue.Queue = queue.Queue()

        # Copy-button feedback timer (pygame.time.get_ticks() epoch)
        self._copy_feedback_until: int = 0

        self.lbl_subtitle = SimpleText(
            "(Clique em um botão de cada vez, do primeiro ao último)",
            13,
            (modal_x + 50, modal_y + 38),
            (180, 180, 180),
        )

        # Navigation Buttons
        self.btn_current = Button(
            image=None,
            text=SimpleText("1. Entenda o cenário atual", 14, (0, 0), (200, 255, 200)),
            position=(modal_x + 50, modal_y + 65),
            click_function=self._show_current_scenario,
            tooltip_text="Exibe as diretrizes e a mensagem inicial ativa do Mestre.",
        )

        self.btn_compile = Button(
            image=None,
            text=SimpleText("2. Compilar Mecânicas", 14, (0, 0), (200, 200, 255)),
            position=(modal_x + 50, modal_y + 105),
            click_function=self._compile_mechanics,
            tooltip_text="Lê a pasta src/model e comprime o código para a IA.",
        )

        # Fixed-Size User Input Box
        self.world_input = FixedMultilineInput(
            position=(modal_x + 50, modal_y + 155),
            width=750,
            height=75,
            text_size=13,
            label_str="Detalhe aqui a nova crônica (ex: Sci-Fi distópico):",
        )

        # Generation Buttons
        self.btn_generate = Button(
            image=None,
            text=SimpleText("3. Gerar Novo Mundo via IA", 14, (0, 0), (255, 200, 200)),
            position=(modal_x + 50, modal_y + 240),
            click_function=self._generate_new_world,
            tooltip_text="Gera um novo DEFAULT_SCENARIO para o scenario.py.",
        )

        self.btn_agentic = Button(
            image=None,
            text=SimpleText(
                "4. Gerar Prompt de Adaptação (Agente)", 14, (0, 0), (255, 220, 150)
            ),
            position=(modal_x + 50, modal_y + 300),
            click_function=self._generate_agentic_prompt,
            tooltip_text="Gera um mega-prompt focado em adaptar o src/model para a nova crônica.",
        )

        # Output header & copy button
        self.btn_copy_iframe = Button(
            image=None,
            text=SimpleText("📋 Copiar Conteúdo", 13, (0, 0), (255, 255, 255)),
            position=(modal_x + 650, modal_y + 250),
            click_function=self._copy_output_to_clipboard,
            background_color=(40, 80, 50),
        )
        self.btn_copy_iframe.visible = False

        # Floating close button for the output panel
        self.btn_floating_close = Button(
            image=None,
            text=SimpleText(" X ", 16, (0, 0), (255, 120, 120)),
            position=(modal_x + 800, modal_y + 299),
            click_function=self._hide_output,
            background_color=(60, 20, 20),
        )
        self.btn_floating_close.visible = False

        # Selectable output view
        self.output_view = SelectableOutputView(
            position=(modal_x + 50, modal_y + 280),
            width=750,
            height=280,
            text="Selecione uma opção acima para visualizar informações ou gerar conteúdo.",
        )
        self.output_view.visible = False

        # File saving controls
        self.filename_input = FixedMultilineInput(
            position=(modal_x + 50, modal_y + 595),
            width=430,
            height=30,
            text_size=13,
            label_str="Nome do arquivo (para salvar em worldgen/):",
        )
        self.filename_input.text_str = "custom_scenario.py"
        self.filename_input.cursor = self.filename_input.anchor = len(
            self.filename_input.text_str
        )
        self.filename_input.visible = False

        self.btn_overwrite = Button(
            image=None,
            text=SimpleText("Sobrescrever scenario.py", 14, (0, 0), (255, 200, 200)),
            position=(modal_x + 500, modal_y + 595),
            click_function=self._overwrite_scenario,
            tooltip_text="Substitui diretamente o arquivo scenario.py atual.",
        )
        self.btn_overwrite.visible = False

        self.btn_save_new = Button(
            image=None,
            text=SimpleText("Salvar em worldgen/", 14, (0, 0), (200, 255, 200)),
            position=(modal_x + 500, modal_y + 635),
            click_function=self._save_new_scenario_file,
            tooltip_text="Cria o arquivo na pasta worldgen/ no diretório raiz.",
        )
        self.btn_save_new.visible = False

        self.btn_back = Button(
            image=None,
            text=SimpleText("Voltar para Opções", 16, (0, 0), (255, 255, 255)),
            position=(modal_x + 50, modal_y + 675),
            click_function=self._close,
        )

        elements = [
            SimpleText(
                "Assistente de Criação de Mundos", 20, (modal_x + 50, modal_y + 12)
            ),
            self.lbl_subtitle,
            self.btn_floating_close,
            self.btn_current,
            self.btn_compile,
            self.world_input,
            self.btn_generate,
            self.btn_agentic,
            self.btn_copy_iframe,
            self.output_view,
            self.filename_input,
            self.btn_overwrite,
            self.btn_save_new,
            self.btn_back,
        ]

        self.minified_context = ""
        self.is_generating = False
        self.pending_generated_code = ""
        return elements

    # ── Event routing ──────────────────────────────────────────────────────

    def handle_events(self, events, mouse_pos):
        """Passes events to input controls and elements."""
        for event in events:
            if hasattr(self.world_input, "handle_event"):
                self.world_input.handle_event(event)
            if (
                hasattr(self.filename_input, "handle_event")
                and self.filename_input.visible
            ):
                self.filename_input.handle_event(event)
            if (
                hasattr(self.output_view, "handle_event")
                and self.output_view.visible
            ):
                self.output_view.handle_event(event)

        super().handle_events(events, mouse_pos)

    # ── Copy-button ────────────────────────────────────────────────────────

    def _copy_output_to_clipboard(self):
        sel_a, sel_b = self.output_view._selection_range()
        payload = (
            self.output_view.text[sel_a:sel_b]
            if sel_a != sel_b
            else self.output_view.text
        )
        ok = copy_to_clipboard(payload)

        # Update the button label using timestamp-based feedback so it
        # automatically resets after 2 seconds without a permanent state change.
        label = "✅ Copiado!" if ok else "⚠ Falha ao copiar"
        self.btn_copy_iframe.text.change_text(label)
        self.btn_copy_iframe.update_image()
        # update_image() now re-applies position internally (Button.py fix),
        # so no manual rect.topleft patch is needed here.
        self._copy_feedback_until = pygame.time.get_ticks() + 2000

    # ── Output panel visibility ────────────────────────────────────────────

    def _show_output(self, text: str, reset_save_controls: bool = True):
        """Single source of truth for opening the output panel/iframe."""
        self.output_view.text = text
        self.output_view.visible = True
        self.btn_copy_iframe.visible = True
        self.btn_floating_close.visible = True

        if reset_save_controls:
            self.filename_input.visible = False
            self.btn_overwrite.visible = False
            self.btn_save_new.visible = False

    def _hide_output(self):
        """Closes just the output panel without leaving the ScenarioAssistant scene."""
        self.output_view.visible = False
        self.btn_copy_iframe.visible = False
        self.btn_floating_close.visible = False
        self.filename_input.visible = False
        self.btn_overwrite.visible = False
        self.btn_save_new.visible = False

    # ── Scene actions ──────────────────────────────────────────────────────

    def _show_current_scenario(self):
        scenario_text = (
            f"--- CENÁRIO ATUAL ---\n\n"
            f"O jogo é feito em Python com Pygame e o cenário é armazenado em scenario.py:\n\n"
            f"[SYSTEM PROMPT]\n{self.game.scenario.system_prompt}\n\n"
            f"[INITIAL MESSAGE]\n{self.game.scenario.initial_message}\n\n"
            f"---------------------"
        )
        self._show_output(scenario_text)

    def _minify_python(self, code: str) -> str:
        code = re.sub(r'(""".*?"""|\'\'\'.*?\'\'\')', '', code, flags=re.DOTALL)
        code = re.sub(r'#.*', '', code)
        lines = [line.rstrip() for line in code.splitlines() if line.strip()]
        return "\n".join(lines)

    def _compile_mechanics(self):
        model_path = os.path.join("src", "model")
        context_parts = []

        if not os.path.exists(model_path):
            self._show_output(f"[Erro] Diretório {model_path} não encontrado.")
            return

        for root, _, files in os.walk(model_path):
            for file in files:
                if not file.endswith('.py') or file == "__init__.py":
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        minified = self._minify_python(f.read())
                        context_parts.append(f"--- {file} ---\n{minified}")
                except Exception:
                    pass

        self.minified_context = "\n\n".join(context_parts)
        self._show_output(
            f"[System] Sucesso! Código minificado (Tamanho aprox: {len(self.minified_context) // 1024} KB)."
        )

    def _generate_new_world(self):
        if self.is_generating:
            return

        user_idea = self.world_input.text_str.strip()
        if not user_idea:
            self._show_output("[Aviso] Digite uma ideia para o novo mundo na caixa de texto!")
            return

        if not self.minified_context:
            self._show_output(
                "[Aviso] Por favor, compile as mecânicas (Botão 2) antes de gerar o mundo."
            )
            return

        self._show_output(
            f"[System] Solicitando novo mundo para: '{user_idea}'...\nAguarde..."
        )
        self.is_generating = True

        threading.Thread(
            target=self._ai_worker_world, args=(user_idea,), daemon=True
        ).start()

    def _generate_agentic_prompt(self):
        if self.is_generating:
            return

        user_idea = self.world_input.text_str.strip()
        if not user_idea:
            self._show_output("[Aviso] Digite uma ideia para a adaptação na caixa de texto!")
            return

        if not self.minified_context:
            self._show_output("[Aviso] Por favor, compile as mecânicas (Botão 2) antes!")
            return

        self._show_output(
            f"[System] Construindo Prompt de Agente IA para: '{user_idea}'..."
        )
        self.is_generating = True

        threading.Thread(
            target=self._ai_worker_agent, args=(user_idea,), daemon=True
        ).start()

    # ── AI worker threads ──────────────────────────────────────────────────
    # These run on background threads.  They must NEVER touch Pygame objects
    # directly.  All UI mutations are posted as callables to self._ui_queue
    # and executed on the main thread inside update().

    def _ai_worker_world(self, user_idea: str):
        mega_prompt = (
            f"Você é um engenheiro de software e Game Designer. Abaixo está o código minificado "
            f"das mecânicas do meu RPG:\n\n{self.minified_context}\n\n"
            f"Crie um novo 'DEFAULT_SCENARIO' (com system_prompt e initial_message) para a temática: '{user_idea}'. "
            f"Retorne APENAS o código Python válido para substituir o DEFAULT_SCENARIO atual em scenario.py."
        )
        self._execute_gemini_request(mega_prompt, is_agent=False)

    def _ai_worker_agent(self, user_idea: str):
        mega_prompt = (
            f"Você é um Arquiteto de Software sênior focado em Python e Orientação a Objetos. "
            f"Abaixo está o código minificado das mecânicas (src/model):\n\n{self.minified_context}\n\n"
            f"Escreva um Prompt de Agente (Agentic Prompt) detalhado instruindo uma LLM sobre como "
            f"refatorar e alterar as classes, entidades, efeitos, atributos e itens em 'src/model/' para a crônica: '{user_idea}'."
        )
        self._execute_gemini_request(mega_prompt, is_agent=True)

    def _execute_gemini_request(self, prompt: str, is_agent: bool):
        """Run in a background thread.  Posts UI updates to ``_ui_queue``."""
        try:
            if self.game.chat and self.game.chat.client:
                response = self.game.chat.client.models.generate_content(
                    model="gemini-3.1-flash-lite-preview",
                    contents=prompt,
                )
                generated_code = response.text

                header = (
                    "=== PROMPT DE AGENTE GERADO ==="
                    if is_agent
                    else "=== NOVO SCENARIO.PY GERADO ==="
                )

                # ── Post UI mutations safely to the main thread ──────────
                def _apply(code=generated_code, h=header, agent=is_agent):
                    self.pending_generated_code = code
                    self._show_output(f"{h}\n\n{code}", reset_save_controls=False)
                    self.filename_input.visible = True
                    self.btn_save_new.visible = True
                    if agent:
                        self.btn_overwrite.visible = False
                        self.filename_input.text_str = "agent_prompt.txt"
                        self.filename_input.cursor = self.filename_input.anchor = len(
                            self.filename_input.text_str
                        )
                    else:
                        self.btn_overwrite.visible = True
                        self.filename_input.text_str = "custom_scenario.py"
                        self.filename_input.cursor = self.filename_input.anchor = len(
                            self.filename_input.text_str
                        )

                self._ui_queue.put(_apply)
            else:
                self._ui_queue.put(
                    lambda: self._show_output("[Erro] Chat/API Client não inicializado no jogo.")
                )
        except Exception as e:
            err_msg = str(e)
            self._ui_queue.put(
                lambda m=err_msg: self._show_output(f"[Erro na API] {m}")
            )
        finally:
            # is_generating is a simple bool — safe to set from any thread on CPython
            self.is_generating = False

    # ── File operations ────────────────────────────────────────────────────

    def _overwrite_scenario(self):
        if not self.pending_generated_code:
            return
        try:
            with open("src/model/scenario.py", "w", encoding="utf-8") as f:
                f.write(self.pending_generated_code)
            self._show_output(
                "[System] Sucesso! O arquivo 'scenario.py' foi sobrescrito.",
                reset_save_controls=False,
            )
        except Exception as e:
            self._show_output(f"[Erro ao salvar] {e}", reset_save_controls=False)

    def _save_new_scenario_file(self):
        if not self.pending_generated_code:
            return

        filename = self.filename_input.text_str.strip()
        if not filename:
            filename = "world_output.txt"

        folder = "worldgen"
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
            file_path = os.path.join(folder, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.pending_generated_code)
            self._show_output(
                f"[System] Sucesso! Arquivo salvo em '{file_path}'.",
                reset_save_controls=False,
            )
        except Exception as e:
            self._show_output(f"[Erro ao salvar] {e}", reset_save_controls=False)

    def _close(self):
        from src.engine.scene.Options import Options
        self.game.change_scene(Options(None, self.screen, self.game))

    # ── Main loop hooks ────────────────────────────────────────────────────

    def update(self):
        # Draw the modal background
        pygame.draw.rect(self.screen, (20, 20, 20), self.modal_rect)
        pygame.draw.rect(self.screen, (200, 255, 200), self.modal_rect, 2)

        # ── Drain the thread-safe UI queue ──────────────────────────────
        # Worker threads post callables here; we execute them on the main thread
        # so Pygame surfaces are only ever touched from one thread.
        try:
            while True:
                fn = self._ui_queue.get_nowait()
                fn()
        except queue.Empty:
            pass

        # ── Reset copy-button label after feedback window ───────────────
        if (
            self._copy_feedback_until > 0
            and pygame.time.get_ticks() >= self._copy_feedback_until
        ):
            self._copy_feedback_until = 0
            self.btn_copy_iframe.text.change_text("📋 Copiar Conteúdo")
            self.btn_copy_iframe.update_image()
            # update_image() now handles rect.topleft internally — no patch needed.

        super().update()