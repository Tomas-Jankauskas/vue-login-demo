import os
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

class GuidelinesProcessor:
    def __init__(self, persist_directory: str = "../data/guidelines_db"):
        """Initialize the guidelines processor with a storage location."""
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        
        # Split by sections first (more precise markdown header matching)
        self.section_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            separators=["\n## ", "\n# "],  # Put newlines back
            length_function=len,
        )
        
        # Then split sections into smaller chunks if needed
        self.chunk_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n### ", "\n- ", "\n1. ", "\n\n", "\n", ". "],  # Added numbered list separator
            length_function=len,
        )
    
    def _split_into_sections(self, text: str) -> List[Dict[str, str]]:
        """Split text into sections based on markdown headers."""
        # Split on main headers
        sections = []
        current_section = []
        current_title = "Introduction"
        
        for line in text.split('\n'):
            if line.startswith('# ') or line.startswith('## '):
                # Save previous section if it exists
                if current_section:
                    sections.append({
                        "title": current_title,
                        "content": '\n'.join(current_section)
                    })
                # Start new section
                current_title = line.lstrip('#').strip()
                current_section = [line]
            else:
                current_section.append(line)
        
        # Add the last section
        if current_section:
            sections.append({
                "title": current_title,
                "content": '\n'.join(current_section)
            })
            
        return sections
        
    def process_guidelines(self, guidelines_text: str) -> Chroma:
        """Process guidelines text and store in vector database."""
        # First split into major sections
        sections = self._split_into_sections(guidelines_text)
        
        # Then split each section into smaller chunks if needed
        all_chunks = []
        for i, section in enumerate(sections):
            section_content = section["content"]
            section_title = section["title"]
            
            # Keep small sections intact
            if len(section_content) <= 1000:
                all_chunks.append({
                    "content": section_content,
                    "section_id": f"section_{i}",
                    "section_title": section_title
                })
            else:
                chunks = self.chunk_splitter.split_text(section_content)
                all_chunks.extend([{
                    "content": chunk,
                    "section_id": f"section_{i}_chunk_{j}",
                    "section_title": section_title
                } for j, chunk in enumerate(chunks)])
        
        # Create documents with metadata
        documents = [
            Document(
                page_content=chunk["content"],
                metadata={
                    "source": "company_guidelines",
                    "section_id": chunk["section_id"],
                    "section_title": chunk["section_title"]
                }
            ) for chunk in all_chunks
        ]
        
        # Create vector store with persistence
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        print(f"Processed {len(all_chunks)} guideline chunks from {len(sections)} sections")
        # Print section titles for verification
        print("\nSections found:")
        section_titles = sorted(set(doc.metadata["section_title"] for doc in documents))
        for title in section_titles:
            print(f"- {title}")
            
        return vectorstore
    
    def load_guidelines(self) -> Chroma:
        """Load existing guidelines from persistent storage."""
        if not os.path.exists(self.persist_directory):
            raise FileNotFoundError("No existing guidelines database found. Please process guidelines first.")
            
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
    
    def get_relevant_guidelines(self, code_diff: str, n_results: int = 3) -> List[Document]:
        """Retrieve relevant guideline chunks for a given code diff.
        
        Args:
            code_diff: The code to analyze
            n_results: Number of relevant chunks to retrieve
            
        Returns:
            List of relevant guideline documents, sorted by relevance
        """
        db = self.load_guidelines()
        
        # Get more results initially (3x requested amount)
        initial_results = db.similarity_search_with_relevance_scores(code_diff, k=n_results * 3)
        
        # Group results by section
        sections: Dict[str, List[tuple[Document, float]]] = {}
        for doc, score in initial_results:
            section = doc.metadata.get('section_title', 'Other')
            if section not in sections:
                sections[section] = []
            sections[section].append((doc, score))
        
        # Print sections and scores for debugging
        print("\nRelevance scores by section:")
        for section, docs in sections.items():
            max_score = max(score for _, score in docs)
            print(f"- {section}: {max_score:.3f}")
        
        final_results = []
        
        # First, get the highest scoring document from each section
        # that has a score above our base threshold
        for section_docs in sections.values():
            if section_docs:
                doc, score = max(section_docs, key=lambda x: x[1])
                if score > 0.3:  # Lower base threshold to include more sections
                    final_results.append(doc)
        
        # Then, add additional high-scoring documents
        # Sort all documents by score
        all_scored = sorted(
            [(doc, score) for docs in sections.values() for doc, score in docs],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Add remaining high-scoring documents
        for doc, score in all_scored:
            if doc not in final_results and score > 0.4:  # Higher threshold for additional docs
                final_results.append(doc)
                if len(final_results) >= n_results:
                    break
        
        # If we still haven't reached n_results, add more docs
        if len(final_results) < n_results:
            for doc, _ in all_scored:
                if doc not in final_results:
                    final_results.append(doc)
                    if len(final_results) >= n_results:
                        break
        
        return final_results

def main():
    # Example usage
    processor = GuidelinesProcessor()
    
    # Read guidelines from file
    with open("../data/coding_guidelines.txt", "r") as f:
        guidelines_text = f.read()
    
    # Process and store guidelines
    processor.process_guidelines(guidelines_text)
    
    # Test retrieval
    test_diff = "function example() { const x = 1; }"
    relevant_guidelines = processor.get_relevant_guidelines(test_diff)
    
    print("\nRelevant guidelines for test diff:")
    for doc in relevant_guidelines:
        print(f"\n--- Guideline Chunk {doc.metadata['section_id']} ---")
        print(doc.page_content)

if __name__ == "__main__":
    main()