#!/usr/bin/env python3
"""
License GraphRAG Pipeline Runner
Comprehensive system for processing license contracts into knowledge graphs
"""

import os
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from neo4j import GraphDatabase
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import torch

from license_data_models import LicenseContract
from license_extraction import LicenseContractExtractor, import_license_contract_to_neo4j

load_dotenv()

class LicenseGraphRAGPipeline:
    """Complete pipeline for ingesting and querying license contracts"""
    
    def __init__(self, model_path: str = None):
        """Initialize the pipeline with all necessary components"""
        # Initialize Llama model path
        if not model_path:
            model_path = os.getenv("LLAMA_MODEL_PATH", "/path/to/llama-3.3-70b")
        
        if not os.path.exists(model_path):
            raise ValueError(f"Llama model not found at: {model_path}")
        
        # Initialize Llama model and tokenizer for query generation
        print(f"Loading Llama model for query generation from: {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Create pipeline with specified parameters
        self.llm = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_length=4096,
            do_sample=True,
            temperature=0.7,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        self.extractor = LicenseContractExtractor(model_path)
        
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
                "CREATE CONSTRAINT license_contract_title IF NOT EXISTS FOR (c:LicenseContract) REQUIRE c.title IS UNIQUE",
                "CREATE CONSTRAINT licensor_name IF NOT EXISTS FOR (l:Licensor) REQUIRE l.name IS UNIQUE",
                "CREATE CONSTRAINT licensee_name IF NOT EXISTS FOR (le:Licensee) REQUIRE le.name IS UNIQUE",
                "CREATE CONSTRAINT patent_number IF NOT EXISTS FOR (p:Patent) REQUIRE p.patent_number IS UNIQUE",
                "CREATE CONSTRAINT product_name IF NOT EXISTS FOR (pr:Product) REQUIRE pr.product_name IS UNIQUE",
                "CREATE CONSTRAINT territory_name IF NOT EXISTS FOR (t:Territory) REQUIRE t.territory_name IS UNIQUE",
                
                # Create indexes for better query performance
                "CREATE INDEX license_execution_date IF NOT EXISTS FOR (c:LicenseContract) ON (c.execution_date)",
                "CREATE INDEX license_contract_type IF NOT EXISTS FOR (c:LicenseContract) ON (c.contract_type)",
                "CREATE INDEX license_exclusivity IF NOT EXISTS FOR (c:LicenseContract) ON (c.exclusivity_grant_type)",
                "CREATE INDEX license_oem_type IF NOT EXISTS FOR (c:LicenseContract) ON (c.oem_type)",
                "CREATE INDEX license_upfront_payment IF NOT EXISTS FOR (c:LicenseContract) ON (c.upfront_payment)"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    # Constraint may already exist
                    print(f"Schema setup note: {e}")
    
    def ingest_contract(self, contract_text: str, contract_id: str = None) -> LicenseContract:
        """Ingest a single license contract into the knowledge graph"""
        
        # Clean and preprocess the text
        cleaned_text = self._clean_contract_text(contract_text)
        
        # Extract structured data using AI
        contract_data = self.extractor.extract_contract_data(cleaned_text)
        
        # Add metadata
        if contract_id:
            contract_data.title = f"{contract_data.title} ({contract_id})"
        
        # Check if contract already exists
        from license_extraction import check_contract_exists
        if check_contract_exists(contract_data.title, self.driver):
            print(f"Contract '{contract_data.title}' already exists in the database.")
            return contract_data
        
        # Import to Neo4j knowledge graph
        import_license_contract_to_neo4j(contract_data, self.driver)
        
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
                return "No relevant license contracts found in the knowledge graph."
            
            # Use LLM to answer the query based on the data
            prompt = f"""
You are a license law expert analyzing a knowledge graph of license agreements.
Based on the contract data below, please answer the user's question clearly and comprehensively.

RELEVANT CONTRACT DATA:
{json.dumps(contract_data, indent=2, default=str)}

USER QUESTION: {query}

Please provide a detailed answer based on the license agreement information above. Include specific details like:
- Contract titles and dates
- Licensor and licensee names
- Financial terms and upfront payments
- Exclusivity and territory provisions
- Patent and product information
- Legal provisions and warranties
- Any patterns or trends across multiple agreements

If the question involves comparisons, calculations, or analysis across multiple contracts, please provide that analysis.
"""
            
            try:
                # Generate response using Llama pipeline
                response = self.llm(prompt)
                generated_text = response[0]['generated_text']
                
                # Extract the response part (remove the input prompt)
                response_content = generated_text[len(prompt):].strip()
                
                return response_content if response_content else "Sorry, I couldn't generate a response."
            except Exception as e:
                return f"Error generating LLM response: {e}"
                
        except Exception as e:
            return f"Error processing query: {e}. Please try a simpler question or check the database connection."
    
    def _get_relevant_contracts(self, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant license contracts from Neo4j based on the query"""
        
        try:
            # Use AI to generate a targeted Cypher query based on the user's question
            cypher_query = self._generate_cypher_query(query, limit)
            
            print(f"🔍 Generated Cypher query: {cypher_query[:100]}...")
            
            with self.driver.session() as session:
                result = session.run(cypher_query)
                contracts = []
                
                for record in result:
                    contract = {
                        'title': record.get('title'),
                        'contract_type': record.get('contract_type'),
                        'summary': record.get('summary'),
                        'execution_date': str(record['execution_date']) if record.get('execution_date') else None,
                        'effective_date': str(record['effective_date']) if record.get('effective_date') else None,
                        'upfront_payment': record.get('upfront_payment'),
                        'exclusivity_grant_type': record.get('exclusivity_grant_type'),
                        'oem_type': record.get('oem_type'),
                        'licensed_field_of_use': record.get('licensed_field_of_use'),
                        'governing_law': record.get('governing_law'),
                        'jurisdiction': record.get('jurisdiction'),
                        'licensors': [l for l in record.get('licensors', []) if l and l.get('name')],
                        'licensees': [le for le in record.get('licensees', []) if le and le.get('name')],
                        'patents': [p for p in record.get('patents', []) if p and p.get('patent_number')],
                        'products': [pr for pr in record.get('products', []) if pr and pr.get('product_name')],
                        'territories': [t for t in record.get('territories', []) if t and t.get('territory_name')]
                    }
                    contracts.append(contract)
                
                print(f"📊 Retrieved {len(contracts)} relevant contracts")
                return contracts
                
        except Exception as e:
            print(f"❌ Error in AI query generation, using fallback: {e}")
            # Use fallback method that doesn't rely on AI
            return self._get_fallback_contracts(limit)
    
    def _generate_cypher_query(self, query: str, limit: int = 10) -> str:
        """Use AI to generate a targeted Cypher query based on the user's question"""
        
        prompt = f"""
You are a Neo4j Cypher query expert. Generate a Cypher query to retrieve relevant license contracts based on the user's question.

DATABASE SCHEMA:
- LicenseContract nodes: title, contract_type, summary, execution_date, effective_date, upfront_payment, exclusivity_grant_type, oem_type, licensed_field_of_use, governing_law, jurisdiction
- Licensor nodes: name, address, entity_type, jurisdiction
- Licensee nodes: name, address, entity_type, jurisdiction  
- Patent nodes: patent_number, patent_title
- Product nodes: product_name, description
- Territory nodes: territory_name, territory_type

RELATIONSHIPS:
- (Licensor)-[:IS_LICENSOR_OF]->(LicenseContract)
- (Licensee)-[:IS_LICENSEE_OF]->(LicenseContract)
- (LicenseContract)-[:LICENSES]->(Patent)
- (LicenseContract)-[:LICENSES]->(Product)
- (LicenseContract)-[:COVERS_TERRITORY]->(Territory)

USER QUESTION: {query}

Generate ONLY a Cypher query that:
1. Starts with MATCH
2. Retrieves relevant contracts based on the question
3. Includes OPTIONAL MATCH for related entities
4. Uses WHERE clauses for filtering when appropriate
5. Orders by execution_date DESC
6. Limits to {limit} results
7. Returns all contract fields and related entities

CRITICAL REQUIREMENTS FOR RETURN CLAUSE:
- ALWAYS return individual properties explicitly, NOT whole nodes
- Use this exact RETURN format:
  RETURN
    lc.title AS title,
    lc.contract_type AS contract_type,
    lc.summary AS summary,
    lc.execution_date AS execution_date,
    lc.effective_date AS effective_date,
    lc.upfront_payment AS upfront_payment,
    lc.exclusivity_grant_type AS exclusivity_grant_type,
    lc.oem_type AS oem_type,
    lc.licensed_field_of_use AS licensed_field_of_use,
    lc.governing_law AS governing_law,
    lc.jurisdiction AS jurisdiction,
    collect(DISTINCT {{name: licensor.name, address: licensor.address, entity_type: licensor.entity_type, jurisdiction: licensor.jurisdiction}}) AS licensors,
    collect(DISTINCT {{name: licensee.name, address: licensee.address, entity_type: licensee.entity_type, jurisdiction: licensee.jurisdiction}}) AS licensees,
    collect(DISTINCT {{patent_number: patent.patent_number, patent_title: patent.patent_title}}) AS patents,
    collect(DISTINCT {{product_name: product.product_name, description: product.description}}) AS products,
    collect(DISTINCT {{territory_name: territory.territory_name, territory_type: territory.territory_type}}) AS territories

DO NOT return whole nodes like 'lc', 'licensor', 'licensee' - only return their properties as shown above.

IMPORTANT: Return ONLY the Cypher query, no explanations, no markdown formatting, no code blocks.
"""
        
        try:
            # Generate response using Llama pipeline
            response = self.llm(prompt)
            generated_text = response[0]['generated_text']
            
            # Extract the response part (remove the input prompt)
            cypher_query = generated_text[len(prompt):].strip()
            
            # Clean up the response - remove markdown formatting if present
            if cypher_query.startswith('```'):
                lines = cypher_query.split('\n')
                # Remove first and last lines if they're markdown code blocks
                if len(lines) > 2:
                    cypher_query = '\n'.join(lines[1:-1]).strip()
            
            # Remove any remaining markdown or explanations
            if '```' in cypher_query:
                # Extract content between code blocks
                start = cypher_query.find('```') + 3
                end = cypher_query.rfind('```')
                if end > start:
                    cypher_query = cypher_query[start:end].strip()
            
            # Ensure it starts with MATCH
            if not cypher_query.upper().startswith('MATCH'):
                # Try to find MATCH in the response
                match_index = cypher_query.upper().find('MATCH')
                if match_index != -1:
                    cypher_query = cypher_query[match_index:]
                else:
                    raise ValueError("No MATCH clause found in generated query")
            
            # Validate basic Cypher syntax
            if not any(keyword in cypher_query.upper() for keyword in ['MATCH', 'RETURN']):
                raise ValueError("Generated query missing required Cypher keywords")
            
            # Post-process to ensure proper RETURN clause
            cypher_query = self._fix_return_clause(cypher_query)
            
            return cypher_query
            
        except Exception as e:
            print(f"Error generating Cypher query: {e}")
            print(f"Generated query was: {cypher_query if 'cypher_query' in locals() else 'None'}")
            # Return a fallback query
            return self._get_fallback_cypher_query(limit)
    
    def _fix_return_clause(self, cypher_query: str) -> str:
        """Fix the RETURN clause to ensure it returns properties instead of whole nodes"""
        
        # Check if the query returns whole nodes (which would cause null values)
        if any(pattern in cypher_query.upper() for pattern in ['RETURN LC,', 'RETURN LICENSOR,', 'RETURN LICENSEE,', 'RETURN LC ', 'RETURN LICENSOR ', 'RETURN LICENSEE ']):
            print("⚠️  Detected whole node return in generated query, fixing...")
            
            # Extract the MATCH and OPTIONAL MATCH parts
            lines = cypher_query.split('\n')
            match_lines = []
            return_line = None
            
            for line in lines:
                line = line.strip()
                if line.upper().startswith('MATCH') or line.upper().startswith('OPTIONAL MATCH') or line.upper().startswith('WITH'):
                    match_lines.append(line)
                elif line.upper().startswith('RETURN'):
                    return_line = line
                    break
            
            # Build the corrected query with proper RETURN clause
            corrected_query = '\n'.join(match_lines) + '\n' + '''
        RETURN
            lc.title AS title,
            lc.contract_type AS contract_type,
            lc.summary AS summary,
            lc.execution_date AS execution_date,
            lc.effective_date AS effective_date,
            lc.upfront_payment AS upfront_payment,
            lc.exclusivity_grant_type AS exclusivity_grant_type,
            lc.oem_type AS oem_type,
            lc.licensed_field_of_use AS licensed_field_of_use,
            lc.governing_law AS governing_law,
            lc.jurisdiction AS jurisdiction,
            collect(DISTINCT {name: licensor.name, address: licensor.address, entity_type: licensor.entity_type, jurisdiction: licensor.jurisdiction}) AS licensors,
            collect(DISTINCT {name: licensee.name, address: licensee.address, entity_type: licensee.entity_type, jurisdiction: licensee.jurisdiction}) AS licensees,
            collect(DISTINCT {patent_number: patent.patent_number, patent_title: patent.patent_title}) AS patents,
            collect(DISTINCT {product_name: product.product_name, description: product.description}) AS products,
            collect(DISTINCT {territory_name: territory.territory_name, territory_type: territory.territory_type}) AS territories
        ORDER BY lc.execution_date DESC
        LIMIT 10
            '''.strip()
            
            return corrected_query
        
        return cypher_query
    
    def _get_fallback_cypher_query(self, limit: int = 10) -> str:
        """Fallback Cypher query when AI generation fails"""
        return f"""
        MATCH (c:LicenseContract)
        OPTIONAL MATCH (l:Licensor)-[:IS_LICENSOR_OF]->(c)
        OPTIONAL MATCH (le:Licensee)-[:IS_LICENSEE_OF]->(c)
        OPTIONAL MATCH (c)-[:LICENSES]->(p:Patent)
        OPTIONAL MATCH (c)-[:LICENSES]->(pr:Product)
        OPTIONAL MATCH (c)-[:COVERS_TERRITORY]->(t:Territory)
        
        WITH c,
             collect(DISTINCT {{
                 name: l.name, 
                 address: l.address,
                 entity_type: l.entity_type,
                 jurisdiction: l.jurisdiction
             }}) as licensors,
             collect(DISTINCT {{
                 name: le.name,
                 address: le.address,
                 entity_type: le.entity_type,
                 jurisdiction: le.jurisdiction
             }}) as licensees,
             collect(DISTINCT {{
                 patent_number: p.patent_number,
                 patent_title: p.patent_title
             }}) as patents,
             collect(DISTINCT {{
                 product_name: pr.product_name,
                 description: pr.description
             }}) as products,
             collect(DISTINCT {{
                 territory_name: t.territory_name,
                 territory_type: t.territory_type
             }}) as territories
        
        RETURN c.title as title,
               c.contract_type as contract_type,
               c.summary as summary,
               c.execution_date as execution_date,
               c.effective_date as effective_date,
               c.upfront_payment as upfront_payment,
               c.exclusivity_grant_type as exclusivity_grant_type,
               c.oem_type as oem_type,
               c.licensed_field_of_use as licensed_field_of_use,
               c.governing_law as governing_law,
               c.jurisdiction as jurisdiction,
               licensors,
               licensees,
               patents,
               products,
               territories
        ORDER BY c.execution_date DESC
        LIMIT {limit}
        """
    
    def _get_fallback_contracts(self, limit: int = 10) -> List[Dict]:
        """Fallback method to get contracts when query generation fails"""
        with self.driver.session() as session:
            cypher_query = self._get_fallback_cypher_query(limit)
            result = session.run(cypher_query)
            contracts = []
            
            for record in result:
                contract = {
                    'title': record['title'],
                    'contract_type': record['contract_type'],
                    'summary': record['summary'],
                    'execution_date': str(record['execution_date']) if record['execution_date'] else None,
                    'effective_date': str(record['effective_date']) if record['effective_date'] else None,
                    'upfront_payment': record['upfront_payment'],
                    'exclusivity_grant_type': record['exclusivity_grant_type'],
                    'oem_type': record['oem_type'],
                    'licensed_field_of_use': record['licensed_field_of_use'],
                    'governing_law': record['governing_law'],
                    'jurisdiction': record['jurisdiction'],
                    'licensors': [l for l in record['licensors'] if l.get('name')],
                    'licensees': [le for le in record.get('licensees', []) if le.get('name')],
                    'patents': [p for p in record.get('patents', []) if p.get('patent_number')],
                    'products': [pr for pr in record.get('products', []) if pr.get('product_name')],
                    'territories': [t for t in record.get('territories', []) if t.get('territory_name')]
                }
                contracts.append(contract)
            
            return contracts
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get statistics about the license knowledge graph"""
        with self.driver.session() as session:
            try:
                stats = {}
                
                # Count different node types
                node_counts = [
                    ("LicenseContract", "license_contracts"),
                    ("Licensor", "licensors"),
                    ("Licensee", "licensees"),
                    ("Patent", "patents"),
                    ("Product", "products"),
                    ("Territory", "territories")
                ]
                
                for node_type, stat_name in node_counts:
                    result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                    stats[stat_name] = result.single()["count"]
                
                # Count relationships
                relationship_counts = [
                    ("IS_LICENSOR_OF", "licensor_relationships"),
                    ("IS_LICENSEE_OF", "licensee_relationships"),
                    ("LICENSES", "license_relationships"),
                    ("COVERS_TERRITORY", "territory_relationships")
                ]
                
                for rel_type, stat_name in relationship_counts:
                    result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                    stats[stat_name] = result.single()["count"]
                
                return stats
                
            except Exception as e:
                print(f"Error getting database stats: {e}")
                return {"error": str(e)}
    
    def search_contracts(self, search_criteria: Dict[str, Any]) -> List[Dict]:
        """Search contracts using specific criteria"""
        with self.driver.session() as session:
            # Build dynamic query based on search criteria
            query_parts = ["MATCH (c:LicenseContract)"]
            where_conditions = []
            params = {}
            
            # Add filters based on criteria
            if search_criteria.get('licensor_name'):
                query_parts.append("MATCH (l:Licensor)-[:IS_LICENSOR_OF]->(c)")
                where_conditions.append("l.name CONTAINS $licensor_name")
                params['licensor_name'] = search_criteria['licensor_name']
            
            if search_criteria.get('licensee_name'):
                query_parts.append("MATCH (le:Licensee)-[:IS_LICENSEE_OF]->(c)")
                where_conditions.append("le.name CONTAINS $licensee_name")
                params['licensee_name'] = search_criteria['licensee_name']
            
            if search_criteria.get('exclusivity_type'):
                where_conditions.append("c.exclusivity_grant_type = $exclusivity_type")
                params['exclusivity_type'] = search_criteria['exclusivity_type']
            
            if search_criteria.get('min_upfront_payment'):
                where_conditions.append("c.upfront_payment >= $min_upfront_payment")
                params['min_upfront_payment'] = search_criteria['min_upfront_payment']
            
            if search_criteria.get('max_upfront_payment'):
                where_conditions.append("c.upfront_payment <= $max_upfront_payment")
                params['max_upfront_payment'] = search_criteria['max_upfront_payment']
            
            if search_criteria.get('patent_number'):
                query_parts.append("MATCH (c)-[:LICENSES]->(p:Patent)")
                where_conditions.append("p.patent_number CONTAINS $patent_number")
                params['patent_number'] = search_criteria['patent_number']
            
            if search_criteria.get('territory'):
                query_parts.append("MATCH (c)-[:COVERS_TERRITORY]->(t:Territory)")
                where_conditions.append("t.territory_name CONTAINS $territory")
                params['territory'] = search_criteria['territory']
            
            # Add WHERE clause if conditions exist
            if where_conditions:
                query_parts.append("WHERE " + " AND ".join(where_conditions))
            
            # Add return clause
            query_parts.append("""
                RETURN c.title as title,
                       c.summary as summary,
                       c.execution_date as execution_date,
                       c.upfront_payment as upfront_payment,
                       c.exclusivity_grant_type as exclusivity_grant_type
                ORDER BY c.execution_date DESC
                LIMIT 50
            """)
            
            cypher_query = "\n".join(query_parts)
            result = session.run(cypher_query, params)
            
            contracts = []
            for record in result:
                contract = {
                    'title': record['title'],
                    'summary': record['summary'],
                    'execution_date': str(record['execution_date']) if record['execution_date'] else None,
                    'upfront_payment': record['upfront_payment'],
                    'exclusivity_grant_type': record['exclusivity_grant_type']
                }
                contracts.append(contract)
            
            return contracts
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()

def extract_text_from_html(file_path: str) -> str:
    """Extract text content from HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            
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
        print(f"Error extracting text from HTML file {file_path}: {e}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    """Extract text content from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error extracting text from TXT file {file_path}: {e}")
        return "" 