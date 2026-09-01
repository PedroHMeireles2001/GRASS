import sys
import os
import json
import re

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_json_extraction():
    print("Testing JSON extraction...")
    response_text = "Here is your reward: ```json\n{\"stats\": {\"gold\": 50, \"xp\": 100}}\n``` Enjoy!"
    json_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_pattern, response_text, re.DOTALL)
    if match:
        json_str = match.group(1)
        data = json.loads(json_str)
        print(f"Extracted JSON: {data}")
        assert data["stats"]["gold"] == 50
        assert data["stats"]["xp"] == 100
        
        clean_text = re.sub(json_pattern, '', response_text, flags=re.DOTALL).strip()
        print(f"Clean text: '{clean_text}'")
        assert "Here is your reward:" in clean_text
        assert "Enjoy!" in clean_text
        assert "```json" not in clean_text
    else:
        print("Failed to find JSON match")
        exit(1)
    print("JSON extraction test passed!\n")

def test_rich_text_wrapping():
    print("Testing Rich Text wrapping segments...")
    # Mocking self for TextAreaShow
    class MockTextArea:
        def __init__(self):
            self.text = "This is **bold** text."
            self.width = 350
            self.padding = 20
            # Mocking font.size
            class MockFont:
                def size(self, text):
                    return (len(text) * 10, 20)
                def get_height(self):
                    return 20
            self.font = MockFont()
            self.font_bold = MockFont()
        
        def _wrap_text(self):
            import re
            lines = []
            current_line = []
            current_line_width = 0
            max_width = self.width - 2 * self.padding
            for paragraph in self.text.split("\n"):
                parts = re.split(r'(\*\*.*?\*\*)', paragraph)
                for part in parts:
                    if not part: continue
                    is_bold = part.startswith("**") and part.endswith("**")
                    clean_part = part[2:-2] if is_bold else part
                    words = clean_part.split(" ")
                    for i, word in enumerate(words):
                        display_word = word + (" " if i < len(words) - 1 else "")
                        word_width = len(display_word) * 10 # Simple mock
                        if current_line_width + word_width <= max_width:
                            current_line.append((display_word, is_bold))
                            current_line_width += word_width
                        else:
                            lines.append(current_line)
                            current_line = [(display_word, is_bold)]
                            current_line_width = word_width
                lines.append(current_line)
                current_line = []
                current_line_width = 0
            return lines

    mock = MockTextArea()
    lines = mock._wrap_text()
    print(f"Wrapped lines: {lines}")
    
    found_bold = False
    for line in lines:
        for text, is_bold in line:
            if is_bold:
                found_bold = True
                print(f"Found bold segment: '{text}'")
                assert "bold" in text
    assert found_bold
    print("Rich Text wrapping test passed!\n")

def test_text_area_caching_and_scrollbar():
    print("Testing TextAreaShow caching and scrollbar calculation...")
    import pygame
    pygame.init()
    pygame.font.init()
    # Set a dummy screen so assets/font can be loaded and font module works
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    
    from src.engine.ui.TextArea import TextAreaShow
    
    text_area = TextAreaShow(
        position=(0, 0),
        width=200,
        height=100,
        text="Line 1\nLine 2\nLine 3"
    )
    
    # Check that text is set
    assert text_area.text == "Line 1\nLine 2\nLine 3"
    
    # Check that we cached lines
    assert len(text_area._cached_lines) > 0
    
    # Count how many times _wrap_text is called by mocking it
    wrap_calls = 0
    original_wrap_text = text_area._wrap_text
    def mock_wrap_text():
        nonlocal wrap_calls
        wrap_calls += 1
        return original_wrap_text()
    
    text_area._wrap_text = mock_wrap_text
    
    # Accessing text should not trigger wrap_text
    _ = text_area.text
    assert wrap_calls == 0
    
    # Setting the same text should not trigger wrap_text
    text_area.text = "Line 1\nLine 2\nLine 3"
    assert wrap_calls == 0
    
    # Setting different text should trigger wrap_text
    text_area.text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8"
    assert wrap_calls == 1
    
    # Verify auto-scroll was triggered because number of lines exceeds height (100)
    line_height = text_area.font.get_height()
    max_visible = (text_area.height - 2 * text_area.padding) // line_height
    total_lines = len(text_area._cached_lines)
    assert total_lines > max_visible
    assert text_area.scroll_y > 0
    
    # Test rendering (should not crash and should draw scrollbar)
    surface = pygame.Surface((200, 100))
    text_area.render(surface)
    
    print("TextAreaShow caching and scrollbar test passed!\n")

def test_text_input_cursor():
    print("Testing TextInput blinking cursor...")
    import pygame
    from src.engine.ui.TextInput import TextInput
    
    text_input = TextInput(
        position=(0, 0),
        width=200,
        height=30,
        initial_text="Test input"
    )
    
    # Render with focus = False (should not draw cursor)
    surface_no_focus = pygame.Surface((200, 30))
    text_input.focus = False
    text_input.render(surface_no_focus)
    
    # Render with focus = True (should draw cursor, no crash)
    surface_focus = pygame.Surface((200, 30))
    text_input.focus = True
    text_input.render(surface_focus)
    
    # Quick sanity check on properties
    assert text_input.text.text == "Test input"
    print("TextInput cursor test passed!\n")

if __name__ == "__main__":
    test_json_extraction()
    test_rich_text_wrapping()
    test_text_area_caching_and_scrollbar()
    test_text_input_cursor()
