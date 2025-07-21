import os
from datetime import datetime
from typing import List, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
import json
import re
import torch

from license_data_models import (
    LicenseContract, Party, LicensedPatent, LicensedProduct, LicensedTerritory,
    ExclusivityMilestone, SublicenseRestriction, ClosingCondition, DiligenceClause,
    ExhibitAttachment, ExclusivityGrantType, OEMType, ContractTermType, AssignmentRestrictionType
)

class LicenseContractExtractor:
    """Extract structured data from license agreements using Llama 3.3 70B"""
    
    def __init__(self, model_path: str = None):
        """
        Initialize the Llama-based extractor
        
        Args:
            model_path: Path to the Llama 3.3 70B model directory
        """
        if not model_path:
            model_path = os.getenv("LLAMA_MODEL_PATH", "/path/to/llama-3.3-70b")
        
        if not os.path.exists(model_path):
            raise ValueError(f"Llama model not found at: {model_path}")
        
        # Initialize Llama model and tokenizer
        print(f"Loading Llama model from: {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Create pipeline with your specified parameters
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_length=4096,
            do_sample=True,
            temperature=0.7,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        self.parser = PydanticOutputParser(pydantic_object=LicenseContract)
    
    def extract_contract_data(self, contract_text: str) -> LicenseContract:
        """Extract structured license contract data from text"""
        
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
               - Addresses and contact information
            
            2. AGREEMENT GRANTS - Extract:
               - Summary of all grant clauses
               - Field of use limitations
               - Territory restrictions
            
            3. EXCLUSIVITY - Determine:
               - Exclusive, Sole, or Nonexclusive
               - Milestones for maintaining exclusivity
               - Sales targets and deadlines
            
            4. LICENSED MATERIALS - Identify:
               - Patent numbers and titles
               - Licensed products
               - Territory scope
            
            5. FINANCIAL TERMS - Extract:
               - Upfront payments
               - Royalty rates
               - Stacking clauses
               - Most favored nations clauses
            
            6. OBLIGATIONS - Identify:
               - Licensor obligations (delivery, training, etc.)
               - Licensee obligations
               - Improvement clauses
            
            7. WARRANTIES - Extract:
               - Litigation warranties
               - Infringement warranties
               - IP sufficiency warranties
               - Product/service warranties
            
            8. CONFIDENTIALITY - Determine:
               - Whether agreement is confidential
               - What materials are confidential
            
            9. LEGAL TERMS - Extract:
               - Governing law
               - Jurisdiction
               - Assignment restrictions
               - Termination rights
            
            RULES:
            - Extract exact dates in YYYY-MM-DD format
            - Extract dollar amounts as numbers only
            - For boolean fields, use true/false
            - For lists, separate with semicolons
            - Always provide a meaningful summary
            
            {format_instructions}
            """,
            input_variables=["contract_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        prompt = prompt_template.format(contract_text=contract_text[:12000])  # Slightly shorter for Llama
        
        try:
            # Generate response using Llama pipeline
            response = self.pipe(prompt)
            generated_text = response[0]['generated_text']
            
            # Extract the response part (remove the input prompt)
            response_content = generated_text[len(prompt):].strip()
            
            result = self.parser.parse(response_content)
            
            # Enhance with rule-based data
            if not result.execution_date and license_data.get('execution_date'):
                result.execution_date = license_data['execution_date']
            
            if not result.licensor and license_data.get('licensor'):
                result.licensor = Party(**license_data['licensor'])
            
            if not result.licensee and license_data.get('licensee'):
                result.licensee = Party(**license_data['licensee'])
            
            if not result.licensed_patents and license_data.get('patents'):
                patents_list = []
                for patent_data in license_data['patents']:
                    patent = LicensedPatent(**patent_data)
                    patents_list.append(patent)
                result.licensed_patents = patents_list
            
            if not result.licensed_products and license_data.get('products'):
                products_list = []
                for product_data in license_data['products']:
                    product = LicensedProduct(**product_data)
                    products_list.append(product)
                result.licensed_products = products_list
            
            if not result.licensed_territory and license_data.get('territories'):
                territories_list = []
                for territory_data in license_data['territories']:
                    territory = LicensedTerritory(**territory_data)
                    territories_list.append(territory)
                result.licensed_territory = territories_list
            
            # Ensure we have a proper summary
            if not result.summary or "Basic extraction" in result.summary:
                result.summary = self._generate_license_summary(contract_text, result, license_data)
            
            return result
            
        except Exception as e:
            return self._create_enhanced_basic_contract(contract_text, "License Agreement", str(e), license_data)
    
    def _extract_license_with_rules(self, contract_text: str) -> dict:
        """Extract license-specific information using rule-based methods"""
        license_data = {}
        
        # Extract execution date
        date_patterns = [
            r'executed\s+on\s+(\w+\s+\d{1,2},?\s+\d{4})',
            r'dated\s+as\s+of\s+(\w+\s+\d{1,2},?\s+\d{4})',
            r'this\s+(\d{1,2})\w+\s+day\s+of\s+(\w+)\s+(\d{4})',
            r'effective\s+date.*?(\w+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, contract_text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1) if len(match.groups()) == 1 else f"{match.group(2)} {match.group(1)}, {match.group(3)}"
                    license_data['execution_date'] = datetime.strptime(date_str, "%B %d, %Y").date()
                    break
                except:
                    continue
        
        # Extract parties
        party_patterns = [
            r'between\s+(.*?)\s+and\s+(.*?)(?:\s+\(|,|\.)',
            r'licensor.*?:\s*(.*?)(?:\s+licensee|\.)',
            r'licensee.*?:\s*(.*?)(?:\s+licensor|\.)'
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, contract_text, re.IGNORECASE)
            if matches:
                if len(matches[0]) == 2:
                    license_data['licensor'] = {'name': matches[0][0].strip()}
                    license_data['licensee'] = {'name': matches[0][1].strip()}
                    break
        
        # Extract patent numbers
        patent_pattern = r'(?:patent|pat\.)\s*(?:no\.?|number)?\s*[#]?\s*(\d{1,3}(?:,\d{3})*(?:,\d{3})*)'
        patents = re.findall(patent_pattern, contract_text, re.IGNORECASE)
        if patents:
            license_data['patents'] = [{'patent_number': patent.replace(',', '')} for patent in patents]
        
        # Extract exclusivity
        if re.search(r'exclusive\s+license', contract_text, re.IGNORECASE):
            license_data['exclusivity'] = 'Exclusive'
        elif re.search(r'sole\s+license', contract_text, re.IGNORECASE):
            license_data['exclusivity'] = 'Sole'
        else:
            license_data['exclusivity'] = 'Nonexclusive'
        
        # Extract upfront payment
        payment_patterns = [
            r'upfront\s+payment.*?\$?([\d,]+(?:\.\d{2})?)',
            r'license\s+fee.*?\$?([\d,]+(?:\.\d{2})?)',
            r'initial\s+payment.*?\$?([\d,]+(?:\.\d{2})?)'
        ]
        
        for pattern in payment_patterns:
            match = re.search(pattern, contract_text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    license_data['upfront_payment'] = amount
                    break
                except:
                    continue
        
        return license_data
    
    def _create_enhanced_basic_contract(self, contract_text: str, contract_type: str, error_msg: str, license_data: dict) -> LicenseContract:
        """Create a basic license contract with available data"""
        
        # Extract basic information
        lines = contract_text.split('\n')
        title = lines[0].strip() if lines else "Unknown License Agreement"
        
        # Create basic parties
        licensor = None
        licensee = None
        if license_data.get('licensor'):
            licensor = Party(**license_data['licensor'])
        if license_data.get('licensee'):
            licensee = Party(**license_data['licensee'])
        
        # Create basic contract
        contract = LicenseContract(
            title=title,
            contract_type=contract_type,
            summary=f"Basic extraction of {contract_type}. Error: {error_msg}",
            execution_date=license_data.get('execution_date'),
            licensor=licensor,
            licensee=licensee,
            exclusivity_grant_type=ExclusivityGrantType(license_data.get('exclusivity', 'Nonexclusive')),
            upfront_payment=license_data.get('upfront_payment'),
            licensed_patents=[LicensedPatent(**patent) for patent in license_data.get('patents', [])],
            licensed_products=[LicensedProduct(**product) for product in license_data.get('products', [])],
            licensed_territory=[LicensedTerritory(**territory) for territory in license_data.get('territories', [])]
        )
        
        return contract
    
    def _generate_license_summary(self, contract_text: str, contract_data: LicenseContract, license_data: dict) -> str:
        """Generate a summary of the license agreement"""
        
        summary_parts = []
        
        if contract_data.licensor and contract_data.licensee:
            summary_parts.append(f"License agreement between {contract_data.licensor.name} (licensor) and {contract_data.licensee.name} (licensee)")
        
        if contract_data.exclusivity_grant_type:
            summary_parts.append(f"Grant type: {contract_data.exclusivity_grant_type.value}")
        
        if contract_data.licensed_patents:
            patent_count = len(contract_data.licensed_patents)
            summary_parts.append(f"Licenses {patent_count} patent(s)")
        
        if contract_data.licensed_products:
            product_count = len(contract_data.licensed_products)
            summary_parts.append(f"Licenses {product_count} product(s)")
        
        if contract_data.upfront_payment:
            summary_parts.append(f"Upfront payment: ${contract_data.upfront_payment:,.2f}")
        
        if contract_data.licensed_territory:
            territory_count = len(contract_data.licensed_territory)
            summary_parts.append(f"Territory: {territory_count} region(s)")
        
        if contract_data.execution_date:
            summary_parts.append(f"Executed: {contract_data.execution_date}")
        
        return ". ".join(summary_parts) if summary_parts else "License agreement with basic terms extracted"

def check_contract_exists(title: str, driver) -> bool:
    """Check if a license contract with the given title already exists"""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (c:LicenseContract {title: $title})
                RETURN count(c) as count
            """, title=title)
            count = result.single()["count"]
            return count > 0
    except Exception as e:
        print(f"Error checking if contract exists: {e}")
        return False

