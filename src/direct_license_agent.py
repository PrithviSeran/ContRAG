#!/usr/bin/env python3
"""
Direct License Agent - Simple approach without complex tool calling
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

class DirectLicenseAgent:
    def __init__(self):
        """Initialize the direct license agent"""
        # Initialize Google API key
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=google_api_key
        )
        
        # Database connection
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
    
    def get_contract_data(self):
        """Get license contract data directly from database"""
        try:
            driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with driver.session() as session:
                result = session.run("""
                    MATCH (c:LicenseContract)
                    OPTIONAL MATCH (l:Licensor)-[:IS_LICENSOR_OF]->(c)
                    OPTIONAL MATCH (le:Licensee)-[:IS_LICENSEE_OF]->(c)
                    OPTIONAL MATCH (c)-[:LICENSES]->(p:Patent)
                    OPTIONAL MATCH (c)-[:LICENSES]->(pr:Product)
                    OPTIONAL MATCH (c)-[:COVERS_TERRITORY]->(t:Territory)
                    
                    WITH c,
                         collect(DISTINCT {name: l.name, address: l.address, entity_type: l.entity_type}) as licensors,
                         collect(DISTINCT {name: le.name, address: le.address, entity_type: le.entity_type}) as licensees,
                         collect(DISTINCT {patent_number: p.patent_number, patent_title: p.patent_title}) as patents,
                         collect(DISTINCT {product_name: pr.product_name, description: pr.description}) as products,
                         collect(DISTINCT {territory_name: t.territory_name, territory_type: t.territory_type}) as territories
                    
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
                    LIMIT 1
                """)
                
                record = result.single()
                if record:
                    return {
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
                        'licensors': record['licensors'],
                        'licensees': record['licensees'],
                        'patents': record['patents'],
                        'products': record['products'],
                        'territories': record['territories']
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
        """Format license contract data for display"""
        if not contract_data:
            return "No license contract data available."
        
        info_parts = []
        
        # Basic info
        info_parts.append(f"TITLE: {contract_data.get('title', 'Not specified')}")
        info_parts.append(f"TYPE: {contract_data.get('contract_type', 'Not specified')}")
        info_parts.append(f"SUMMARY: {contract_data.get('summary', 'Not specified')}")
        info_parts.append(f"EXECUTION DATE: {contract_data.get('execution_date', 'Not specified')}")
        info_parts.append(f"EFFECTIVE DATE: {contract_data.get('effective_date', 'Not specified')}")
        info_parts.append(f"EXCLUSIVITY: {contract_data.get('exclusivity_grant_type', 'Not specified')}")
        info_parts.append(f"OEM TYPE: {contract_data.get('oem_type', 'Not specified')}")
        info_parts.append(f"FIELD OF USE: {contract_data.get('licensed_field_of_use', 'Not specified')}")
        info_parts.append(f"GOVERNING LAW: {contract_data.get('governing_law', 'Not specified')}")
        info_parts.append(f"JURISDICTION: {contract_data.get('jurisdiction', 'Not specified')}")
        
        # Financial terms
        upfront_payment = contract_data.get('upfront_payment')
        if upfront_payment:
            info_parts.append(f"UPFRONT PAYMENT: ${upfront_payment:,.2f}")
        else:
            info_parts.append("UPFRONT PAYMENT: Not specified")
        
        # Licensors
        licensors = contract_data.get('licensors', [])
        if licensors and any(l.get('name') for l in licensors):
            info_parts.append("\nLICENSORS:")
            for licensor in licensors:
                if licensor.get('name'):
                    entity_type = licensor.get('entity_type', '')
                    entity_info = f" ({entity_type})" if entity_type else ""
                    info_parts.append(f"- {licensor['name']}{entity_info}")
        else:
            info_parts.append("\nLICENSORS: None found")
        
        # Licensees
        licensees = contract_data.get('licensees', [])
        if licensees and any(l.get('name') for l in licensees):
            info_parts.append("\nLICENSEES:")
            for licensee in licensees:
                if licensee.get('name'):
                    entity_type = licensee.get('entity_type', '')
                    entity_info = f" ({entity_type})" if entity_type else ""
                    info_parts.append(f"- {licensee['name']}{entity_info}")
        else:
            info_parts.append("\nLICENSEES: None found")
        
        # Patents
        patents = contract_data.get('patents', [])
        if patents and any(p.get('patent_number') for p in patents):
            info_parts.append("\nLICENSED PATENTS:")
            for patent in patents:
                if patent.get('patent_number'):
                    patent_number = patent['patent_number']
                    patent_title = patent.get('patent_title', '')
                    title_info = f" - {patent_title}" if patent_title else ""
                    info_parts.append(f"- Patent {patent_number}{title_info}")
        else:
            info_parts.append("\nLICENSED PATENTS: None found")
        
        # Products
        products = contract_data.get('products', [])
        if products and any(p.get('product_name') for p in products):
            info_parts.append("\nLICENSED PRODUCTS:")
            for product in products:
                if product.get('product_name'):
                    product_name = product['product_name']
                    description = product.get('description', '')
                    desc_info = f" - {description}" if description else ""
                    info_parts.append(f"- {product_name}{desc_info}")
        else:
            info_parts.append("\nLICENSED PRODUCTS: None found")
        
        # Territories
        territories = contract_data.get('territories', [])
        if territories and any(t.get('territory_name') for t in territories):
            info_parts.append("\nLICENSED TERRITORIES:")
            for territory in territories:
                if territory.get('territory_name'):
                    territory_name = territory['territory_name']
                    territory_type = territory.get('territory_type', '')
                    type_info = f" ({territory_type})" if territory_type else ""
                    info_parts.append(f"- {territory_name}{type_info}")
        else:
            info_parts.append("\nLICENSED TERRITORIES: None found")
        
        return "\n".join(info_parts)
    
    def answer_question(self, question):
        """Answer a question about the license contract"""
        
        # Get contract data
        contract_data = self.get_contract_data()
        
        if not contract_data:
            return "No license contract found in the database. Please ingest a contract first."
        
        # Format contract information
        contract_info = self.format_contract_info(contract_data)
        
        # Create prompt for LLM
        prompt = f"""
You are analyzing a license agreement. Based on the contract information below, please answer the user's question clearly and specifically.

CONTRACT INFORMATION:
{contract_info}

USER QUESTION: {question}

Please provide a specific answer based on the license contract information above. If the requested information is not available in the contract data, please say so clearly.
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content if response.content else "Sorry, I couldn't generate a response."
        except Exception as e:
            return f"Error generating response: {e}"

def create_direct_license_agent():
    """Create a direct license agent"""
    return DirectLicenseAgent()

# Test function
def test_direct_agent():
    """Test the direct license agent"""
    agent = DirectLicenseAgent()
    
    print("🚀 Testing Direct License Agent...")
    
    # First, let's see what contract data we have
    contract_data = agent.get_contract_data()
    if contract_data:
        print("✅ License contract data found!")
        print("\n📋 License Contract Information:")
        print(agent.format_contract_info(contract_data))
    else:
        print("❌ No license contract data found in database")
        return
    
    # Test questions
    test_questions = [
        "What is the title of this license contract?",
        "Who are the licensor and licensee in this agreement?",
        "What patents are licensed under this agreement?",
        "What is the exclusivity type of this license?",
        "What is the upfront payment amount?",
        "What products are licensed under this agreement?",
        "What territories are covered by this license?",
        "What is the governing law for this agreement?"
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