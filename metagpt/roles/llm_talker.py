#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025-11-15
@Author  : AI Assistant
@File    : llm_talker.py
@Desc    : A role that handles LLM communication, sending messages to LLM and returning responses to clients.
"""

from typing import Optional

from pydantic import Field

from metagpt.roles import Role
from metagpt.schema import Message, AIMessage


class LLMTalker(Role):
    """A role that handles LLM communication.
    
    This role acts as a bridge between clients and LLM, handling message sending
    and response retrieval without complex business logic.
    """
    
    name: str = "LLMTalker"
    profile: str = "LLM Communication Handler"
    goal: str = "Send messages to LLM and return responses to clients"
    constraints: str = "Provide accurate and timely LLM responses"
    desc: str = "A simple LLM communication role that forwards messages to LLM and returns responses"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Simple initialization - no complex actions needed
        self.set_actions([])
    
    async def think(self) -> bool:
        """Always ready to process messages."""
        # Always return True to indicate readiness
        return True
    
    async def act(self) -> Message:
        """Process the latest message and get LLM response."""
        if not self.rc.news:
            # No messages to process
            return AIMessage(content="No message to process", cause_by=self)
        
        # Get the latest message
        latest_msg = self.rc.news[-1]
        
        # Send message to LLM and get response
        try:
            response = await self.llm.aask(latest_msg.content)
            logger.info(f"LLM Response: {response}")
            
            # Return the LLM response as an AI message
            return AIMessage(
                content=response,
                cause_by=self,
                sent_from=self
            )
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return AIMessage(
                content=f"Error processing message: {str(e)}",
                cause_by=self
            )
    
    async def talk_to_llm(self, message: str) -> str:
        """Direct method to send a message to LLM and get response.
        
        Args:
            message (str): The message to send to LLM
            
        Returns:
            str: The LLM response
        """
        try:
            response = await self.llm.aask(message)
            return response
        except Exception as e:
            logger.error(f"Error in talk_to_llm: {e}")
            return f"Error: {str(e)}"
    
    def set_llm_client(self, llm_client):
        """Set the LLM client to use.
        
        Args:
            llm_client: The LLM client instance
        """
        self.llm = llm_client
        if hasattr(self.llm, 'system_prompt'):
            self.llm.system_prompt = self._get_prefix()
    
    def get_status(self) -> dict:
        """Get current status of the LLM talker.
        
        Returns:
            dict: Status information
        """
        return {
            "name": self.name,
            "profile": self.profile,
            "status": "ready",
            "message_count": len(self.rc.news),
            "latest_message": self.rc.news[-1].content if self.rc.news else None
        }