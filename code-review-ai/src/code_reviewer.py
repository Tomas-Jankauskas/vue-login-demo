import os
from typing import List, Dict, Optional, Union
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from guidelines_processor import GuidelinesProcessor
from dotenv import load_dotenv
import anthropic

# Load environment variables from .env file
load_dotenv()

# Set Anthropic API key in the environment
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "")

class CodeReviewer:
    def __init__(self, 
                 model: Optional[Union[str, BaseChatModel]] = None,
                 temperature: float = 0):
        """Initialize the code reviewer with specified model.
        
        Args:
            model: Either a model name string or a LangChain chat model instance.
                  If string, must be one of: 'gpt-3.5-turbo', 'gpt-4', 'claude-3-opus', 'claude-3-sonnet'
                  If None, defaults to 'gpt-3.5-turbo'
            temperature: Model temperature (0-1). Only used if model is a string.
        """
        if model is None:
            model = "gpt-3.5-turbo"
            
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
            
        self.guidelines_processor = GuidelinesProcessor()
        
        # Define the review prompt template
        self.prompt_template = ChatPromptTemplate.from_template("""You are an expert code reviewer specializing in enforcing Frontend Development Guidelines.
Your task is to thoroughly analyze code changes against the provided guidelines and identify ANY violations.

For each guideline section provided, you must:
1. Check if the code violates any guidelines in that section
2. Report ALL violations found, no matter how minor

For each violation found, you MUST:
1. Quote the EXACT guideline text being violated
2. Show the specific code that violates it
3. Explain WHY it's a violation
4. Provide a detailed solution showing how to fix it

Format your review as:
- 🎯 Guideline Violations:
  Group violations by section:
  
  [Section Name] Violations:
  - [Guideline]: "exact guideline text"
    Code: `relevant code snippet`
    Why: Clear explanation of the violation
    Fix: Specific solution with example code
  
  [Next Section] Violations:
  ...

- 🐛 Potential Issues:
  List any technical problems, bugs, or security concerns

- 💡 Suggestions:
  Provide specific, actionable suggestions for improvement

You MUST check EVERY guideline in EACH section provided. Do not skip any checks.
If a section has no violations, explicitly state "No violations found in this section."

Here are the relevant guidelines for this code review, organized by section:

{guidelines}

Code to Review:
{code_diff}

Additional Context:
{context}

Please provide a thorough code review following the specified format.""")
    
    def _format_guidelines(self, guidelines_docs: List[Document]) -> str:
        """Format retrieved guidelines into a readable string with section information."""
        # Group guidelines by section
        sections: Dict[str, List[str]] = {}
        for doc in guidelines_docs:
            section_title = doc.metadata.get('section_title', 'Other Guidelines')
            if section_title not in sections:
                sections[section_title] = []
            sections[section_title].append(doc.page_content.strip())
        
        # Format each section with clear separation and numbering
        formatted_sections = []
        for i, (title, chunks) in enumerate(sorted(sections.items()), 1):
            # Combine chunks and remove any duplicate content
            lines = []
            seen_lines = set()
            for chunk in chunks:
                for line in chunk.split('\n'):
                    line = line.strip()
                    if line and line not in seen_lines:
                        seen_lines.add(line)
                        lines.append(line)
            
            # Format section with clear boundaries and content
            section = [
                "=" * 80,
                f"Section {i}: {title}",
                "=" * 80,
                "",  # Empty line for readability
                "\n".join(lines),
                "",  # Empty line for readability
            ]
            formatted_sections.append("\n".join(section))
        
        return "\n".join(formatted_sections)
    
    def review_code(self, 
                   code_diff: str, 
                   context: Optional[str] = None,
                   n_relevant_guidelines: int = 10) -> str:
        """
        Review code changes using relevant guidelines.
        
        Args:
            code_diff: The code changes to review
            context: Additional context about the changes (optional)
            n_relevant_guidelines: Number of relevant guideline chunks to retrieve
        
        Returns:
            Detailed code review following company guidelines
        """
        # Get relevant guidelines
        relevant_guidelines = self.guidelines_processor.get_relevant_guidelines(
            code_diff, 
            n_results=n_relevant_guidelines
        )
        
        # Format the guidelines with section information
        formatted_guidelines = self._format_guidelines(relevant_guidelines)
        
        # Create the prompt
        prompt = self.prompt_template.format_messages(
            guidelines=formatted_guidelines,
            code_diff=code_diff,
            context=context or "No additional context provided."
        )
        
        # Get the review
        review = self.llm.invoke(prompt)
        return review.content

def main():
    # Test both models
    print("\nGPT-3.5 Review:")
    gpt_reviewer = CodeReviewer("gpt-3.5-turbo", temperature=0)
    
    # Read test component
    with open("test_component.js", "r") as f:
        code_diff = f.read()
    
    # Get GPT review
    gpt_review = gpt_reviewer.review_code(
        code_diff,
        context="This is a Vue.js component that needs to follow our frontend guidelines."
    )
    print(gpt_review)
    
    print("\nClaude 3.5 Sonnet Review:")
    claude_reviewer = CodeReviewer("claude-3-5-sonnet-20241022", temperature=0)
    
    # Get Claude review
    claude_review = claude_reviewer.review_code(
        code_diff,
        context="This is a Vue.js component that needs to follow our frontend guidelines."
    )
    print(claude_review)

if __name__ == "__main__":
    main()