def import_license_contract_to_neo4j(contract_data: LicenseContract, driver):
    """Import license contract data to Neo4j database"""
    
    # Check if contract already exists
    if check_contract_exists(contract_data.title, driver):
        print(f"Contract '{contract_data.title}' already exists. Skipping import.")
        return
    
    try:
        with driver.session() as session:
            contract_props = {
                'title': contract_data.title,
                'contract_type': contract_data.contract_type,
                'summary': contract_data.summary,
                'execution_date': contract_data.execution_date.isoformat() if contract_data.execution_date else None,
                'effective_date': contract_data.effective_date.isoformat() if contract_data.effective_date else None,
                'expiration_date': contract_data.expiration_date.isoformat() if contract_data.expiration_date else None,
                'agreement_grants': contract_data.agreement_grants,
                'exclusivity_grant_type': contract_data.exclusivity_grant_type.value if contract_data.exclusivity_grant_type else None,
                'right_to_sublicense': contract_data.right_to_sublicense,
                'crosslicensing_indicator': contract_data.crosslicensing_indicator,
                'licensed_field_of_use': contract_data.licensed_field_of_use,
                'contract_term': contract_data.contract_term.value if contract_data.contract_term else None,
                'contract_term_details': contract_data.contract_term_details,
                'contract_releases': contract_data.contract_releases,
                'non_compete_covenant_indicator': contract_data.non_compete_covenant_indicator,
                'retained_licensor_rights': contract_data.retained_licensor_rights,
                'product_branding_rights': contract_data.product_branding_rights,
                'oem_type': contract_data.oem_type.value if contract_data.oem_type else None,
                'license_use_restrictions': contract_data.license_use_restrictions,
                'licensor_obligations': contract_data.licensor_obligations,
                'licensor_improvements_clause': contract_data.licensor_improvements_clause,
                'licensee_improvements_clause': contract_data.licensee_improvements_clause,
                'licensee_right_to_improvements': contract_data.licensee_right_to_improvements,
                'related_parties_licensor': contract_data.related_parties_licensor,
                'related_parties_licensee': contract_data.related_parties_licensee,
                'related_parties_unknown': contract_data.related_parties_unknown,
                'upfront_payment': contract_data.upfront_payment,
                'stacking_clause_indicator': contract_data.stacking_clause_indicator,
                'stacking_clause_terms': contract_data.stacking_clause_terms,
                'most_favored_nations_clause': contract_data.most_favored_nations_clause,
                'licensee_infringement_indemnities': contract_data.licensee_infringement_indemnities,
                'licensor_product_liability_indemnities': contract_data.licensor_product_liability_indemnities,
                'licensee_product_liability_indemnities': contract_data.licensee_product_liability_indemnities,
                'delivery_supply': contract_data.delivery_supply,
                'relationship_between_contract_parties_clause': contract_data.relationship_between_contract_parties_clause,
                'warranties_litigation': contract_data.warranties_litigation,
                'warranties_infringement': contract_data.warranties_infringement,
                'warranties_ip_sufficiency': contract_data.warranties_ip_sufficiency,
                'warranties_product_or_service': contract_data.warranties_product_or_service,
                'assignment_restrictions': contract_data.assignment_restrictions.value if contract_data.assignment_restrictions else None,
                'assignment_restrictions_details': contract_data.assignment_restrictions_details,
                'insurance_clause_indicator': contract_data.insurance_clause_indicator,
                'audit_clause': contract_data.audit_clause,
                'late_delivery_clauses': contract_data.late_delivery_clauses,
                'confidential_agreement': contract_data.confidential_agreement,
                'confidential_materials': contract_data.confidential_materials,
                'patent_prosecution_responsibilities': contract_data.patent_prosecution_responsibilities,
                'suspected_infringement_clause': contract_data.suspected_infringement_clause,
                'legal_representative_organization': contract_data.legal_representative_organization,
                'legal_representative_lawyer': contract_data.legal_representative_lawyer,
                'governing_law': contract_data.governing_law,
                'jurisdiction': contract_data.jurisdiction,
                'termination_rights': contract_data.termination_rights,
                'dispute_resolution': contract_data.dispute_resolution,
                'regulatory_requirements': contract_data.regulatory_requirements,
                'export_control': contract_data.export_control
            }
            
            # Remove None values
            contract_props = {k: v for k, v in contract_props.items() if v is not None}
            
            # Create or merge contract node
            session.run("""
                MERGE (c:LicenseContract {title: $title})
                SET c += $props
                RETURN c
            """, title=contract_data.title, props=contract_props)
            
            # Create party nodes and relationships
            if contract_data.licensor:
                licensor_props = {
                    'name': contract_data.licensor.name,
                    'address': contract_data.licensor.address,
                    'entity_type': contract_data.licensor.entity_type,
                    'jurisdiction': contract_data.licensor.jurisdiction,
                    'contact_info': contract_data.licensor.contact_info
                }
                licensor_props = {k: v for k, v in licensor_props.items() if v is not None}
                
                # Create licensor node with individual properties
                licensor_query = """
                    MERGE (l:Licensor {name: $name})
                    SET l.address = $address, l.entity_type = $entity_type, l.jurisdiction = $jurisdiction, l.contact_info = $contact_info
                    WITH l
                    MATCH (c:LicenseContract {title: $title})
                    MERGE (l)-[:IS_LICENSOR_OF]->(c)
                """
                session.run(licensor_query, 
                           name=licensor_props.get('name'),
                           address=licensor_props.get('address'),
                           entity_type=licensor_props.get('entity_type'),
                           jurisdiction=licensor_props.get('jurisdiction'),
                           contact_info=licensor_props.get('contact_info'),
                           title=contract_data.title)
            
            if contract_data.licensee:
                licensee_props = {
                    'name': contract_data.licensee.name,
                    'address': contract_data.licensee.address,
                    'entity_type': contract_data.licensee.entity_type,
                    'jurisdiction': contract_data.licensee.jurisdiction,
                    'contact_info': contract_data.licensee.contact_info
                }
                licensee_props = {k: v for k, v in licensee_props.items() if v is not None}
                
                # Create licensee node with individual properties
                licensee_query = """
                    MERGE (l:Licensee {name: $name})
                    SET l.address = $address, l.entity_type = $entity_type, l.jurisdiction = $jurisdiction, l.contact_info = $contact_info
                    WITH l
                    MATCH (c:LicenseContract {title: $title})
                    MERGE (l)-[:IS_LICENSEE_OF]->(c)
                """
                session.run(licensee_query, 
                           name=licensee_props.get('name'),
                           address=licensee_props.get('address'),
                           entity_type=licensee_props.get('entity_type'),
                           jurisdiction=licensee_props.get('jurisdiction'),
                           contact_info=licensee_props.get('contact_info'),
                           title=contract_data.title)
            
            # Create patent nodes
            for patent in contract_data.licensed_patents:
                patent_props = {
                    'patent_number': patent.patent_number,
                    'patent_title': patent.patent_title,
                    'filing_date': patent.filing_date.isoformat() if patent.filing_date else None,
                    'issue_date': patent.issue_date.isoformat() if patent.issue_date else None
                }
                patent_props = {k: v for k, v in patent_props.items() if v is not None}
                
                # Create patent node with individual properties
                patent_query = """
                    MERGE (p:Patent {patent_number: $patent_number})
                    SET p.patent_title = $patent_title, p.filing_date = $filing_date, p.issue_date = $issue_date
                    WITH p
                    MATCH (c:LicenseContract {title: $title})
                    MERGE (c)-[:LICENSES]->(p)
                """
                session.run(patent_query, 
                           patent_number=patent_props.get('patent_number'),
                           patent_title=patent_props.get('patent_title'),
                           filing_date=patent_props.get('filing_date'),
                           issue_date=patent_props.get('issue_date'),
                           title=contract_data.title)
            
            # Create product nodes
            for product in contract_data.licensed_products:
                product_props = {
                    'product_name': product.product_name,
                    'description': product.description,
                    'category': product.category
                }
                product_props = {k: v for k, v in product_props.items() if v is not None}
                
                # Create product node with individual properties
                product_query = """
                    MERGE (p:Product {product_name: $product_name})
                    SET p.description = $description, p.category = $category
                    WITH p
                    MATCH (c:LicenseContract {title: $title})
                    MERGE (c)-[:LICENSES]->(p)
                """
                session.run(product_query, 
                           product_name=product_props.get('product_name'),
                           description=product_props.get('description'),
                           category=product_props.get('category'),
                           title=contract_data.title)
            
            # Create territory nodes
            for territory in contract_data.licensed_territory:
                territory_props = {
                    'territory_name': territory.territory_name,
                    'territory_type': territory.territory_type,
                    'restrictions': territory.restrictions
                }
                territory_props = {k: v for k, v in territory_props.items() if v is not None}
                
                # Create territory node with individual properties
                territory_query = """
                    MERGE (t:Territory {territory_name: $territory_name})
                    SET t.territory_type = $territory_type, t.restrictions = $restrictions
                    WITH t
                    MATCH (c:LicenseContract {title: $title})
                    MERGE (c)-[:COVERS_TERRITORY]->(t)
                """
                session.run(territory_query, 
                           territory_name=territory_props.get('territory_name'),
                           territory_type=territory_props.get('territory_type'),
                           restrictions=territory_props.get('restrictions'),
                           title=contract_data.title)
    
    except Exception as e:
        print(f"Error importing license contract '{contract_data.title}': {e}")
        raise

