#!/bin/bash
# GRASS Project: Physical Dice Wiring & UI Layout Diagnostic
# Usage: ./diagnose_refactoring.sh [--verbose] [--export=report.txt]

set -o pipefail
export COLUMNS=120

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

VERBOSE=false
EXPORT_FILE=""
REPORT_LINES=()

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --verbose) VERBOSE=true; shift ;;
    --export=*) EXPORT_FILE="${1#*=}"; shift ;;
    *) echo "Unknown option: $1"; shift ;;
  esac
done

print_header() {
  local level=$1
  local title=$2
  echo -e "\n${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
  echo -e "${MAGENTA}${level}${NC} ${BLUE}${title}${NC}"
  echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}\n"
  REPORT_LINES+=("$level $title")
}

print_section() {
  local title=$1
  echo -e "${CYAN}▸ ${title}${NC}"
  REPORT_LINES+=("  ▸ $title")
}

print_pass() {
  echo -e "${GREEN}✓ PASS${NC}: $1"
  REPORT_LINES+=("✓ PASS: $1")
}

print_fail() {
  echo -e "${RED}✗ FAIL${NC}: $1"
  REPORT_LINES+=("✗ FAIL: $1")
}

print_warn() {
  echo -e "${YELLOW}⚠ WARN${NC}: $1"
  REPORT_LINES+=("⚠ WARN: $1")
}

check_file_exists() {
  local file=$1
  if [[ ! -f "$file" ]]; then
    print_fail "File not found: $file"
    return 1
  fi
  return 0
}

# ============================================================================
# P0: CRITICAL BUG FIXES (THREAD SAFETY)
# ============================================================================

print_header "P0" "CRITICAL BUG FIXES (THREAD SAFETY)"

print_section "ChatScene.py: AI Callback UI Mutations"

if check_file_exists "src/engine/scene/ChatScene.py"; then
  echo "Checking for thread-unsafe mutations in _on_chat_response..."
  
  # Check if queue.Queue is imported
  if grep -q "from queue import Queue\|import queue" src/engine/scene/ChatScene.py; then
    print_pass "queue.Queue imported in ChatScene.py"
  else
    print_fail "queue.Queue NOT imported in ChatScene.py (REQUIRED for thread safety)"
  fi
  
  # Check if _on_chat_response exists
  if grep -q "def _on_chat_response" src/engine/scene/ChatScene.py; then
    echo "Found _on_chat_response callback:"
    grep -n "def _on_chat_response" src/engine/scene/ChatScene.py
    
    # Check for direct self.actual_text.text mutations
    if grep -A 30 "def _on_chat_response" src/engine/scene/ChatScene.py | grep -q "self.actual_text.text\s*="; then
      print_warn "Direct mutation detected: self.actual_text.text = ... in _on_chat_response"
      echo "  (Should be enqueued to thread-safe queue)"
    fi
    
    # Check for TypewriterManager creation
    if grep -A 30 "def _on_chat_response" src/engine/scene/ChatScene.py | grep -q "TypewriterManager"; then
      print_warn "TypewriterManager instantiation in _on_chat_response callback"
      echo "  (Should be enqueued to thread-safe queue)"
    fi
    
    # Check for self.elements.append
    if grep -A 30 "def _on_chat_response" src/engine/scene/ChatScene.py | grep -q "self.elements.append"; then
      print_warn "self.elements.append() in _on_chat_response callback"
      echo "  (Should be enqueued to thread-safe queue)"
    fi
  else
    print_fail "_on_chat_response callback not found in ChatScene.py"
  fi
  
  # Check if update() method drains a queue
  if grep -A 20 "def update" src/engine/scene/ChatScene.py | grep -q "queue\|Queue"; then
    print_pass "update() method appears to drain queue (thread-safe architecture)"
  else
    print_warn "No queue draining detected in update() method"
  fi
fi

echo ""

# ============================================================================
# P1: GAMEPLAY & DICE WIRING FIXES
# ============================================================================

print_header "P1" "GAMEPLAY & DICE WIRING FIXES"

print_section "Skill Pipeline: raw_d20 Parameter Propagation"

