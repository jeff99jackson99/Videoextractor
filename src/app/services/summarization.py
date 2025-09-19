"""AI summarization service using OpenAI GPT models."""

import os
from typing import Optional, List
from openai import OpenAI


class SummarizationService:
    """Service for generating summaries using OpenAI GPT models."""

    def __init__(self):
        """Initialize the summarization service."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for summarization"
            )
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    async def generate_summary(
        self, 
        transcript: str, 
        summary_type: str = "comprehensive"
    ) -> str:
        """
        Generate a summary of the transcript.
        
        Args:
            transcript: The transcript text to summarize
            summary_type: Type of summary ('brief', 'comprehensive', 'key_points')
            
        Returns:
            Generated summary text
        """
        if not transcript.strip():
            return "No transcript content to summarize."

        prompt = self._get_summary_prompt(transcript, summary_type)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating clear, concise summaries of video content based on transcripts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise RuntimeError(f"Summary generation failed: {str(e)}")

    async def generate_key_points(self, transcript: str) -> List[str]:
        """
        Extract key points from the transcript.
        
        Args:
            transcript: The transcript text to analyze
            
        Returns:
            List of key points
        """
        if not transcript.strip():
            return ["No transcript content to analyze."]

        prompt = f"""
        Extract the most important key points from this video transcript. 
        Return them as a numbered list, with each point being concise but informative.
        Focus on main topics, important decisions, conclusions, and actionable items.

        Transcript:
        {transcript}

        Key Points:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying and extracting key information from video transcripts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the response into a list
            key_points = []
            for line in content.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove numbering/bullets and add to list
                    cleaned_point = line.lstrip('0123456789.-• ').strip()
                    if cleaned_point:
                        key_points.append(cleaned_point)
            
            return key_points if key_points else [content]
            
        except Exception as e:
            raise RuntimeError(f"Key points extraction failed: {str(e)}")

    async def generate_action_items(self, transcript: str) -> List[str]:
        """
        Extract action items and tasks from the transcript.
        
        Args:
            transcript: The transcript text to analyze
            
        Returns:
            List of action items
        """
        if not transcript.strip():
            return ["No transcript content to analyze."]

        prompt = f"""
        Identify any action items, tasks, or next steps mentioned in this video transcript.
        Return them as a clear list. If no specific action items are mentioned, 
        suggest relevant follow-up actions based on the content.

        Transcript:
        {transcript}

        Action Items:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying actionable tasks and next steps from video content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=600,
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the response into a list
            action_items = []
            for line in content.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove numbering/bullets and add to list
                    cleaned_item = line.lstrip('0123456789.-• ').strip()
                    if cleaned_item:
                        action_items.append(cleaned_item)
            
            return action_items if action_items else [content]
            
        except Exception as e:
            raise RuntimeError(f"Action items extraction failed: {str(e)}")

    def _get_summary_prompt(self, transcript: str, summary_type: str) -> str:
        """Get the appropriate prompt for the summary type."""
        base_prompt = f"Please summarize the following video transcript:\n\n{transcript}\n\n"
        
        if summary_type == "brief":
            return base_prompt + "Provide a brief, 2-3 sentence summary of the main points."
        elif summary_type == "key_points":
            return base_prompt + "Extract and list the key points discussed in the video."
        else:  # comprehensive
            return base_prompt + (
                "Provide a comprehensive summary that covers:\n"
                "1. Main topic/purpose of the video\n"
                "2. Key points and important details\n"
                "3. Conclusions or outcomes\n"
                "4. Any action items or next steps mentioned"
            )
