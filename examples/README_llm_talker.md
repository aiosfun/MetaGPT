# LLMTalker Role Example

This example demonstrates how to use the `LLMTalker` role for LLM communication in MetaGPT framework.

## Overview

The `LLMTalker` role provides a clean interface for LLM communication without complex business logic. It separates LLM handling from the main agent logic.

## Files

- `agent_with_llm_talker.py` - Complete example using MetaGPT framework
- `README_llm_talker.md` - This documentation

## Key Components

### LLMTalker Role (`metagpt/roles/llm_talker.py`)

```python
from metagpt.roles.llm_talker import LLMTalker

# Initialize
llm_talker = LLMTalker()

# Set LLM client
llm_talker.set_llm_client(your_llm_client)

# Send message to LLM
response = await llm_talker.talk_to_llm("Hello, how are you?")
```

### Example Agent Structure

```python
from metagpt.roles.llm_talker import LLMTalker
from metagpt.actions import Action, ActionOutput
from metagpt.schema import Message

class SimpleTalkAction(Action):
    """Action that uses LLMTalker to communicate with LLM"""
    
    def __init__(self, llm_talker: LLMTalker):
        self.llm_talker = llm_talker
    
    async def run(self, message: str, **kwargs) -> ActionOutput:
        response = await self.llm_talker.talk_to_llm(message)
        return ActionOutput(content=response, instruct_content=response)

class AgentWithLLMTalker(Role):
    """Example agent using LLMTalker"""
    
    def __init__(self, llm_config=None):
        self.llm_talker = LLMTalker()
        if llm_config:
            self.llm_talker.set_llm_client(llm_config)
        
        # Set up actions
        self.set_actions([SimpleTalkAction(self.llm_talker)])
```

## Usage Pattern

1. **Initialize LLMTalker**: Create an instance of the role
2. **Set LLM Client**: Optionally configure with an LLM client
3. **Create Actions**: Define actions that use LLMTalker
4. **Set Actions**: Add actions to the role
5. **Run Agent**: Use MetaGPT environment to orchestrate

## Benefits

- **Separation of Concerns**: LLM logic isolated from agent logic
- **Reusability**: LLMTalker can be used across different agents
- **Testability**: Can test LLM communication independently
- **Flexibility**: Easy to swap LLM implementations

## Integration with Existing MetaGPT

The LLMTalker role integrates seamlessly with existing MetaGPT:

- Uses standard `Role` base class
- Compatible with `Action` framework
- Works with `Environment` orchestration
- Supports standard MetaGPT logging

## Running the Example

```bash
cd examples
python agent_with_llm_talker.py
```

This will demonstrate:
- LLMTalker initialization
- LLM communication
- Action execution
- Message handling