if check_file_exists "src/model/skills.py"; then
  echo "Analyzing Skill.execute() signature..."
  
  # Check for Skill class definition
  if grep -q "^class Skill" src/model/skills.py; then
    print_pass "Skill class found"
    
    # Check execute method signature
    if grep -n "def execute" src/model/skills.py | head -3; then
      if grep -A 3 "def execute" src/model/skills.py | grep -q "raw_d20"; then
        print_pass "Skill.execute() accepts raw_d20 parameter"
      else
        print_fail "Skill.execute() does NOT accept raw_d20 parameter (REQUIRED)"
      fi
    fi
  else
    print_fail "Skill class not found in skills.py"
  fi
  
  echo ""
  echo "Checking skill definitions for random.randint() calls..."
  RANDINT_COUNT=$(grep -c "random\.randint" src/model/skills.py)
  if [[ $RANDINT_COUNT -gt 0 ]]; then
    print_warn "Found $RANDINT_COUNT random.randint() calls in skills.py"
    echo "Locations:"
    grep -n "random\.randint" src/model/skills.py | head -5
    if [[ $RANDINT_COUNT -gt 5 ]]; then
      echo "  ... and $((RANDINT_COUNT - 5)) more"
    fi
  else
    print_pass "No unconditional random.randint() calls in skills.py"
  fi
fi

echo ""

print_section "CombatScene.py: Skill Roll Prompting & Physical Dice Awareness"

if check_file_exists "src/engine/scene/CombatScene.py"; then
  echo "Checking for physical_dice_enabled awareness in skill activation..."
  
  # Check for _use_skill_button function
  if grep -q "_use_skill_button\|use_skill" src/engine/scene/CombatScene.py; then
    print_pass "Skill activation method found"
    
    # Check if physical_dice_enabled is checked
    if grep -A 15 "_use_skill_button\|def.*use_skill" src/engine/scene/CombatScene.py | grep -q "physical_dice_enabled\|physical.*dice"; then
      print_pass "physical_dice_enabled check detected in skill activation"
    else
      print_fail "No physical_dice_enabled check in skill activation (REQUIRED)"
    fi
  else
    print_fail "Skill activation method (_use_skill_button) not found"
  fi
  
  echo ""
  echo "Checking for physical d20 input prompt logic..."
  
  # Check for d20 input modal or prompt
  if grep -q "d20\|physical.*input\|roll_input" src/engine/scene/CombatScene.py; then
    print_warn "Physical d20 input references found; verify they're used in skill activation"
    grep -n "d20\|physical" src/engine/scene/CombatScene.py | head -3
  else
    print_fail "No physical d20 input prompt logic detected"
  fi
  
  echo ""
  echo "Checking for skill.execute() calls..."
  EXECUTE_COUNT=$(grep -c "\.execute\|\.execute(" src/engine/scene/CombatScene.py)
  echo "Found $EXECUTE_COUNT skill.execute() calls"
  grep -n "\.execute" src/engine/scene/CombatScene.py
fi

echo ""

print_section "ChatScene.py: Physical Dice Context Injection"

if check_file_exists "src/engine/scene/ChatScene.py"; then
  echo "Checking for physical dice mode context in AI prompt..."
  
  # Check if physical dice context is injected
  if grep -q "Physical Dice Mode\|physical.*dice\|physical_dice_enabled" src/engine/scene/ChatScene.py; then
    print_pass "Physical dice context detected in ChatScene"
    grep -n "Physical Dice Mode\|physical.*dice" src/engine/scene/ChatScene.py
  else
    print_fail "Physical dice context NOT injected into AI prompt (REQUIRED)"
    echo "Expected: system prompt mentioning 'Physical Dice Mode' or 'roll their own real-world dice'"
  fi
  
  echo ""
  echo "Checking ChatScene.__init__() structure..."
  if grep -q "def __init__" src/engine/scene/ChatScene.py; then
    print_pass "ChatScene.__init__() found"
    
    # Check if it references game.physical_dice_enabled
    if grep -A 30 "def __init__" src/engine/scene/ChatScene.py | grep -q "physical_dice_enabled\|self.game"; then
      print_pass "game object accessible in __init__()"
    fi
  fi
fi

echo ""

# ============================================================================
# P2: UI LAYOUT & POLISH
# ============================================================================

print_header "P2" "UI LAYOUT & POLISH"

print_section "CombatScene.py: Action Button Grid Offscreen Clipping"

