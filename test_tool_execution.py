#!/usr/bin/env python3
"""
Test script to debug tool execution in v1_basic_agent_improved.py
"""
import asyncio
import json
import sys
import os

# Add the current directory to path so we can import from examples
sys.path.insert(0, '.')
sys.path.insert(0, 'examples')

from pathlib import Path

# Import our tool functions directly
sys.path.append(str(Path('examples')))
try:
    from v1_basic_agent_improved import run_bash, run_write_file, run_read_file
    print("✅ Successfully imported tool functions")
except ImportError as e:
    print(f"❌ Failed to import tool functions: {e}")
    sys.exit(1)

async def test_direct_tool_execution():
    """Test tools directly without LLM"""
    print("\n🧪 Testing direct tool execution...")

    # Test 1: Write a simple file
    print("\n1. Testing write_file...")
    try:
        result = run_write_file("test_file.txt", "Hello World!", "overwrite")
        print(f"✅ write_file result: {result}")

        # Verify file was created
        if Path("test_file.txt").exists():
            print("✅ File was actually created!")
            with open("test_file.txt", "r") as f:
                content = f.read()
                print(f"📄 File content: {content}")
        else:
            print("❌ File was NOT created!")

    except Exception as e:
        print(f"❌ write_file error: {e}")

    # Test 2: Read the file back
    print("\n2. Testing read_file...")
    try:
        result = run_read_file("test_file.txt")
        print(f"✅ read_file result: {result}")
    except Exception as e:
        print(f"❌ read_file error: {e}")

    # Test 3: Test bash command
    print("\n3. Testing bash...")
    try:
        result = run_bash("echo 'Hello from bash'")
        print(f"✅ bash result: {result}")
    except Exception as e:
        print(f"❌ bash error: {e}")

    # Test 4: Test Windows command
    print("\n4. Testing Windows command...")
    try:
        result = run_bash("dir")
        print(f"✅ dir result length: {len(result)} chars")
        print(f"📄 First 200 chars: {result[:200]}...")
    except Exception as e:
        print(f"❌ dir error: {e}")

    # Cleanup
    try:
        Path("test_file.txt").unlink()
        print("🧹 Cleaned up test file")
    except:
        pass

async def test_llm_tool_parsing():
    """Test if the LLM would parse tool calls correctly"""
    print("\n🧪 Testing tool call parsing...")

    # Simulate an LLM response with tool calls
    mock_response = """I'll help you create a snake game. Let me start by checking the directory and then creating the file.

TOOL_CALL: bash
PARAMETERS: {"command": "dir"}

TOOL_CALL: write_file
PARAMETERS: {"path": "snake_game.py", "content": "print('Hello Snake Game')"}

I've created the snake game for you!"""

    print(f"📝 Mock LLM response:\n{mock_response}")

    # Test our regex pattern
    import re
    tool_pattern = r"TOOL_CALL:\s*(\w+)\s*\nPARAMETERS:\s*({.*?})\s*(?=\n\n|\nTOOL_CALL:|$)"
    matches = re.findall(tool_pattern, mock_response, re.DOTALL)

    print(f"\n🔍 Found {len(matches)} tool calls:")
    for i, (tool_name, params_str) in enumerate(matches, 1):
        print(f"  {i}. Tool: {tool_name}")
        print(f"     Parameters: {params_str}")
        try:
            params = json.loads(params_str)
            print(f"     ✅ Valid JSON: {params}")
        except json.JSONDecodeError as e:
            print(f"     ❌ Invalid JSON: {e}")