class LicenseContractInput(BaseModel):
    """Input schema for license contract queries"""
    
    # Parties
    licensor_name: Optional[str] = Field(None, description="Licensor company name")
    licensee_name: Optional[str] = Field(None, description="Licensee company name")
    
    # Financial filters
    min_upfront_payment: Optional[float] = Field(None, description="Minimum upfront payment amount")
    max_upfront_payment: Optional[float] = Field(None, description="Maximum upfront payment amount")
    
    # License types
    exclusivity_type: Optional[str] = Field(None, description="Exclusivity type (Exclusive, Sole, Nonexclusive)")
    oem_type: Optional[str] = Field(None, description="OEM type (MSA, B2B, VAR, PL, DM, CS, SOEM)")
    
    # Date filters
    execution_after: Optional[str] = Field(None, description="Contracts executed after date (YYYY-MM-DD)")
    execution_before: Optional[str] = Field(None, description="Contracts executed before date (YYYY-MM-DD)")
    effective_after: Optional[str] = Field(None, description="Contracts effective after date (YYYY-MM-DD)")
    effective_before: Optional[str] = Field(None, description="Contracts effective before date (YYYY-MM-DD)")
    
    # Legal and compliance
    governing_law: Optional[str] = Field(None, description="Governing law jurisdiction")
    jurisdiction: Optional[str] = Field(None, description="Legal jurisdiction")
    
    # Rights and restrictions
    has_sublicense_rights: Optional[bool] = Field(None, description="Whether licensee has sublicense rights")
    has_crosslicensing: Optional[bool] = Field(None, description="Whether agreement includes cross-licensing")
    has_confidentiality: Optional[bool] = Field(None, description="Whether agreement is confidential")
    
    # Patent and product filters
    patent_number: Optional[str] = Field(None, description="Specific patent number")
    product_name: Optional[str] = Field(None, description="Specific product name")
    territory: Optional[str] = Field(None, description="Specific territory")
    
    # Advanced queries
    summary_search: Optional[str] = Field(None, description="Search in contract summaries")
    custom_query: Optional[str] = Field(None, description="Custom search criteria")

