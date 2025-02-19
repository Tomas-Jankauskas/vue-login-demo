import os
import sys
from typing import List, Dict, Optional, Union
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.chat_models.base import BaseChatModel
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from dotenv import load_dotenv
import anthropic

# Load environment variables from .env file
load_dotenv()

class CodeReviewer:
    def __init__(self, 
                 model: Optional[Union[str, BaseChatModel]] = None,
                 temperature: float = 0):
        """Initialize the code reviewer with specified model."""
        if model is None:
            model = "claude-3-5-sonnet-20241022"
            
        if isinstance(model, str):
            if model.startswith("gpt"):
                self.llm = ChatOpenAI(model_name=model, temperature=temperature)
            elif model.startswith("claude"):
                self.llm = ChatAnthropic(
                    model=model,
                    temperature=temperature,
                    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
                )
            else:
                raise ValueError(f"Unsupported model: {model}")
        else:
            self.llm = model
            
        # Define the review prompt template
        self.prompt_template = ChatPromptTemplate.from_template("""You are an expert code reviewer specializing in Frontend Development.
Your task is to thoroughly analyze code changes and identify ANY issues or potential improvements.

For each issue found, you MUST:
1. Show the specific code that needs improvement
2. Explain WHY it's an issue
3. Provide a detailed solution showing how to fix it

Format your review as:
- 🎯 Code Issues:
  Group issues by category (Security, Performance, Accessibility, etc.):
  
  [Category] Issues:
  - Issue: Description
    Code: `relevant code snippet`
    Why: Clear explanation
    Fix: Specific solution with example code
  
  [Next Category] Issues:
  ...

- 🐛 Potential Problems:
  List any technical problems, bugs, or security concerns

- 💡 Suggestions:
  Provide specific, actionable suggestions for improvement

Code to Review:
{code}

Additional Context:
{context}

Please provide a thorough code review following the specified format.""")
    
    def review_code(self, 
                   code: str, 
                   context: Optional[str] = None) -> str:
        """
        Review code changes.
        
        Args:
            code: The code to review
            context: Additional context about the changes (optional)
        
        Returns:
            Detailed code review
        """
        # Create the prompt
        prompt = self.prompt_template.format_messages(
            code=code,
            context=context or "No additional context provided."
        )
        
        # Get the review
        review = self.llm.invoke(prompt)
        return review.content

def main():
    if len(sys.argv) < 2:
        print("Please provide a file to review")
        sys.exit(1)
        
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
        
    # Read the file
    with open(file_path, "r") as f:
        code = f.read()
    
    # Initialize reviewer with Claude 3.5 Sonnet
    reviewer = CodeReviewer("claude-3-5-sonnet-20241022", temperature=0)
    
    # Get review
    review = reviewer.review_code(
        code,
        context=f"Reviewing file: {file_path}"
    )
    
    print(review)

if __name__ == "__main__":
    main()