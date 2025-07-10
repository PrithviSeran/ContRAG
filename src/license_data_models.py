from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum

class ExclusivityGrantType(str, Enum):
    """Types of exclusivity grants in license agreements"""
    EXCLUSIVE = "Exclusive"
    SOLE = "Sole"
    NONEXCLUSIVE = "Nonexclusive"

class OEMType(str, Enum):
    """Types of OEM agreements"""
    MSA = "MSA"  # Traditional manufacturing and supply agreement
    B2B = "B2B"  # B2B agreement of supplier providing materials to manufacturer
    VAR = "VAR"  # Value-added-reseller
    PL = "PL"    # Private label
    DM = "DM"    # Design and manufacture
    CS = "CS"    # Component supply
    SOEM = "SOEM"  # Software OEM

class ContractTermType(str, Enum):
    """Types of contract terms"""
    PERPETUAL = "perpetual"
    FIXED_END_DATE = "fixed end date"
    VARIABLE_END = "variable end"

class AssignmentRestrictionType(str, Enum):
    """Types of assignment restrictions"""
    NON_TRANSFERABLE = "non-transferable without agreement by licensor"
    FULLY_TRANSFERABLE = "fully transferable"
    CUSTOM = "custom clause"

class Party(BaseModel):
    """Represents a party to the license agreement"""
    name: str
    address: Optional[str] = None
    entity_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    contact_info: Optional[str] = None

class ExclusivityMilestone(BaseModel):
    """Milestones required to maintain exclusive rights"""
    description: str
    sales_target: Optional[str] = None
    deadline: Optional[date] = None
    consequences: Optional[str] = None

class SublicenseRestriction(BaseModel):
    """Restrictions on sublicensing"""
    restriction_type: str  # approval required, number limits, etc.
    description: str
    conditions: Optional[str] = None

class LicensedPatent(BaseModel):
    """Represents a licensed patent"""
    patent_number: str
    patent_title: Optional[str] = None
    filing_date: Optional[date] = None
    issue_date: Optional[date] = None

class LicensedProduct(BaseModel):
    """Represents a licensed product"""
    product_name: str
    description: Optional[str] = None
    category: Optional[str] = None

class LicensedTerritory(BaseModel):
    """Represents a licensed territory"""
    territory_name: str
    territory_type: Optional[str] = None  # country, region, worldwide, etc.
    restrictions: Optional[str] = None

class ClosingCondition(BaseModel):
    """Conditions that must be met for agreement effectiveness"""
    condition_description: str
    is_waivable: bool = True
    responsible_party: Optional[str] = None
    deadline: Optional[date] = None

class DiligenceClause(BaseModel):
    """Diligence requirements for the licensee"""
    requirement_type: str  # development, commercialization, etc.
    description: str
    timeline: Optional[str] = None
    consequences: Optional[str] = None

class ExhibitAttachment(BaseModel):
    """Represents an exhibit or attachment to the agreement"""
    name: str
    type: Optional[str] = None  # exhibit, attachment, schedule, etc.
    description: Optional[str] = None
    reference_section: Optional[str] = None

class LicenseContract(BaseModel):
    """Main license agreement model"""
    
    # Basic Contract Information
    title: str
    contract_type: str = "License Agreement"
    summary: Optional[str] = None
    
    # Key Dates
    execution_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    
    # Parties
    licensor: Optional[Party] = None
    licensee: Optional[Party] = None
    
    # Agreement Grants
    agreement_grants: Optional[str] = None  # summaries of all grant clauses
    
    # Exclusivity
    exclusivity_grant_type: Optional[ExclusivityGrantType] = None
    exclusivity_milestones: List[ExclusivityMilestone] = []
    
    # Sublicensing
    right_to_sublicense: Optional[bool] = None
    sublicense_restrictions: List[SublicenseRestriction] = []
    
    # Cross-licensing
    crosslicensing_indicator: Optional[bool] = None
    
    # Licensed Materials
    licensed_field_of_use: Optional[str] = None
    licensed_patents: List[LicensedPatent] = []
    licensed_products: List[LicensedProduct] = []
    licensed_territory: List[LicensedTerritory] = []
    
    # Contract Terms
    contract_term: Optional[ContractTermType] = None
    contract_term_details: Optional[str] = None  # specific dates or conditions
    
    # Releases and Covenants
    contract_releases: Optional[str] = None
    non_compete_covenant_indicator: Optional[bool] = None
    
    # Rights
    retained_licensor_rights: Optional[str] = None
    product_branding_rights: Optional[bool] = None
    
    # OEM Information
    oem_type: Optional[OEMType] = None
    
    # Use Restrictions
    license_use_restrictions: Optional[str] = None
    
    # Obligations
    licensor_obligations: Optional[str] = None  # semicolon-separated list
    
    # Improvements
    licensor_improvements_clause: Optional[str] = None
    licensee_improvements_clause: Optional[str] = None
    licensee_right_to_improvements: Optional[bool] = None
    
    # Related Parties
    related_parties_licensor: Optional[str] = None
    related_parties_licensee: Optional[str] = None
    related_parties_unknown: Optional[str] = None
    
    # Financial Terms
    upfront_payment: Optional[float] = None
    stacking_clause_indicator: Optional[bool] = None
    stacking_clause_terms: Optional[str] = None
    most_favored_nations_clause: Optional[bool] = None
    
    # Indemnities
    licensee_infringement_indemnities: Optional[str] = None
    licensor_product_liability_indemnities: Optional[str] = None
    licensee_product_liability_indemnities: Optional[str] = None
    
    # Delivery and Supply
    delivery_supply: Optional[str] = None
    
    # Relationship
    relationship_between_contract_parties_clause: Optional[str] = None
    
    # Warranties
    warranties_litigation: Optional[str] = None
    warranties_infringement: Optional[str] = None
    warranties_ip_sufficiency: Optional[str] = None
    warranties_product_or_service: Optional[str] = None
    
    # Assignment
    assignment_restrictions: Optional[AssignmentRestrictionType] = None
    assignment_restrictions_details: Optional[str] = None
    
    # Insurance and Audit
    insurance_clause_indicator: Optional[bool] = None
    audit_clause: Optional[str] = None
    
    # Delivery and Performance
    late_delivery_clauses: Optional[str] = None
    diligence_clause: List[DiligenceClause] = []
    
    # Confidentiality
    confidential_agreement: Optional[bool] = None
    confidential_materials: Optional[str] = None
    
    # Patent Management
    patent_prosecution_responsibilities: Optional[str] = None
    suspected_infringement_clause: Optional[str] = None
    
    # Legal Representatives
    legal_representative_organization: Optional[str] = None
    legal_representative_lawyer: Optional[str] = None
    
    # Exhibits and Attachments
    list_of_exhibits_and_attachments_in_contract: List[ExhibitAttachment] = []
    
    # Additional Terms
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    termination_rights: Optional[str] = None
    dispute_resolution: Optional[str] = None
    
    # Risk Factors and Disclosures
    risk_factors: List[str] = []
    material_changes: Optional[str] = None
    
    # Regulatory Compliance
    regulatory_requirements: Optional[str] = None
    export_control: Optional[str] = None

class LicenseTransaction(BaseModel):
    """Represents a complete license transaction"""
    contract: LicenseContract
    transaction_id: Optional[str] = None
    status: str = "pending"  # pending, active, terminated, expired
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    version: Optional[str] = None
    amendments: List[str] = [] 