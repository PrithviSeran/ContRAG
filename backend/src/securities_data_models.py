from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum

class SecurityType(str, Enum):
    """Types of securities that can be issued"""
    COMMON_STOCK = "common_stock"
    PREFERRED_STOCK = "preferred_stock"
    WARRANT = "warrant"
    OPTION = "option"
    CONVERTIBLE_NOTE = "convertible_note"
    DEBT = "debt"
    UNIT = "unit"  # Combination of securities

class PartyRole(str, Enum):
    """Roles of parties in securities transactions"""
    ISSUER = "issuer"
    PURCHASER = "purchaser"
    INVESTOR = "investor"
    UNDERWRITER = "underwriter"
    PLACEMENT_AGENT = "placement_agent"
    LEGAL_COUNSEL = "legal_counsel"

class RegistrationStatus(str, Enum):
    """Registration status of securities"""
    REGISTERED = "registered"
    EXEMPT = "exempt"
    RESTRICTED = "restricted"
    RULE_144A = "rule_144a"

class Party(BaseModel):
    """Represents a party to the securities transaction"""
    name: str
    role: PartyRole
    entity_type: Optional[str] = None  # Corporation, LLC, Individual, etc.
    jurisdiction: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    contact_info: Optional[str] = None

class Security(BaseModel):
    """Represents a security being issued"""
    security_type: SecurityType
    number_of_shares: Optional[int] = None
    par_value: Optional[float] = None
    purchase_price_per_share: Optional[float] = None
    total_purchase_price: Optional[float] = None
    exercise_price: Optional[float] = None  # For warrants/options
    conversion_terms: Optional[str] = None
    dividend_rate: Optional[float] = None
    voting_rights: Optional[str] = None
    liquidation_preference: Optional[str] = None
    anti_dilution_provisions: Optional[str] = None

class ClosingConditions(BaseModel):
    """Conditions that must be met for closing"""
    condition_description: str
    is_waivable: bool = True
    responsible_party: Optional[str] = None
    deadline: Optional[date] = None

class RegistrationRights(BaseModel):
    """Registration rights granted to investors"""
    demand_rights: Optional[int] = None  # Number of demand registrations
    piggyback_rights: bool = False
    form_s3_rights: bool = False
    registration_expenses: Optional[str] = None  # Who pays expenses
    holdback_period: Optional[int] = None  # Days investors must hold back

class ResaleRestrictions(BaseModel):
    """Restrictions on resale of securities"""
    holding_period: Optional[int] = None  # Days
    volume_limitations: Optional[str] = None
    manner_of_sale: Optional[str] = None
    notice_requirements: Optional[str] = None
    rule_144_compliance: bool = False

class Representation(BaseModel):
    """Representations and warranties"""
    category: str  # Organization, Authority, Financial, etc.
    description: str
    is_material: bool = True
    survival_period: Optional[int] = None  # Days after closing

class SecuritiesContract(BaseModel):
    """Main securities purchase agreement model"""
    
    # Basic Contract Information
    title: str
    contract_type: str = "Securities Purchase Agreement"
    summary: Optional[str] = None
    
    # Key Dates
    execution_date: Optional[date] = None
    closing_date: Optional[date] = None
    effectiveness_date: Optional[date] = None
    
    # Parties
    parties: List[Party] = []
    
    # Securities Details
    securities: List[Security] = []
    total_offering_amount: Optional[float] = None
    
    # Registration and Compliance
    registration_status: Optional[RegistrationStatus] = None
    registration_rights: Optional[RegistrationRights] = None
    resale_restrictions: Optional[ResaleRestrictions] = None
    
    # Transaction Terms
    closing_conditions: List[ClosingConditions] = []
    use_of_proceeds: Optional[str] = None
    expenses: Optional[str] = None
    
    # Legal Terms
    representations_warranties: List[Representation] = []
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    termination_rights: Optional[str] = None
    
    # Disclosure and Reporting
    disclosure_requirements: Optional[str] = None
    periodic_reporting: Optional[str] = None
    
    # Additional Terms
    board_rights: Optional[str] = None
    information_rights: Optional[str] = None
    preemptive_rights: Optional[str] = None
    tag_along_rights: Optional[str] = None
    drag_along_rights: Optional[str] = None
    
    # Risk Factors and Disclosures
    risk_factors: List[str] = []
    material_changes: Optional[str] = None
    
    # Financial Information
    recent_financials: Optional[str] = None
    auditor_info: Optional[str] = None
    
    # Regulatory Compliance
    sec_exemption: Optional[str] = None  # Rule 506, etc.
    state_exemptions: Optional[str] = None
    international_considerations: Optional[str] = None

class SecuritiesTransaction(BaseModel):
    """Represents a complete securities transaction"""
    contract: SecuritiesContract
    transaction_id: Optional[str] = None
    status: str = "pending"  # pending, closed, terminated
    created_at: Optional[date] = None
    updated_at: Optional[date] = None 