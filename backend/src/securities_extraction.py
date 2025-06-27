import os
from datetime import datetime
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
import json
import re

from .securities_data_models import (
    SecuritiesContract, Party, Security, ClosingConditions, 
    RegistrationRights, ResaleRestrictions, Representation,
    SecurityType, PartyRole, RegistrationStatus
)

class SecuritiesContractExtractor:
    """Extract structured data from securities purchase agreements"""
    
    def __init__(self):
        # Use gemini-1.5-flash which has higher rate limits than gemini-2.0-flash
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001",
            temperature=0.1,  # Lower temperature for more consistent extraction
            max_tokens=8192   # Sufficient for most contracts
        )
        self.parser = PydanticOutputParser(pydantic_object=SecuritiesContract)
    
    def extract_contract_data(self, contract_text: str) -> SecuritiesContract:
        """Extract structured securities contract data from text"""
        
        # Detect contract type for better extraction
        contract_type = self._detect_contract_type(contract_text)
        
        # Use specialized prompt based on contract type
        if "license" in contract_type.lower():
            return self._extract_license_agreement(contract_text)
        elif "employment" in contract_type.lower() or "letter" in contract_type.lower():
            return self._extract_employment_agreement(contract_text)
        elif "settlement" in contract_type.lower():
            return self._extract_settlement_agreement(contract_text)
        elif "lease" in contract_type.lower():
            return self._extract_lease_agreement(contract_text)
        else:
            return self._extract_securities_agreement(contract_text)
    
    def _detect_contract_type(self, contract_text: str) -> str:
        """Detect the type of contract from the text"""
        text_lower = contract_text.lower()
        
        if any(term in text_lower for term in ["license agreement", "licensing", "intellectual property"]):
            return "License Agreement"
        elif any(term in text_lower for term in ["employment agreement", "employment letter", "letter agreement"]):
            return "Employment Agreement"
        elif any(term in text_lower for term in ["settlement agreement", "mutual release"]):
            return "Settlement Agreement"
        elif any(term in text_lower for term in ["lease agreement", "supplemental lease", "landlord", "tenant"]):
            return "Lease Agreement"
        elif any(term in text_lower for term in ["securities purchase", "stock purchase", "investment agreement"]):
            return "Securities Purchase Agreement"
        elif any(term in text_lower for term in ["warrant agreement", "warrant purchase"]):
            return "Warrant Agreement"
        elif any(term in text_lower for term in ["rights agreement", "investor rights"]):
            return "Rights Agreement"
        else:
            return "Securities Agreement"
    
    def _extract_securities_agreement(self, contract_text: str) -> SecuritiesContract:
        """Extract securities purchase agreement data with enhanced parsing"""
        
        # First, try to extract specific information using rule-based extraction
        rule_based_data = self._extract_with_rules(contract_text)
        
        # Enhanced prompt with more specific instructions and examples
        prompt_template = PromptTemplate(
            template="""
            You are an expert legal AI specializing in securities law and corporate finance.
            Extract SPECIFIC information from this securities agreement. Be PRECISE and look for exact terms.
            
            CONTRACT TEXT:
            {contract_text}
            
            CRITICAL EXTRACTION REQUIREMENTS:
            
            1. EXECUTION DATE - Look for phrases like:
               - "executed on", "dated as of", "this ___ day of", "effective date"
               - Extract the EXACT date in YYYY-MM-DD format
            
            2. FINANCIAL TERMS - Look for:
               - "purchase price", "total offering", "aggregate purchase price" 
               - "$X per share", "consideration of $", "payment of $"
               - Extract EXACT dollar amounts as numbers (without $ symbol)
            
            3. SECURITIES DETAILS - Identify:
               - "shares of common stock", "preferred stock", "warrants", "convertible"
               - Number of shares: "X shares", "up to X shares"
               - Par value: "par value of $", "no par value"
            
            4. PARTIES - Extract:
               - Company name (often after "between" or "by and between")
               - Entity type: "Inc.", "LLC", "Corporation", "Ltd."
               - State of incorporation: "Delaware corporation", "Nevada LLC"
               - Investor/Purchaser names
            
            5. CLOSING CONDITIONS - Look for:
               - "conditions precedent", "closing conditions", "subject to"
               - Due diligence, regulatory approvals, board approvals
            
            6. CONTRACT TYPE - Determine exact type:
               - Securities Purchase Agreement, Stock Purchase Agreement
               - Warrant Agreement, Rights Agreement, Investment Agreement
               - License Agreement, Employment Agreement, Settlement Agreement
            
            RULES:
            - If you find a date, extract it in YYYY-MM-DD format
            - If you find dollar amounts, extract as numbers only
            - If parsing fails partially, still extract what you can find
            - Always provide a meaningful summary of the transaction
            
            {format_instructions}
            """,
            input_variables=["contract_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        prompt = prompt_template.format(contract_text=contract_text[:15000])
        
        try:
            response = self.llm.invoke(prompt)
            result = self.parser.parse(response.content)
            
            # Enhance with rule-based data if AI parsing missed anything
            if not result.execution_date and rule_based_data.get('execution_date'):
                result.execution_date = rule_based_data['execution_date']
            
            if not result.total_offering_amount and rule_based_data.get('total_offering_amount'):
                result.total_offering_amount = rule_based_data['total_offering_amount']
            
            if not result.parties and rule_based_data.get('parties'):
                result.parties = rule_based_data['parties']
            
            # Add securities if AI didn't extract them
            if not result.securities and rule_based_data.get('securities'):
                securities_list = []
                for sec_data in rule_based_data['securities']:
                    try:
                        security = Security(
                            security_type=SecurityType(sec_data.get('security_type', 'common_stock')),
                            number_of_shares=sec_data.get('number_of_shares'),
                            purchase_price_per_share=sec_data.get('purchase_price_per_share'),
                            exercise_price=sec_data.get('exercise_price')
                        )
                        securities_list.append(security)
                    except ValueError:
                        # Skip invalid security types
                        continue
                result.securities = securities_list
            
            # Add closing conditions if AI didn't extract them
            if not result.closing_conditions and rule_based_data.get('closing_conditions'):
                conditions_list = []
                for cond_data in rule_based_data['closing_conditions']:
                    condition = ClosingConditions(
                        condition_description=cond_data['condition_description'],
                        is_waivable=cond_data.get('is_waivable', False),
                        responsible_party=cond_data.get('responsible_party', 'mutual')
                    )
                    conditions_list.append(condition)
                result.closing_conditions = conditions_list
            
            # Ensure we have a proper summary
            if not result.summary or "Basic extraction" in result.summary:
                result.summary = self._generate_contract_summary(contract_text, result)
            
            return result
            
        except Exception as e:
            # Enhanced fallback with rule-based extraction
            return self._create_enhanced_basic_contract(contract_text, "Securities Purchase Agreement", str(e), rule_based_data)
    
    def _extract_license_agreement(self, contract_text: str) -> SecuritiesContract:
        """Extract license agreement data with enhanced parsing"""
        
        # Extract license-specific information using rules
        license_data = self._extract_license_with_rules(contract_text)
        
        prompt_template = PromptTemplate(
            template="""
            You are analyzing a LICENSE AGREEMENT. Extract SPECIFIC information:
            
            CONTRACT TEXT:
            {contract_text}
            
            CRITICAL EXTRACTION REQUIREMENTS:
            
            1. PARTIES - Identify:
               - Licensor: Company granting the license
               - Licensee: Company receiving the license
               - Entity types and jurisdictions
            
            2. INTELLECTUAL PROPERTY - Look for:
               - Patents: "Patent No.", "U.S. Patent", "patent application"
               - Technology: "know-how", "proprietary technology", "trade secrets"
               - Trademarks: specific product names, brand names
               - Field of use: therapeutic areas, indications
            
            3. FINANCIAL TERMS - Extract:
               - Upfront payments: "upfront fee", "initial payment"
               - Royalty rates: "X% royalty", "royalty of X percent"
               - Milestone payments: "upon achieving", "development milestones"
               - Minimum royalties: "minimum annual royalty"
            
            4. TERRITORY AND SCOPE:
               - Geographic territory: "worldwide", "United States", specific countries
               - Field of use: "human therapeutics", specific diseases/conditions
               - Exclusivity: "exclusive", "non-exclusive", "co-exclusive"
            
            5. KEY DATES:
               - Execution date, effective date
               - Term duration: "for a period of X years"
               - Expiration dates, renewal options
            
            6. OBLIGATIONS AND CONDITIONS:
               - Development milestones and timelines
               - Regulatory approval requirements
               - Commercialization obligations
               - Termination conditions
            
            Extract EXACT amounts, percentages, and dates. Be precise with party names and IP descriptions.
            
            {format_instructions}
            """,
            input_variables=["contract_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        prompt = prompt_template.format(contract_text=contract_text[:15000])
        
        try:
            response = self.llm.invoke(prompt)
            result = self.parser.parse(response.content)
            result.contract_type = "License Agreement"
            
            # Enhance with rule-based data
            if not result.execution_date and license_data.get('execution_date'):
                result.execution_date = license_data['execution_date']
            
            if not result.total_offering_amount and license_data.get('upfront_payment'):
                result.total_offering_amount = license_data['upfront_payment']
            
            if not result.parties and license_data.get('parties'):
                result.parties = license_data['parties']
            
            # Add securities and conditions from rule-based extraction
            if not result.securities and license_data.get('securities'):
                securities_list = []
                for sec_data in license_data['securities']:
                    try:
                        security = Security(
                            security_type=SecurityType(sec_data.get('security_type', 'common_stock')),
                            number_of_shares=sec_data.get('number_of_shares'),
                            purchase_price_per_share=sec_data.get('purchase_price_per_share'),
                            exercise_price=sec_data.get('exercise_price')
                        )
                        securities_list.append(security)
                    except ValueError:
                        continue
                result.securities = securities_list
            
            if not result.closing_conditions and license_data.get('closing_conditions'):
                conditions_list = []
                for cond_data in license_data['closing_conditions']:
                    condition = ClosingConditions(
                        condition_description=cond_data['condition_description'],
                        is_waivable=cond_data.get('is_waivable', False),
                        responsible_party=cond_data.get('responsible_party', 'mutual')
                    )
                    conditions_list.append(condition)
                result.closing_conditions = conditions_list
            
            # Generate better summary
            if not result.summary or "Basic extraction" in result.summary:
                result.summary = self._generate_license_summary(contract_text, result, license_data)
            
            return result
            
        except Exception as e:
            return self._create_enhanced_basic_contract(contract_text, "License Agreement", str(e), license_data)
    
    def _extract_employment_agreement(self, contract_text: str) -> SecuritiesContract:
        """Extract employment agreement data"""
        
        # For employment agreements, extract basic info
        title_match = re.search(r'employment.*?agreement|letter.*?agreement', contract_text, re.IGNORECASE)
        title = title_match.group(0) if title_match else "Employment Agreement"
        
        return SecuritiesContract(
            title=title,
            contract_type="Employment Agreement",
            summary="Employment agreement or letter agreement between company and employee"
        )
    
    def _extract_settlement_agreement(self, contract_text: str) -> SecuritiesContract:
        """Extract settlement agreement data"""
        
        title_match = re.search(r'settlement.*?agreement|mutual.*?release', contract_text, re.IGNORECASE)
        title = title_match.group(0) if title_match else "Settlement Agreement"
        
        return SecuritiesContract(
            title=title,
            contract_type="Settlement Agreement",
            summary="Settlement agreement and mutual release between parties"
        )
    
    def _extract_lease_agreement(self, contract_text: str) -> SecuritiesContract:
        """Extract lease agreement data"""
        
        title_match = re.search(r'supplemental.*?lease|lease.*?agreement', contract_text, re.IGNORECASE)
        title = title_match.group(0) if title_match else "Lease Agreement"
        
        return SecuritiesContract(
            title=title,
            contract_type="Lease Agreement",
            summary="Lease agreement or supplemental lease between landlord and tenant"
        )
    
    def _create_basic_contract(self, contract_text: str, contract_type: str, error_msg: str) -> SecuritiesContract:
        """Create a basic contract when full parsing fails"""
        
        # Try to extract basic information
        title_patterns = [
            r'(?:this\s+)?"?([^"]*agreement[^"]*)"?',
            r'title[:\s]*([^\n]+)',
            r'^([A-Z][A-Z\s]+AGREEMENT)',
        ]
        
        title = contract_type
        for pattern in title_patterns:
            match = re.search(pattern, contract_text[:1000], re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                break
        
        # Extract parties if possible
        parties = []
        party_patterns = [
            r'between\s+([^,]+),?\s+.*?and\s+([^,\n]+)',
            r'by and between\s+([^,]+),?\s+.*?and\s+([^,\n]+)',
        ]
        
        for pattern in party_patterns:
            match = re.search(pattern, contract_text[:2000], re.IGNORECASE)
            if match:
                party1 = match.group(1).strip()
                party2 = match.group(2).strip()
                
                # Try to determine roles
                if any(term in party1.lower() for term in ["abeona", "access", "therapeutics"]):
                    parties.append(Party(name=party1, role=PartyRole.ISSUER))
                    parties.append(Party(name=party2, role=PartyRole.PURCHASER))
                else:
                    parties.append(Party(name=party1, role=PartyRole.PURCHASER))
                    parties.append(Party(name=party2, role=PartyRole.ISSUER))
                break
        
        return SecuritiesContract(
            title=title,
            contract_type=contract_type,
            summary=f"Basic extraction - full parsing failed: {error_msg[:100]}...",
            parties=parties
        )
    
    def _extract_with_rules(self, contract_text: str) -> dict:
        """Rule-based extraction for specific information that LLMs often miss"""
        rule_data = {}
        
        # Date extraction patterns
        date_patterns = [
            r'(?:executed|dated|effective|entered into)\s+(?:as\s+of\s+)?(?:on\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'this\s+(\d{1,2})\w{0,2}\s+day\s+of\s+([A-Za-z]+),?\s+(\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'as\s+of\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'made.*?(?:as\s+of\s+|on\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, contract_text[:3000], re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1) if match.groups() else match.group(0)
                    date_str = date_str.strip()
                    
                    # Try to parse various date formats
                    date_formats = [
                        '%B %d, %Y',      # "January 1, 2023"
                        '%B %d %Y',       # "January 1 2023"
                        '%m/%d/%Y',       # "1/1/2023"
                        '%Y-%m-%d',       # "2023-01-01"
                        '%d %B %Y',       # "1 January 2023"
                        '%B %Y',          # "January 2023" (day defaults to 1)
                    ]
                    
                    for fmt in date_formats:
                        try:
                            if fmt == '%B %Y':
                                # For month-year only, add day 1
                                parsed_date = datetime.strptime(f"1 {date_str}", f'%d {fmt}')
                            else:
                                parsed_date = datetime.strptime(date_str, fmt)
                            rule_data['execution_date'] = parsed_date.date()
                            break
                        except ValueError:
                            continue
                    
                    # If we found a date, break from the pattern loop
                    if 'execution_date' in rule_data:
                        break
                        
                except Exception:
                    continue
        
        # Financial amount extraction
        amount_patterns = [
            r'aggregate\s+purchase\s+price.*?\$\s*([\d,]+(?:\.\d{2})?)',
            r'total\s+(?:offering|purchase\s+price).*?\$\s*([\d,]+(?:\.\d{2})?)',
            r'purchase\s+price.*?is\s+\$\s*([\d,]+(?:\.\d{2})?)',
            r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|mil)',
            r'consideration.*?\$\s*([\d,]+(?:\.\d{2})?)',
            r'(?:for|is)\s+\$\s*([\d,]+(?:\.\d{2})?)',
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, contract_text[:5000], re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    # Convert millions to actual amount
                    if 'million' in match.group(0).lower():
                        amount *= 1000000
                    rule_data['total_offering_amount'] = amount
                    break
                except ValueError:
                    continue
        
        # Party extraction using more sophisticated patterns
        party_patterns = [
            r'(?:between|by and between)\s+([^,\n]+?),?\s+a\s+([^,\n]*?)\s+(?:corporation|company|llc|inc)',
            r'([A-Z][A-Za-z\s&]+(?:Inc|LLC|Corporation|Corp)\.?)',
        ]
        
        parties = []
        seen_party_names = set()
        
        for pattern in party_patterns:
            matches = re.finditer(pattern, contract_text[:2000], re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    name = match.group(1).strip()
                    entity_info = match.group(2).strip()
                    
                    # Skip if we've already seen this party name
                    if name.lower() in seen_party_names:
                        continue
                    seen_party_names.add(name.lower())
                    
                    # Determine entity type and jurisdiction
                    entity_type = None
                    jurisdiction = None
                    
                    if 'delaware' in entity_info.lower():
                        jurisdiction = 'Delaware'
                    elif 'nevada' in entity_info.lower():
                        jurisdiction = 'Nevada'
                    elif 'new york' in entity_info.lower():
                        jurisdiction = 'New York'
                    
                    if any(term in entity_info.lower() for term in ['corp', 'corporation']):
                        entity_type = 'Corporation'
                    elif 'llc' in entity_info.lower():
                        entity_type = 'LLC'
                    
                    # Determine role
                    role = PartyRole.PURCHASER
                    if any(term in name.lower() for term in ['abeona', 'access', 'therapeutics']):
                        role = PartyRole.ISSUER
                    
                    parties.append(Party(
                        name=name,
                        role=role,
                        entity_type=entity_type,
                        jurisdiction=jurisdiction
                    ))
                else:
                    name = match.group(1).strip()
                    if (len(name) > 5 and 
                        name.lower() not in seen_party_names and
                        not any(skip in name.lower() for skip in ['pursuant', 'whereas', 'section', 'agreement', 'company agrees'])):
                        
                        seen_party_names.add(name.lower())
                        role = PartyRole.PURCHASER
                        if any(term in name.lower() for term in ['abeona', 'access', 'therapeutics']):
                            role = PartyRole.ISSUER
                        parties.append(Party(name=name, role=role))
        
        if parties:
            rule_data['parties'] = parties
        
        # Securities information extraction
        securities_info = self._extract_securities_info(contract_text)
        if securities_info:
            rule_data['securities'] = securities_info
        
        # Closing conditions extraction
        conditions = self._extract_closing_conditions(contract_text)
        if conditions:
            rule_data['closing_conditions'] = conditions
        
        return rule_data
    
    def _extract_securities_info(self, contract_text: str) -> List[dict]:
        """Extract securities information using rule-based patterns"""
        securities = []
        
        # Common stock patterns
        stock_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s+shares?\s+of\s+common\s+stock',
            r'common\s+stock.*?(\d{1,3}(?:,\d{3})*)\s+shares?',
            r'(\d{1,3}(?:,\d{3})*)\s+shares?\s+of.*?common',
        ]
        
        for pattern in stock_patterns:
            match = re.search(pattern, contract_text[:5000], re.IGNORECASE)
            if match:
                try:
                    shares_str = match.group(1).replace(',', '')
                    shares = int(shares_str)
                    securities.append({
                        'security_type': 'common_stock',
                        'number_of_shares': shares
                    })
                    break
                except ValueError:
                    continue
        
        # Preferred stock patterns
        preferred_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s+shares?\s+of\s+preferred\s+stock',
            r'preferred\s+stock.*?(\d{1,3}(?:,\d{3})*)\s+shares?',
            r'series\s+[A-Z]\s+preferred.*?(\d{1,3}(?:,\d{3})*)\s+shares?',
        ]
        
        for pattern in preferred_patterns:
            match = re.search(pattern, contract_text[:5000], re.IGNORECASE)
            if match:
                try:
                    shares_str = match.group(1).replace(',', '')
                    shares = int(shares_str)
                    securities.append({
                        'security_type': 'preferred_stock',
                        'number_of_shares': shares
                    })
                    break
                except ValueError:
                    continue
        
        # Warrant patterns
        warrant_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s+warrants?',
            r'warrant.*?(\d{1,3}(?:,\d{3})*)',
            r'exercise.*?(\d{1,3}(?:,\d{3})*)\s+warrants?',
        ]
        
        for pattern in warrant_patterns:
            match = re.search(pattern, contract_text[:5000], re.IGNORECASE)
            if match:
                try:
                    warrants_str = match.group(1).replace(',', '')
                    warrants = int(warrants_str)
                    
                    # Look for exercise price
                    exercise_price = None
                    exercise_pattern = r'exercise\s+price.*?\$\s*([\d,]+(?:\.\d{2})?)'
                    exercise_match = re.search(exercise_pattern, contract_text[:5000], re.IGNORECASE)
                    if exercise_match:
                        try:
                            exercise_price = float(exercise_match.group(1).replace(',', ''))
                        except ValueError:
                            pass
                    
                    securities.append({
                        'security_type': 'warrant',
                        'number_of_shares': warrants,
                        'exercise_price': exercise_price
                    })
                    break
                except ValueError:
                    continue
        
        # Price per share extraction
        price_patterns = [
            r'\$\s*([\d,]+(?:\.\d{2})?)\s+per\s+share',
            r'purchase\s+price.*?\$\s*([\d,]+(?:\.\d{2})?)\s+per\s+share',
            r'price\s+of\s+\$\s*([\d,]+(?:\.\d{2})?)\s+per\s+share',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, contract_text[:5000], re.IGNORECASE)
            if match:
                try:
                    price = float(match.group(1).replace(',', ''))
                    # Add price to the most recent security
                    if securities:
                        securities[-1]['purchase_price_per_share'] = price
                    break
                except ValueError:
                    continue
        
        return securities
    
    def _extract_closing_conditions(self, contract_text: str) -> List[dict]:
        """Extract closing conditions using rule-based patterns"""
        conditions = []
        
        condition_patterns = [
            r'(?:conditions? precedent|closing conditions?).*?(?:includes?|are):?\s*([^.]*)',
            r'(?:subject to|contingent upon).*?([^.]*)',
            r'the closing.*?(?:subject to|contingent upon).*?([^.]*)',
        ]
        
        for pattern in condition_patterns:
            matches = re.finditer(pattern, contract_text[:8000], re.IGNORECASE | re.DOTALL)
            for match in matches:
                condition_text = match.group(1).strip()
                
                # Split on common separators and clean up
                condition_items = re.split(r'[;,]\s*(?:\([a-z]\)|[0-9]+\.)', condition_text)
                
                for item in condition_items:
                    item = item.strip()
                    if len(item) > 10 and len(item) < 200:  # Reasonable length
                        conditions.append({
                            'condition_description': item,
                            'is_waivable': 'waivable' in item.lower(),
                            'responsible_party': self._identify_responsible_party(item)
                        })
        
        # Common specific conditions
        specific_conditions = [
            ('due diligence', 'completion of due diligence'),
            ('board approval', 'board of directors approval'),
            ('shareholder approval', 'shareholder approval'),
            ('regulatory approval', 'regulatory approval'),
            ('sec approval', 'SEC approval'),
            ('legal opinion', 'delivery of legal opinion'),
            ('audit', 'completion of audit'),
        ]
        
        for keyword, description in specific_conditions:
            if keyword in contract_text.lower():
                conditions.append({
                    'condition_description': description,
                    'is_waivable': False,  # Default to non-waivable
                    'responsible_party': 'company' if keyword in ['board approval', 'audit'] else 'third_party'
                })
        
        return conditions[:10]  # Limit to 10 conditions
    
    def _identify_responsible_party(self, condition_text: str) -> str:
        """Identify which party is responsible for a condition"""
        text_lower = condition_text.lower()
        
        if any(term in text_lower for term in ['company', 'issuer', 'seller']):
            return 'company'
        elif any(term in text_lower for term in ['purchaser', 'investor', 'buyer']):
            return 'investor'
        elif any(term in text_lower for term in ['sec', 'regulatory', 'government', 'court']):
            return 'third_party'
        else:
            return 'mutual'
    
    def _generate_contract_summary(self, contract_text: str, contract_data: SecuritiesContract) -> str:
        """Generate a meaningful contract summary based on extracted data"""
        
        # Extract key terms for summary
        summary_parts = []
        
        # Add contract type
        if contract_data.contract_type:
            summary_parts.append(f"{contract_data.contract_type}")
        
        # Add parties if available
        if contract_data.parties:
            issuer = next((p.name for p in contract_data.parties if p.role == PartyRole.ISSUER), None)
            purchaser = next((p.name for p in contract_data.parties if p.role == PartyRole.PURCHASER), None)
            
            if issuer and purchaser:
                summary_parts.append(f"between {issuer} and {purchaser}")
            elif contract_data.parties:
                party_names = [p.name for p in contract_data.parties[:2]]
                summary_parts.append(f"between {' and '.join(party_names)}")
        
        # Add financial terms
        if contract_data.total_offering_amount:
            summary_parts.append(f"for ${contract_data.total_offering_amount:,.0f}")
        
        # Add securities info if available
        if contract_data.securities:
            security_types = [s.security_type.value for s in contract_data.securities if s.security_type]
            if security_types:
                summary_parts.append(f"involving {', '.join(set(security_types))}")
        
        # Add execution date
        if contract_data.execution_date:
            summary_parts.append(f"executed on {contract_data.execution_date}")
        
        # If we have enough information, create a proper summary
        if len(summary_parts) >= 2:
            return ' '.join(summary_parts) + '.'
        
        # Otherwise, try to extract key information from the text
        text_snippet = contract_text[:500].replace('\n', ' ').strip()
        
        # Look for agreement type in text
        agreement_match = re.search(r'([A-Z][A-Za-z\s]*AGREEMENT[A-Za-z\s]*)', text_snippet, re.IGNORECASE)
        if agreement_match:
            agreement_type = agreement_match.group(1).strip()
            return f"{agreement_type} with extracted party and financial information."
        
        return f"Securities contract with {len(contract_data.parties)} parties" + (
            f" involving ${contract_data.total_offering_amount:,.0f}" if contract_data.total_offering_amount else ""
        ) + "."
    
    def _create_enhanced_basic_contract(self, contract_text: str, contract_type: str, error_msg: str, rule_data: dict) -> SecuritiesContract:
        """Create an enhanced basic contract using both AI parsing failure and rule-based extraction"""
        
        # Start with the basic contract
        basic_contract = self._create_basic_contract(contract_text, contract_type, error_msg)
        
        # Enhance with rule-based data
        if rule_data.get('execution_date'):
            basic_contract.execution_date = rule_data['execution_date']
        
        if rule_data.get('total_offering_amount'):
            basic_contract.total_offering_amount = rule_data['total_offering_amount']
        
        if rule_data.get('parties') and not basic_contract.parties:
            basic_contract.parties = rule_data['parties']
        
        # Add securities information
        if rule_data.get('securities'):
            securities_list = []
            for sec_data in rule_data['securities']:
                security = Security(
                    security_type=SecurityType(sec_data.get('security_type', 'common_stock')),
                    number_of_shares=sec_data.get('number_of_shares'),
                    purchase_price_per_share=sec_data.get('purchase_price_per_share'),
                    exercise_price=sec_data.get('exercise_price')
                )
                securities_list.append(security)
            basic_contract.securities = securities_list
        
        # Add closing conditions
        if rule_data.get('closing_conditions'):
            conditions_list = []
            for cond_data in rule_data['closing_conditions']:
                condition = ClosingConditions(
                    condition_description=cond_data['condition_description'],
                    is_waivable=cond_data.get('is_waivable', False),
                    responsible_party=cond_data.get('responsible_party', 'mutual')
                )
                conditions_list.append(condition)
            basic_contract.closing_conditions = conditions_list
        
        # Generate a better summary
        basic_contract.summary = self._generate_contract_summary(contract_text, basic_contract)
        
        return basic_contract
    
    def _extract_license_with_rules(self, contract_text: str) -> dict:
        """Rule-based extraction for license agreement specific information"""
        license_data = {}
        
        # Royalty rate extraction
        royalty_patterns = [
            r'(\d+(?:\.\d+)?)\s*%\s*royalty',
            r'royalty.*?(\d+(?:\.\d+)?)\s*percent',
            r'royalty rate.*?(\d+(?:\.\d+)?)\s*%',
        ]
        
        for pattern in royalty_patterns:
            match = re.search(pattern, contract_text[:5000], re.IGNORECASE)
            if match:
                try:
                    royalty_rate = float(match.group(1))
                    license_data['royalty_rate'] = royalty_rate
                    break
                except ValueError:
                    continue
        
        # Upfront payment extraction
        upfront_patterns = [
            r'upfront.*?payment.*?\$\s*([\d,]+(?:\.\d{2})?)',
            r'initial.*?payment.*?\$\s*([\d,]+(?:\.\d{2})?)',
            r'upon.*?execution.*?\$\s*([\d,]+(?:\.\d{2})?)',
        ]
        
        for pattern in upfront_patterns:
            match = re.search(pattern, contract_text[:5000], re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    license_data['upfront_payment'] = amount
                    break
                except ValueError:
                    continue
        
        # Patent number extraction
        patent_patterns = [
            r'(?:Patent No\.|U\.S\. Patent No\.|Patent Number)\s*([0-9,]+)',
            r'patent application.*?([0-9/,]+)',
        ]
        
        patents = []
        for pattern in patent_patterns:
            matches = re.finditer(pattern, contract_text[:3000], re.IGNORECASE)
            for match in matches:
                patent_num = match.group(1).strip()
                if patent_num not in patents:
                    patents.append(patent_num)
        
        if patents:
            license_data['patents'] = patents
        
        # Territory extraction
        territory_patterns = [
            r'territory.*?(worldwide|global)',
            r'territory.*?(United States|U\.S\.|USA)',
            r'exclusively.*?(worldwide|global|United States)',
        ]
        
        for pattern in territory_patterns:
            match = re.search(pattern, contract_text[:3000], re.IGNORECASE)
            if match:
                territory = match.group(1)
                license_data['territory'] = territory
                break
        
        # Field of use extraction
        field_patterns = [
            r'field of use.*?(human therapeutics?|therapeutic)',
            r'indication.*?(cancer|oncology|rare disease)',
            r'treatment of.*?([A-Za-z\s]+disease)',
        ]
        
        for pattern in field_patterns:
            match = re.search(pattern, contract_text[:3000], re.IGNORECASE)
            if match:
                field = match.group(1)
                license_data['field_of_use'] = field
                break
        
        # Add the general rule-based extraction as well
        general_data = self._extract_with_rules(contract_text)
        license_data.update(general_data)
        
        return license_data
    
    def _generate_license_summary(self, contract_text: str, contract_data: SecuritiesContract, license_data: dict) -> str:
        """Generate a meaningful license agreement summary"""
        
        summary_parts = []
        
        # Add license type
        if 'exclusive' in contract_text.lower():
            summary_parts.append("Exclusive License Agreement")
        elif 'non-exclusive' in contract_text.lower():
            summary_parts.append("Non-Exclusive License Agreement")
        else:
            summary_parts.append("License Agreement")
        
        # Add parties
        if contract_data.parties:
            licensor = next((p.name for p in contract_data.parties if p.role == PartyRole.ISSUER), None)
            licensee = next((p.name for p in contract_data.parties if p.role == PartyRole.PURCHASER), None)
            
            if licensor and licensee:
                summary_parts.append(f"between {licensor} (licensor) and {licensee} (licensee)")
        
        # Add technology/IP information
        if license_data.get('patents'):
            patents = license_data['patents'][:2]  # First 2 patents
            summary_parts.append(f"covering patents {', '.join(patents)}")
        
        # Add field of use
        if license_data.get('field_of_use'):
            summary_parts.append(f"for {license_data['field_of_use']}")
        
        # Add territory
        if license_data.get('territory'):
            summary_parts.append(f"in {license_data['territory']}")
        
        # Add financial terms
        financial_terms = []
        if license_data.get('upfront_payment'):
            financial_terms.append(f"${license_data['upfront_payment']:,.0f} upfront")
        
        if license_data.get('royalty_rate'):
            financial_terms.append(f"{license_data['royalty_rate']}% royalty")
        
        if financial_terms:
            summary_parts.append(f"with {' and '.join(financial_terms)}")
        
        # Add execution date
        if contract_data.execution_date:
            summary_parts.append(f"executed on {contract_data.execution_date}")
        
        if len(summary_parts) >= 2:
            return ' '.join(summary_parts) + '.'
        
        # Fallback summary
        return f"License agreement for intellectual property rights between parties{' with financial terms' if financial_terms else ''}."

def import_securities_contract_to_neo4j(contract_data: SecuritiesContract, driver):
    """Import structured securities contract data into Neo4j"""
    
    cypher_query = """
    // Create main securities contract node
    MERGE (c:SecuritiesContract {title: $title})
    SET c.contract_type = $contract_type,
        c.summary = $summary,
        c.execution_date = CASE WHEN $execution_date IS NOT NULL 
                          THEN date($execution_date) ELSE NULL END,
        c.closing_date = CASE WHEN $closing_date IS NOT NULL 
                        THEN date($closing_date) ELSE NULL END,
        c.effectiveness_date = CASE WHEN $effectiveness_date IS NOT NULL 
                              THEN date($effectiveness_date) ELSE NULL END,
        c.total_offering_amount = $total_offering_amount,
        c.registration_status = $registration_status,
        c.use_of_proceeds = $use_of_proceeds,
        c.governing_law = $governing_law,
        c.jurisdiction = $jurisdiction,
        c.sec_exemption = $sec_exemption,
        c.disclosure_requirements = $disclosure_requirements
    
    // Create parties and relationships
    WITH c
    UNWIND $parties AS party_data
    MERGE (p:Party {name: party_data.name})
    SET p.role = party_data.role,
        p.entity_type = party_data.entity_type,
        p.jurisdiction = party_data.jurisdiction,
        p.address = party_data.address,
        p.tax_id = party_data.tax_id
    MERGE (p)-[:PARTY_TO]->(c)
    
    // Create securities and relationships
    WITH c
    UNWIND $securities AS security_data
    CREATE (s:Security)
    SET s.security_type = security_data.security_type,
        s.number_of_shares = security_data.number_of_shares,
        s.par_value = security_data.par_value,
        s.purchase_price_per_share = security_data.purchase_price_per_share,
        s.total_purchase_price = security_data.total_purchase_price,
        s.exercise_price = security_data.exercise_price,
        s.conversion_terms = security_data.conversion_terms,
        s.voting_rights = security_data.voting_rights,
        s.liquidation_preference = security_data.liquidation_preference
    MERGE (c)-[:ISSUES_SECURITY]->(s)
    
    // Create closing conditions
    WITH c
    UNWIND $closing_conditions AS condition_data
    CREATE (cc:ClosingCondition)
    SET cc.description = condition_data.condition_description,
        cc.is_waivable = condition_data.is_waivable,
        cc.responsible_party = condition_data.responsible_party,
        cc.deadline = CASE WHEN condition_data.deadline IS NOT NULL 
                     THEN date(condition_data.deadline) ELSE NULL END
    MERGE (c)-[:HAS_CLOSING_CONDITION]->(cc)
    
    // Create representations and warranties
    WITH c
    UNWIND $representations AS rep_data
    CREATE (r:Representation)
    SET r.category = rep_data.category,
        r.description = rep_data.description,
        r.is_material = rep_data.is_material,
        r.survival_period = rep_data.survival_period
    MERGE (c)-[:INCLUDES_REPRESENTATION]->(r)
    
    // Create registration rights if present
    WITH c
    FOREACH (_ IN CASE WHEN $registration_rights IS NOT NULL THEN [1] ELSE [] END |
        CREATE (rr:RegistrationRights)
        SET rr.demand_rights = $registration_rights.demand_rights,
            rr.piggyback_rights = $registration_rights.piggyback_rights,
            rr.form_s3_rights = $registration_rights.form_s3_rights,
            rr.registration_expenses = $registration_rights.registration_expenses,
            rr.holdback_period = $registration_rights.holdback_period
        MERGE (c)-[:GRANTS_REGISTRATION_RIGHTS]->(rr)
    )
    
    // Create resale restrictions if present  
    WITH c
    FOREACH (_ IN CASE WHEN $resale_restrictions IS NOT NULL THEN [1] ELSE [] END |
        CREATE (rs:ResaleRestrictions)
        SET rs.holding_period = $resale_restrictions.holding_period,
            rs.volume_limitations = $resale_restrictions.volume_limitations,
            rs.manner_of_sale = $resale_restrictions.manner_of_sale,
            rs.rule_144_compliance = $resale_restrictions.rule_144_compliance
        MERGE (c)-[:HAS_RESALE_RESTRICTIONS]->(rs)
    )
    """
    
    # Prepare data with defaults for missing values
    parties_data = []
    for party in contract_data.parties:
        parties_data.append({
            'name': party.name,
            'role': party.role.value if party.role else 'unknown',
            'entity_type': party.entity_type,
            'jurisdiction': party.jurisdiction,
            'address': party.address,
            'tax_id': party.tax_id
        })
    
    securities_data = []
    for security in contract_data.securities:
        securities_data.append({
            'security_type': security.security_type.value if security.security_type else 'unknown',
            'number_of_shares': security.number_of_shares,
            'par_value': security.par_value,
            'purchase_price_per_share': security.purchase_price_per_share,
            'total_purchase_price': security.total_purchase_price,
            'exercise_price': security.exercise_price,
            'conversion_terms': security.conversion_terms,
            'voting_rights': security.voting_rights,
            'liquidation_preference': security.liquidation_preference
        })
    
    closing_conditions_data = []
    for condition in contract_data.closing_conditions:
        closing_conditions_data.append({
            'condition_description': condition.condition_description,
            'is_waivable': condition.is_waivable,
            'responsible_party': condition.responsible_party,
            'deadline': condition.deadline.isoformat() if condition.deadline else None
        })
    
    representations_data = []
    for rep in contract_data.representations_warranties:
        representations_data.append({
            'category': rep.category,
            'description': rep.description,
            'is_material': rep.is_material,
            'survival_period': rep.survival_period
        })
    
    # Prepare registration rights data
    registration_rights_data = None
    if contract_data.registration_rights:
        registration_rights_data = {
            'demand_rights': contract_data.registration_rights.demand_rights,
            'piggyback_rights': contract_data.registration_rights.piggyback_rights,
            'form_s3_rights': contract_data.registration_rights.form_s3_rights,
            'registration_expenses': contract_data.registration_rights.registration_expenses,
            'holdback_period': contract_data.registration_rights.holdback_period
        }
    
    # Prepare resale restrictions data
    resale_restrictions_data = None
    if contract_data.resale_restrictions:
        resale_restrictions_data = {
            'holding_period': contract_data.resale_restrictions.holding_period,
            'volume_limitations': contract_data.resale_restrictions.volume_limitations,
            'manner_of_sale': contract_data.resale_restrictions.manner_of_sale,
            'rule_144_compliance': contract_data.resale_restrictions.rule_144_compliance
        }
    
    with driver.session() as session:
        try:
            session.run(cypher_query, {
                "title": contract_data.title,
                "contract_type": contract_data.contract_type,
                "summary": contract_data.summary,
                "execution_date": contract_data.execution_date.isoformat() if contract_data.execution_date else None,
                "closing_date": contract_data.closing_date.isoformat() if contract_data.closing_date else None,
                "effectiveness_date": contract_data.effectiveness_date.isoformat() if contract_data.effectiveness_date else None,
                "total_offering_amount": contract_data.total_offering_amount,
                "registration_status": contract_data.registration_status.value if contract_data.registration_status else None,
                "use_of_proceeds": contract_data.use_of_proceeds,
                "governing_law": contract_data.governing_law,
                "jurisdiction": contract_data.jurisdiction,
                "sec_exemption": contract_data.sec_exemption,
                "disclosure_requirements": contract_data.disclosure_requirements,
                "parties": parties_data,
                "securities": securities_data,
                "closing_conditions": closing_conditions_data,
                "representations": representations_data,
                "registration_rights": registration_rights_data,
                "resale_restrictions": resale_restrictions_data
            })
        except Exception as e:
            print(f"Warning: Error importing contract to Neo4j: {e}")
            # Create minimal contract record as fallback
            minimal_query = """
            MERGE (c:SecuritiesContract {title: $title})
            SET c.contract_type = $contract_type,
                c.summary = $summary
            """
            session.run(minimal_query, {
                "title": contract_data.title,
                "contract_type": contract_data.contract_type,
                "summary": contract_data.summary
            })

class SecuritiesContractInput(BaseModel):
    """Input schema for securities contract queries"""
    
    # Parties
    company_name: Optional[str] = Field(None, description="Company/issuer name")
    investor_name: Optional[str] = Field(None, description="Investor/purchaser name")
    
    # Financial filters
    min_offering_amount: Optional[float] = Field(None, description="Minimum total offering amount")
    max_offering_amount: Optional[float] = Field(None, description="Maximum total offering amount")
    min_price_per_share: Optional[float] = Field(None, description="Minimum price per share")
    max_price_per_share: Optional[float] = Field(None, description="Maximum price per share")
    
    # Security types
    security_type: Optional[str] = Field(None, description="Type of security (common_stock, preferred_stock, warrant, etc.)")
    
    # Date filters
    execution_after: Optional[str] = Field(None, description="Contracts executed after date (YYYY-MM-DD)")
    execution_before: Optional[str] = Field(None, description="Contracts executed before date (YYYY-MM-DD)")
    closing_after: Optional[str] = Field(None, description="Contracts closing after date (YYYY-MM-DD)")
    closing_before: Optional[str] = Field(None, description="Contracts closing before date (YYYY-MM-DD)")
    
    # Legal and compliance
    registration_status: Optional[str] = Field(None, description="Registration status (registered, exempt, restricted)")
    sec_exemption: Optional[str] = Field(None, description="SEC exemption rule (e.g., Rule 506)")
    governing_law: Optional[str] = Field(None, description="Governing law jurisdiction")
    
    # Rights and restrictions
    has_registration_rights: Optional[bool] = Field(None, description="Whether contract includes registration rights")
    has_resale_restrictions: Optional[bool] = Field(None, description="Whether contract has resale restrictions")
    has_board_rights: Optional[bool] = Field(None, description="Whether investors get board rights")
    
    # Advanced queries
    summary_search: Optional[str] = Field(None, description="Search in contract summaries")
    custom_query: Optional[str] = Field(None, description="Custom search criteria")

class SecuritiesContractTool(BaseTool):
    name: str = "SecuritiesContractSearch"
    description: str = (
        "Search and analyze securities purchase agreements and investment contracts. "
        "Can filter by parties, financial terms, security types, dates, and legal provisions."
    )
    args_schema: type[BaseModel] = SecuritiesContractInput
    
    def _run(self, **kwargs) -> str:
        """Execute the securities contract search"""
        return self._build_and_execute_query(**kwargs)
    
    def _build_and_execute_query(self, **kwargs) -> str:
        """Build and execute Cypher query based on inputs"""
        
        # Base query
        cypher = "MATCH (c:SecuritiesContract) "
        filters = []
        params = {}
        
        # Party filters
        if kwargs.get('company_name'):
            cypher += "MATCH (c)<-[:PARTY_TO]-(company:Party) "
            filters.append("company.role IN ['issuer'] AND toLower(company.name) CONTAINS $company_name")
            params['company_name'] = kwargs['company_name'].lower()
            
        if kwargs.get('investor_name'):
            cypher += "MATCH (c)<-[:PARTY_TO]-(investor:Party) "
            filters.append("investor.role IN ['purchaser', 'investor'] AND toLower(investor.name) CONTAINS $investor_name")
            params['investor_name'] = kwargs['investor_name'].lower()
        
        # Financial filters
        if kwargs.get('min_offering_amount'):
            filters.append("c.total_offering_amount >= $min_offering_amount")
            params['min_offering_amount'] = kwargs['min_offering_amount']
            
        if kwargs.get('max_offering_amount'):
            filters.append("c.total_offering_amount <= $max_offering_amount")
            params['max_offering_amount'] = kwargs['max_offering_amount']
        
        # Security type filters
        if kwargs.get('security_type'):
            cypher += "MATCH (c)-[:ISSUES_SECURITY]->(s:Security) "
            filters.append("s.security_type = $security_type")
            params['security_type'] = kwargs['security_type']
        
        # Date filters
        if kwargs.get('execution_after'):
            filters.append("c.execution_date >= date($execution_after)")
            params['execution_after'] = kwargs['execution_after']
            
        if kwargs.get('closing_before'):
            filters.append("c.closing_date <= date($closing_before)")
            params['closing_before'] = kwargs['closing_before']
        
        # Legal filters
        if kwargs.get('registration_status'):
            filters.append("c.registration_status = $registration_status")
            params['registration_status'] = kwargs['registration_status']
            
        if kwargs.get('sec_exemption'):
            filters.append("c.sec_exemption CONTAINS $sec_exemption")
            params['sec_exemption'] = kwargs['sec_exemption']
        
        # Apply filters
        if filters:
            cypher += "WHERE " + " AND ".join(filters) + " "
        
        # Return results
        cypher += """
        RETURN {
            total_contracts: count(c),
            contracts: collect(DISTINCT {
                title: c.title,
                summary: c.summary,
                total_offering_amount: c.total_offering_amount,
                execution_date: c.execution_date,
                closing_date: c.closing_date,
                registration_status: c.registration_status,
                parties: [(c)<-[:PARTY_TO]-(p) | {name: p.name, role: p.role}],
                securities: [(c)-[:ISSUES_SECURITY]->(s) | {type: s.security_type, shares: s.number_of_shares, price: s.purchase_price_per_share}]
            })[..5]
        } AS results
        """
        
        return self._execute_cypher(cypher, params)
    
    def _execute_cypher(self, cypher: str, params: dict) -> str:
        """Execute Cypher query against Neo4j database"""
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                result = session.run(cypher, params)
                data = result.single()
                
                if data and 'results' in data:
                    return self._format_results(data['results'])
                else:
                    return "No results found for the given criteria."
                    
        except Exception as e:
            return f"Database error: {str(e)}"
        finally:
            if 'driver' in locals():
                driver.close()
    
    def _format_results(self, results: dict) -> str:
        """Format query results for display"""
        if not results:
            return "No contracts found."
        
        total = results.get('total_contracts', 0)
        contracts = results.get('contracts', [])
        
        output = [f"Found {total} securities contract(s):\n"]
        
        for i, contract in enumerate(contracts, 1):
            output.append(f"{i}. {contract.get('title', 'Unknown Title')}")
            
            if contract.get('total_offering_amount'):
                output.append(f"   Offering Amount: ${contract['total_offering_amount']:,.2f}")
            
            if contract.get('execution_date'):
                output.append(f"   Execution Date: {contract['execution_date']}")
                
            if contract.get('closing_date'):
                output.append(f"   Closing Date: {contract['closing_date']}")
            
            parties = contract.get('parties', [])
            if parties:
                party_info = [f"{p.get('name', 'Unknown')} ({p.get('role', 'Unknown')})" for p in parties]
                output.append(f"   Parties: {', '.join(party_info)}")
            
            securities = contract.get('securities', [])
            if securities:
                sec_info = []
                for sec in securities:
                    sec_desc = sec.get('type', 'Unknown')
                    if sec.get('shares'):
                        sec_desc += f" ({sec['shares']:,} shares"
                        if sec.get('price'):
                            sec_desc += f" @ ${sec['price']:.2f}"
                        sec_desc += ")"
                    sec_info.append(sec_desc)
                output.append(f"   Securities: {', '.join(sec_info)}")
            
            output.append("")
        
        return "\n".join(output) 