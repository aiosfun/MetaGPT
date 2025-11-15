#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025-11-15
@Author  : AI Assistant
@File    : agent_with_llm_talker.py
@Desc    : Example of using LLMTalker role for LLM communication in MetaGPT framework
"""

import asyncio
from metagpt.actions import Action, ActionOutput
from metagpt.roles.llm_talker import LLMTalker
from metagpt.logs import logger
from metagpt.schema import Message


class SimpleTalkAction(Action):
    """Simple action to demonstrate LLMTalker usage"""
    
    def __init__(self, llm_talker: LLMTalker):
        self.llm_talker = llm_talker
    
    async def run(self, message: str, **kwargs) -> ActionOutput:
        """Send message to LLM and return response"""
        try:
            response = await self.llm_talker.talk_to_llm(message)
            return ActionOutput(content=response, instruct_content=response)
        except Exception as e:
            logger.error(f"Error in SimpleTalkAction: {e}")
            return ActionOutput(content=f"Error: {str(e)}", instruct_content="")


class AgentWithLLMTalker:
    """Example agent using LLMTalker role for LLM communication"""
    
    def __init__(self, llm_config=None):
        # Initialize LLMTalker role
        self.llm_talker = LLMTalker()
        
        # Set LLM client if provided
        if llm_config:
            self.llm_talker.set_llm_client(llm_config)
        
        # Set up actions
        self.set_actions([SimpleTalkAction(self.llm_talker)])
    
    async def think(self) -> bool:
        """Always ready to process messages"""
        return True
    
    async def act(self) -> Message:
        """Process the latest message and get LLM response"""
        if not self.rc.news:
            return Message(content="No message to process", cause_by=self)
        
        # Get the latest message
        latest_msg = self.rc.news[-1]
        
        # Use the SimpleTalkAction to communicate with LLM
        response = await self.rc.todo.run(latest_msg.content)
        
        # Return the response as a message
        return Message(
            content=response.content if hasattr(response, 'content') else str(response),
            cause_by=self.rc.todo,
            sent_from=self
        )


async def main():
    """Example of using LLMTalker in a MetaGPT agent"""
    from metagpt import LLM
    
    # Initialize LLM (you can configure this as needed)
    llm = LLM()
    
    # Create agent with LLMTalker
    agent = AgentWithLLMTalker(llm_config=llm)
    
    # Set up environment (minimal example)
    from metagpt.environment import Environment
    env = Environment()
    env.add_roles([agent])
    
    print("Agent with LLMTalker initialized!")
    print("Try sending a message like 'hello world'")
    
    # Example interaction
    user_message = Message(content="hello world", cause_by="user")
    env.publish_message(user_message)
    
    # Let the agent process the message
    await agent.run()
    
    # Get the response
    if agent.rc.memory:
        response = agent.rc.memory.get()[-1]
        print(f"LLM Response: {response.content}")


if __name__ == "__main__":
    asyncio.run(main())