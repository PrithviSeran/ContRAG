#!/usr/bin/env python3
"""
Securities GraphRAG Pipeline Runner
Comprehensive system for processing securities contracts into knowledge graphs
"""

import os
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from neo4j import GraphDatabase
from bs4 import BeautifulSoup
import json

from securities_data_models import SecuritiesContract
from securities_extraction import SecuritiesContractExtractor, import_securities_contract_to_neo4j

class SecuritiesGraphRAGPipeline:
    """Complete pipeline for ingesting and querying securities contracts"""
    
    def __init__(self):
        """Initialize the pipeline with all necessary components"""
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        self.extractor = SecuritiesContractExtractor()
        
        # Database connection
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        # Initialize database schema
        self._initialize_database_schema()
    
    def _initialize_database_schema(self):
        """Create database constraints and indexes for better performance"""
        with self.driver.session() as session:
            # Create constraints for unique identification
            constraints = [
                "CREATE CONSTRAINT contract_title IF NOT EXISTS FOR (c:SecuritiesContract) REQUIRE c.title IS UNIQUE",
                "CREATE CONSTRAINT party_name IF NOT EXISTS FOR (p:Party) REQUIRE p.name IS UNIQUE",
                
                # Create indexes for better query performance
                "CREATE INDEX contract_date IF NOT EXISTS FOR (c:SecuritiesContract) ON (c.execution_date)",
                "CREATE INDEX contract_type IF NOT EXISTS FOR (c:SecuritiesContract) ON (c.contract_type)",
                "CREATE INDEX party_role IF NOT EXISTS FOR (p:Party) ON (p.role)",
                "CREATE INDEX security_type IF NOT EXISTS FOR (s:Security) ON (s.security_type)",
                "CREATE INDEX offering_amount IF NOT EXISTS FOR (c:SecuritiesContract) ON (c.total_offering_amount)"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    # Constraint may already exist
                    print(f"Schema setup note: {e}")
    
    def ingest_contract(self, contract_text: str, contract_id: str = None) -> SecuritiesContract:
        """Ingest a single contract into the knowledge graph"""
        
        # Clean and preprocess the text
        cleaned_text = self._clean_contract_text(contract_text)
        
        # Extract structured data using AI
        contract_data = self.extractor.extract_contract_data(cleaned_text)
        
        # Add metadata
        if contract_id:
            contract_data.title = f"{contract_data.title} ({contract_id})"
        
        # Import to Neo4j knowledge graph
        import_securities_contract_to_neo4j(contract_data, self.driver)
        
        return contract_data
    
    def _clean_contract_text(self, text: str) -> str:
        """Clean and preprocess contract text for better extraction"""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove HTML artifacts if present
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove document metadata tags
        text = re.sub(r'<TYPE>.*?</TYPE>', '', text, flags=re.DOTALL)
        text = re.sub(r'<SEQUENCE>.*?</SEQUENCE>', '', text, flags=re.DOTALL)
        text = re.sub(r'<FILENAME>.*?</FILENAME>', '', text, flags=re.DOTALL)
        
        # Clean up special characters
        text = text.replace('\xa0', ' ')  # Non-breaking space
        text = text.replace('\u2019', "'")  # Smart apostrophe
        text = text.replace('\u201c', '"').replace('\u201d', '"')  # Smart quotes
        
        return text.strip()
    
    def query_contracts(self, query: str) -> str:
        """Query the knowledge graph using natural language"""
        
        try:
            # Get relevant contract data from Neo4j
            contract_data = self._get_relevant_contracts(query)
            
            if not contract_data:
                return "No relevant contracts found in the knowledge graph."
            
            # Use LLM to answer the query based on the data
            prompt = f"""
You are a securities law expert analyzing a knowledge graph of securities contracts.
Based on the contract data below, please answer the user's question clearly and comprehensively.

RELEVANT CONTRACT DATA:
{json.dumps(contract_data, indent=2, default=str)}

USER QUESTION: {query}

Please provide a detailed answer based on the contract information above. Include specific details like:
- Contract titles and dates
- Party names and roles
- Financial terms and amounts
- Legal provisions and conditions
- Any patterns or trends across multiple contracts

If the question involves comparisons, calculations, or analysis across multiple contracts, please provide that analysis.
"""
            
            try:
                response = self.llm.invoke(prompt)
                return response.content if response.content else "Sorry, I couldn't generate a response."
            except Exception as e:
                return f"Error generating LLM response: {e}"
                
        except Exception as e:
            return f"Error processing query: {e}. Please try a simpler question or check the database connection."
    
    def _get_relevant_contracts(self, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant contracts from Neo4j based on the query"""
        
        with self.driver.session() as session:
            # Simplified query that works with existing schema
            cypher_query = """
            MATCH (c:SecuritiesContract)
            OPTIONAL MATCH (c)<-[:PARTY_TO]-(p:Party)
            OPTIONAL MATCH (c)-[:ISSUES_SECURITY]->(s:Security)
            OPTIONAL MATCH (c)-[:HAS_CLOSING_CONDITION]->(cc:ClosingCondition)
            
            WITH c,
                 collect(DISTINCT {
                     name: p.name, 
                     role: p.role, 
                     entity_type: p.entity_type,
                     jurisdiction: p.jurisdiction
                 }) as parties,
                 collect(DISTINCT {
                     type: s.security_type,
                     shares: s.number_of_shares,
                     par_value: s.par_value
                 }) as securities,
                 collect(DISTINCT {
                     description: cc.description,
                     is_waivable: cc.is_waivable
                 }) as conditions
            
            RETURN c.title as title,
                   c.contract_type as contract_type,
                   c.summary as summary,
                   c.execution_date as execution_date,
                   c.total_offering_amount as total_offering_amount,
                   parties,
                   securities,
                   conditions
            ORDER BY c.execution_date DESC
            LIMIT $limit
            """
            
            result = session.run(cypher_query, limit=limit)
            contracts = []
            
            for record in result:
                contract = {
                    'title': record['title'],
                    'contract_type': record['contract_type'],
                    'summary': record['summary'],
                    'execution_date': str(record['execution_date']) if record['execution_date'] else None,
                    'total_offering_amount': record['total_offering_amount'],
                    'parties': [p for p in record['parties'] if p.get('name')],
                    'securities': [s for s in record['securities'] if s.get('type')],
                    'conditions': [c for c in record['conditions'] if c.get('description')]
                }
                contracts.append(contract)
            
            return contracts
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get statistics about the knowledge graph"""
        with self.driver.session() as session:
            try:
                # Use separate simpler queries to avoid timeouts
                stats = {}
                
                # Count contracts
                result = session.run("MATCH (c:SecuritiesContract) RETURN count(c) as count")
                stats['Total Contracts'] = result.single()['count']
                
                # Count parties  
                result = session.run("MATCH (p:Party) RETURN count(p) as count")
                stats['Total Parties'] = result.single()['count']
                
                # Count securities
                result = session.run("MATCH (s:Security) RETURN count(s) as count")
                stats['Total Securities'] = result.single()['count']
                
                # Count closing conditions
                result = session.run("MATCH (cc:ClosingCondition) RETURN count(cc) as count")
                stats['Total Closing Conditions'] = result.single()['count']
                
                # Count representations
                result = session.run("MATCH (r:Representation) RETURN count(r) as count")
                stats['Total Representations'] = result.single()['count']
                
                return stats
                
            except Exception as e:
                # Fallback to basic count
                result = session.run("MATCH (c:SecuritiesContract) RETURN count(c) as count")
                return {
                    'Total Contracts': result.single()['count'],
                    'Stats Error': f"Could not get detailed stats: {e}"
                }
    
    def close(self):
        """Close the database connection"""
        self.driver.close()

def extract_text_from_html(file_path: str) -> str:
    """Extract clean text from HTML contract files"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT contract files"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return "" 