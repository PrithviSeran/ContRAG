#!/usr/bin/env python3
"""
Direct Securities Agent - Simple approach without complex tool calling
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

class DirectSecuritiesAgent:
    def __init__(self):
        """Initialize the direct securities agent"""
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        
        # Database connection
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
    
    def get_contract_data(self):
        """Get contract data directly from database"""
        try:
            driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with driver.session() as session:
                result = session.run("""
                    MATCH (c:SecuritiesContract)
                    OPTIONAL MATCH (c)<-[:PARTY_TO]-(p:Party)
                    OPTIONAL MATCH (c)-[:ISSUES_SECURITY]->(s:Security)
                    OPTIONAL MATCH (c)-[:HAS_CLOSING_CONDITION]->(cc:ClosingCondition)
                    
                    WITH c, 
                         collect(DISTINCT {name: p.name, role: p.role, entity_type: p.entity_type}) as parties,
                         collect(DISTINCT {type: s.security_type, par_value: s.par_value}) as securities,
                         collect(DISTINCT {description: cc.description, is_waivable: cc.is_waivable}) as conditions
                    
                    RETURN c.title as title,
                           c.contract_type as contract_type,
                           c.summary as summary,
                           c.execution_date as execution_date,
                           c.registration_status as registration_status,
                           parties,
                           securities,
                           conditions
                    ORDER BY c.execution_date DESC
                    LIMIT 1
                """)
                
                record = result.single()
                if record:
                    return {
                        'title': record['title'],
                        'contract_type': record['contract_type'],
                        'summary': record['summary'],
                        'execution_date': str(record['execution_date']) if record['execution_date'] else None,
                        'registration_status': record['registration_status'],
                        'parties': record['parties'],
                        'securities': record['securities'],
                        'conditions': record['conditions']
                    }
                else:
                    return None
        except Exception as e:
            print(f"Database error: {e}")
            return None
        finally:
            if 'driver' in locals():
                driver.close()
    
    def format_contract_info(self, contract_data):
        """Format contract data for display"""
        if not contract_data:
            return "No contract data available."
        
        info_parts = []
        
        # Basic info
        info_parts.append(f"TITLE: {contract_data.get('title', 'Not specified')}")
        info_parts.append(f"TYPE: {contract_data.get('contract_type', 'Not specified')}")
        info_parts.append(f"SUMMARY: {contract_data.get('summary', 'Not specified')}")
        info_parts.append(f"EXECUTION DATE: {contract_data.get('execution_date', 'Not specified')}")
        info_parts.append(f"REGISTRATION STATUS: {contract_data.get('registration_status', 'Not specified')}")
        
        # Parties
        parties = contract_data.get('parties', [])
        if parties and any(p.get('name') for p in parties):
            info_parts.append("\nPARTIES:")
            for party in parties:
                if party.get('name'):
                    role = party.get('role', 'Unknown role')
                    entity_type = party.get('entity_type', '')
                    entity_info = f" ({entity_type})" if entity_type else ""
                    info_parts.append(f"- {party['name']} - {role}{entity_info}")
        else:
            info_parts.append("\nPARTIES: None found")
        
        # Securities
        securities = contract_data.get('securities', [])
        if securities and any(s.get('type') for s in securities):
            info_parts.append("\nSECURITIES:")
            for security in securities:
                if security.get('type'):
                    sec_type = security['type']
                    par_value = security.get('par_value')
                    par_info = f" (Par value: ${par_value})" if par_value else ""
                    info_parts.append(f"- {sec_type}{par_info}")
        else:
            info_parts.append("\nSECURITIES: None found")
        
        # Closing conditions
        conditions = contract_data.get('conditions', [])
        if conditions and any(c.get('description') for c in conditions):
            info_parts.append("\nCLOSING CONDITIONS:")
            for condition in conditions:
                if condition.get('description'):
                    desc = condition['description']
                    waivable = " (Waivable)" if condition.get('is_waivable') else " (Non-waivable)"
                    info_parts.append(f"- {desc}{waivable}")
        else:
            info_parts.append("\nCLOSING CONDITIONS: None found")
        
        return "\n".join(info_parts)
    
    def answer_question(self, question):
        """Answer a question about the securities contract"""
        
        # Get contract data
        contract_data = self.get_contract_data()
        
        if not contract_data:
            return "No securities contract found in the database. Please ingest a contract first."
        
        # Format contract information
        contract_info = self.format_contract_info(contract_data)
        
        # Create prompt for LLM
        prompt = f"""
You are analyzing a securities purchase agreement. Based on the contract information below, please answer the user's question clearly and specifically.

CONTRACT INFORMATION:
{contract_info}

USER QUESTION: {question}

Please provide a specific answer based on the contract information above. If the requested information is not available in the contract data, please say so clearly.
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content if response.content else "Sorry, I couldn't generate a response."
        except Exception as e:
            return f"Error generating response: {e}"

def create_direct_securities_agent():
    """Create a direct securities agent"""
    return DirectSecuritiesAgent()

# Test function
def test_direct_agent():
    """Test the direct agent"""
    agent = DirectSecuritiesAgent()
    
    print("🚀 Testing Direct Securities Agent...")
    
    # First, let's see what contract data we have
    contract_data = agent.get_contract_data()
    if contract_data:
        print("✅ Contract data found!")
        print("\n📋 Contract Information:")
        print(agent.format_contract_info(contract_data))
    else:
        print("❌ No contract data found in database")
        return
    
    # Test questions
    test_questions = [
        "What is the title of this securities contract?",
        "Who are the parties involved in this agreement?",
        "What types of securities are being issued?",
        "What are the closing conditions mentioned?",
        "What is the registration status?"
    ]
    
    print(f"\n{'='*60}")
    print("TESTING QUESTIONS")
    print("="*60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 Question {i}: {question}")
        try:
            answer = agent.answer_question(question)
            print(f"📊 Answer: {answer}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 40)

if __name__ == "__main__":
    test_direct_agent() 