class LicenseContractTool(BaseTool):
    name: str = "LicenseContractSearch"
    description: str = (
        "Search and analyze license agreements and intellectual property contracts. "
        "Can filter by parties, financial terms, license types, dates, and legal provisions."
    )
    args_schema: type[BaseModel] = LicenseContractInput
    
    def __init__(self, neo4j_driver):
        super().__init__()
        self.driver = neo4j_driver
    
    def _run(self, **kwargs) -> str:
        return self._build_and_execute_query(**kwargs)
    
    def _build_and_execute_query(self, **kwargs) -> str:
        """Build and execute a Cypher query based on input parameters"""
        
        # Start building the query
        query_parts = ["MATCH (c:LicenseContract)"]
        where_conditions = []
        params = {}
        
        # Add party filters
        if kwargs.get('licensor_name'):
            query_parts.append("MATCH (l:Licensor)-[:IS_LICENSOR_OF]->(c)")
            where_conditions.append("l.name CONTAINS $licensor_name")
            params['licensor_name'] = kwargs['licensor_name']
        
        if kwargs.get('licensee_name'):
            query_parts.append("MATCH (le:Licensee)-[:IS_LICENSEE_OF]->(c)")
            where_conditions.append("le.name CONTAINS $licensee_name")
            params['licensee_name'] = kwargs['licensee_name']
        
        # Add financial filters
        if kwargs.get('min_upfront_payment'):
            where_conditions.append("c.upfront_payment >= $min_upfront_payment")
            params['min_upfront_payment'] = kwargs['min_upfront_payment']
        
        if kwargs.get('max_upfront_payment'):
            where_conditions.append("c.upfront_payment <= $max_upfront_payment")
            params['max_upfront_payment'] = kwargs['max_upfront_payment']
        
        # Add license type filters
        if kwargs.get('exclusivity_type'):
            where_conditions.append("c.exclusivity_grant_type = $exclusivity_type")
            params['exclusivity_type'] = kwargs['exclusivity_type']
        
        if kwargs.get('oem_type'):
            where_conditions.append("c.oem_type = $oem_type")
            params['oem_type'] = kwargs['oem_type']
        
        # Add date filters
        if kwargs.get('execution_after'):
            where_conditions.append("c.execution_date >= $execution_after")
            params['execution_after'] = kwargs['execution_after']
        
        if kwargs.get('execution_before'):
            where_conditions.append("c.execution_date <= $execution_before")
            params['execution_before'] = kwargs['execution_before']
        
        if kwargs.get('effective_after'):
            where_conditions.append("c.effective_date >= $effective_after")
            params['effective_after'] = kwargs['effective_after']
        
        if kwargs.get('effective_before'):
            where_conditions.append("c.effective_date <= $effective_before")
            params['effective_before'] = kwargs['effective_before']
        
        # Add legal filters
        if kwargs.get('governing_law'):
            where_conditions.append("c.governing_law CONTAINS $governing_law")
            params['governing_law'] = kwargs['governing_law']
        
        if kwargs.get('jurisdiction'):
            where_conditions.append("c.jurisdiction CONTAINS $jurisdiction")
            params['jurisdiction'] = kwargs['jurisdiction']
        
        # Add rights filters
        if kwargs.get('has_sublicense_rights') is not None:
            where_conditions.append("c.right_to_sublicense = $has_sublicense_rights")
            params['has_sublicense_rights'] = kwargs['has_sublicense_rights']
        
        if kwargs.get('has_crosslicensing') is not None:
            where_conditions.append("c.crosslicensing_indicator = $has_crosslicensing")
            params['has_crosslicensing'] = kwargs['has_crosslicensing']
        
        if kwargs.get('has_confidentiality') is not None:
            where_conditions.append("c.confidential_agreement = $has_confidentiality")
            params['has_confidentiality'] = kwargs['has_confidentiality']
        
        # Add patent/product filters
        if kwargs.get('patent_number'):
            query_parts.append("MATCH (c)-[:LICENSES]->(p:Patent)")
            where_conditions.append("p.patent_number CONTAINS $patent_number")
            params['patent_number'] = kwargs['patent_number']
        
        if kwargs.get('product_name'):
            query_parts.append("MATCH (c)-[:LICENSES]->(pr:Product)")
            where_conditions.append("pr.product_name CONTAINS $product_name")
            params['product_name'] = kwargs['product_name']
        
        if kwargs.get('territory'):
            query_parts.append("MATCH (c)-[:COVERS_TERRITORY]->(t:Territory)")
            where_conditions.append("t.territory_name CONTAINS $territory")
            params['territory'] = kwargs['territory']
        
        # Add text search
        if kwargs.get('summary_search'):
            where_conditions.append("c.summary CONTAINS $summary_search")
            params['summary_search'] = kwargs['summary_search']
        
        # Add custom query
        if kwargs.get('custom_query'):
            where_conditions.append(kwargs['custom_query'])
        
        # Combine query parts
        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))
        
        # Add return clause
        query_parts.append("""
            RETURN c.title as title, 
                   c.contract_type as type,
                   c.summary as summary,
                   c.execution_date as execution_date,
                   c.upfront_payment as upfront_payment,
                   c.exclusivity_grant_type as exclusivity,
                   c.oem_type as oem_type,
                   c.governing_law as governing_law
            ORDER BY c.execution_date DESC
            LIMIT 50
        """)
        
        cypher_query = "\n".join(query_parts)
        
        return self._execute_cypher(cypher_query, params)
    
    def _execute_cypher(self, cypher: str, params: dict) -> str:
        """Execute Cypher query and return formatted results"""
        try:
            with self.driver.session() as session:
                result = session.run(cypher, params)
                records = list(result)
                
                if not records:
                    return "No license contracts found matching the specified criteria."
                
                return self._format_results(records)
                
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def _format_results(self, records: list) -> str:
        """Format query results as a readable string"""
        if not records:
            return "No results found."
        
        formatted_results = []
        for i, record in enumerate(records, 1):
            result = f"{i}. {record['title']}\n"
            result += f"   Type: {record['type']}\n"
            result += f"   Execution Date: {record['execution_date'] or 'Not specified'}\n"
            result += f"   Upfront Payment: ${record['upfront_payment']:,.2f}" if record['upfront_payment'] else "   Upfront Payment: Not specified"
            result += f"\n   Exclusivity: {record['exclusivity'] or 'Not specified'}\n"
            result += f"   OEM Type: {record['oem_type'] or 'Not specified'}\n"
            result += f"   Governing Law: {record['governing_law'] or 'Not specified'}\n"
            result += f"   Summary: {record['summary'][:200]}..." if record['summary'] and len(record['summary']) > 200 else f"   Summary: {record['summary'] or 'Not available'}"
            formatted_results.append(result)
        
        return f"Found {len(records)} license contract(s):\n\n" + "\n\n".join(formatted_results) 