async def test_simple_snake_game_creation():
    """Test creating a simple snake game directly"""
    print("\n🐍 Testing direct snake game creation...")

    snake_game_code = '''#!/usr/bin/env python3
import turtle
import time
import random

# Simple Snake Game
def snake_game():
    # Set up the screen
    wn = turtle.Screen()
    wn.title("Snake Game")
    wn.bgcolor("black")
    wn.setup(width=600, height=600)
    wn.tracer(0)  # Turns off the screen updates

    # Snake head
    head = turtle.Turtle()
    head.speed(0)
    head.shape("square")
    head.color("white")
    head.penup()
    head.goto(0, 0)
    head.direction = "stop"

    # Snake food
    food = turtle.Turtle()
    food.speed(0)
    food.shape("circle")
    food.color("red")
    food.penup()
    food.goto(0, 100)

    segments = []
    score = 0

    # Functions
    def go_up():
        if head.direction != "down":
            head.direction = "up"

    def go_down():
        if head.direction != "up":
            head.direction = "down"

    def go_left():
        if head.direction != "right":
            head.direction = "left"

    def go_right():
        if head.direction != "left":
            head.direction = "right"

    def move():
        if head.direction == "up":
            y = head.ycor()
            head.sety(y + 20)
        if head.direction == "down":
            y = head.ycor()
            head.sety(y - 20)
        if head.direction == "left":
            x = head.xcor()
            head.setx(x - 20)
        if head.direction == "right":
            x = head.xcor()
            head.setx(x + 20)

    # Keyboard bindings
    wn.listen()
    wn.onkeypress(go_up, "w")
    wn.onkeypress(go_down, "s")
    wn.onkeypress(go_left, "a")
    wn.onkeypress(go_right, "d")

    # Main game loop
    while True:
        wn.update()

        # Check for collision with border
        if head.xcor() > 290 or head.xcor() < -290 or head.ycor() > 290 or head.ycor() < -290:
            time.sleep(1)
            head.goto(0, 0)
            head.direction = "stop"

            # Hide the segments
            for segment in segments:
                segment.goto(1000, 1000)

            segments.clear()
            score = 0

        # Check for collision with food
        if head.distance(food) < 20:
            # Move the food to a random spot
            x = random.randint(-290, 290)
            y = random.randint(-290, 290)
            food.goto(x, y)

            # Add a segment
            new_segment = turtle.Turtle()
            new_segment.speed(0)
            new_segment.shape("square")
            new_segment.color("grey")
            new_segment.penup()
            segments.append(new_segment)

            score += 10

        # Move the end segments first in reverse order
        for i in range(len(segments)-1, 0, -1):
            x = segments[i-1].xcor()
            y = segments[i-1].ycor()
            segments[i].goto(x, y)

        # Move segment 0 to where the head is
        if len(segments) > 0:
            x = head.xcor()
            y = head.ycor()
            segments[0].goto(x, y)

        move()

        # Check for head collision with the body segments
        for segment in segments:
            if segment.distance(head) < 20:
                time.sleep(1)
                head.goto(0, 0)
                head.direction = "stop"

                # Hide the segments
                for segment in segments:
                    segment.goto(1000, 1000)

                segments.clear()
                score = 0

        time.sleep(0.1)

    wn.mainloop()

if __name__ == "__main__":
    snake_game()
    print("Use W/A/S/D keys to control the snake!")
'''

    try:
        result = run_write_file("snake_game_test.py", snake_game_code, "overwrite")
        print(f"✅ Snake game created: {result}")

        # Verify file was created and has content
        if Path("snake_game_test.py").exists():
            file_size = Path("snake_game_test.py").stat().st_size
            print(f"✅ File exists with {file_size} bytes")

            # Check first few lines
            with open("snake_game_test.py", "r") as f:
                first_line = f.readline().strip()
                print(f"📄 First line: {first_line}")

            print("🎮 To run the game: python snake_game_test.py")
        else:
            print("❌ File was NOT created!")

    except Exception as e:
        print(f"❌ Snake game creation error: {e}")

async def main():
    """Run all tests"""
    print("🔧 Tool Execution Debug Test")
    print("=" * 50)

    await test_direct_tool_execution()
    await test_llm_tool_parsing()
    await test_simple_snake_game_creation()

    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())