if check_file_exists "src/engine/scene/CombatScene.py"; then
  echo "Checking _button_grid_position() anchor point..."
  
  if grep -q "_button_grid_position\|button.*grid" src/engine/scene/CombatScene.py; then
    print_pass "Button grid positioning function found"
    
    # Check for hardcoded offscreen y coordinate
    if grep -n "screen.get_height()\s*-\s*50" src/engine/scene/CombatScene.py; then
      print_fail "CRITICAL: Found hardcoded screen.get_height() - 50 (likely offscreen)"
      echo "  Recommendation: Change to screen.get_height() - 150 or higher"
    elif grep -n "start_y.*=.*screen.get_height()" src/engine/scene/CombatScene.py; then
      print_warn "Button grid start_y uses screen.get_height(); verify value is not too low"
      grep -B 2 -A 2 "start_y.*=.*screen.get_height()" src/engine/scene/CombatScene.py
    else
      print_pass "No obvious hardcoded offscreen positioning detected"
    fi
  else
    print_warn "Button grid positioning function not clearly named; manual inspection needed"
  fi
fi

echo ""

print_section "CharacterCreator.py: Attributes Checklist Overflow"

if check_file_exists "src/engine/scene/CharacterCreator.py"; then
  echo "Checking _update_attrib_checklist() y_offset hardcoding..."
  
  if grep -q "_update_attrib_checklist" src/engine/scene/CharacterCreator.py; then
    print_pass "Attribute checklist function found"
    
    # Check for hardcoded y_offset
    if grep -n "y_offset\s*=\s*641" src/engine/scene/CharacterCreator.py; then
      print_fail "CRITICAL: Found hardcoded y_offset = 641 (not resolution-aware)"
      echo "  Recommendation: Dynamically calculate from screen.get_height()"
    elif grep -n "y_offset.*=.*[0-9]\{3,4\}" src/engine/scene/CharacterCreator.py; then
      print_warn "Hardcoded y_offset detected; should be resolution-aware"
      grep -B 2 -A 5 "y_offset.*=.*[0-9]\{3,4\}" src/engine/scene/CharacterCreator.py | head -8
    else
      print_pass "No obvious hardcoded y_offset detected"
    fi
  else
    print_warn "Attribute checklist function not found"
  fi
  
  echo ""
  echo "Checking for dynamic screen resolution handling..."
  
  if grep -q "screen.get_height()\|screen.get_width()" src/engine/scene/CharacterCreator.py; then
    print_pass "Resolution-aware screen.get_*() calls detected"
  else
    print_warn "No dynamic resolution handling detected in CharacterCreator.py"
  fi
fi

echo ""

print_section "UI Components: CharacterSheetPanel & ASCIIBgPlayer Scaling"

for component in "CharacterSheetPanel" "ASCIIBgPlayer"; do
  echo "Analyzing $component..."
  
  # Search for component definition
  COMPONENT_FILE=$(grep -r "class $component" src/ 2>/dev/null | cut -d: -f1 | head -1)
  
  if [[ -n "$COMPONENT_FILE" ]]; then
    print_pass "$component found in: $COMPONENT_FILE"
    
    # Check for absolute positioning
    if grep -A 20 "class $component" "$COMPONENT_FILE" | grep -q "width\s*=.*[0-9]\{3,4\}\|height\s*=.*[0-9]\{3,4\}"; then
      print_warn "Absolute geometry positioning detected in $component"
      echo "  (Should use percentage or relative positioning)"
    else
      print_pass "No obvious absolute geometry in $component"
    fi
  else
    print_fail "$component class not found in src/ tree"
  fi
  
  echo ""
done

# ============================================================================
# SUMMARY & EXPORT
# ============================================================================

print_header "SUMMARY" "DIAGNOSTIC REPORT COMPLETE"

PASS_COUNT=$(echo "${REPORT_LINES[@]}" | grep -c "^✓")
FAIL_COUNT=$(echo "${REPORT_LINES[@]}" | grep -c "^✗")
WARN_COUNT=$(echo "${REPORT_LINES[@]}" | grep -c "^⚠")

echo -e "Results:"
echo -e "  ${GREEN}✓ PASS: $PASS_COUNT${NC}"
echo -e "  ${RED}✗ FAIL: $FAIL_COUNT${NC}"
echo -e "  ${YELLOW}⚠ WARN: $WARN_COUNT${NC}"

if [[ -n "$EXPORT_FILE" ]]; then
  {
    echo "GRASS Project: Refactoring Diagnostic Report"
    echo "Generated: $(date)"
    echo ""
    printf '%s\n' "${REPORT_LINES[@]}"
  } > "$EXPORT_FILE"
  echo -e "\n${GREEN}Report exported to: $EXPORT_FILE${NC}"
fi

if [[ $FAIL_COUNT -gt 0 ]]; then
  exit 1
else
  exit 0
fi
