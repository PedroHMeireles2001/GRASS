### Phase 1: Unify the Text-Editing State Model
Refactor the text-input architecture across editable components (such as @ScenarioAssistant.py and @TextInput.py) from simple string-renderers into true text-editing state machines[cite: 2].

1. **Adopt a Cursor and Anchor Model:**
   * Replace loose selection variables with explicit `self.cursor` and `self.anchor` integers[cite: 2].
   * Define the active selection dynamically via a property helper[cite: 2]:
     ```python
     @property
     def selection(self):
         return (min(self.cursor, self.anchor), max(self.cursor, self.anchor))

     def has_selection(self):
         return self.cursor != self.anchor
     ```
2. **Implement a Unified Replacement Primitive:**
   * Create a helper method `_replace_selection(self, replacement: str)` that handles deleting selected ranges or inserting text precisely at the cursor index, updating cursor and anchor positions cleanly[cite: 2].
3. **Correct Deletion and Insertion Rules:**
   * **Typing / TEXTINPUT:** Route incoming text through `_replace_selection(event.text)` so characters insert at the exact cursor index rather than appending to the end of `text_str`[cite: 1, 2].
   * **Backspace:** If a selection exists, delete it; otherwise, delete the character immediately preceding `self.cursor` (`text[cursor - 1]`) and decrement the cursor[cite: 1, 2].
   * **Delete:** If a selection exists, delete it; otherwise, delete the character immediately following `self.cursor` (`text[cursor]`)[cite: 1, 2].

---

### Phase 2: Centralize Event Policies & Keyboard Focus
1. **Focus Management:** Ensure that only one text-input component holds keyboard focus and active text input state (`pygame.key.start_text_input()` / `pygame.key.stop_text_input()`) at any given time[cite: 1, 5, 8].
2. **Keyboard Repeat Configuration:** Implement `pygame.key.set_repeat(400, 35)` when an editable input gains focus, and clear it (`pygame.key.set_repeat()`) when focus is lost, ensuring smoother held-key behavior for Backspace and arrow navigation[cite: 2].

---

### Phase 3: Harden Component-Specific Utilities and UI Fixes
1. **Clipboard Robustness:**
   * Abstract clipboard operations into reliable helper functions (`copy_to_clipboard` and `paste_from_clipboard`) to safeguard against environment-specific failures across platforms and WSL2 layers[cite: 2].
2. **Stateful UI Buttons:**
   * Update action feedback buttons (such as the copy button in @ScenarioAssistant.py) to use timestamp-based logic (`pygame.time.get_ticks()`) rather than permanent state changes, automatically resetting feedback text after a brief duration[cite: 1, 2].
3. **Thread Safety:**
   * In asynchronous workflows (such as background Gemini generation threads in @ScenarioAssistant.py), marshal UI state updates and output view mutations safely back to the main thread via a thread-safe `Queue` instead of directly modifying UI properties from worker threads[cite: 1, 2].
4. **Button Geometry Safeguard:**
   * In @UIElement.py or @Button.py, ensure that `update_image()` preserves the button's layout position correctly without forcing manual rect realignment on callers[cite: 2].

---

### Execution Scope & File Targets
Apply these architectural patterns systematically to:
* @ScenarioAssistant.py (Focusing on `FixedMultilineInput` and scene-level clipboard/worker flows)[cite: 1, 2]
* @TextInput.py (Focusing on chat input behavior and auto-growing height management)[cite: 2, 5]
* Maintain existing read-only viewport rendering, scrolling metrics, and clipping safeguards in @SelectableOutputView (in @ScenarioAssistant.py) and @TextArea.py[cite: 1, 2, 4].