import os
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
import networkx as nx
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv

from license_data_models import LicenseContract
from license_extraction import LicenseContractExtractor

load_dotenv()

class LicenseGraphRAGPipeline:
    """Pipeline for ingesting and querying license contracts using NetworkX"""
    
    def __init__(self, model_path: str = None):
        """Initialize the pipeline with all necessary components"""
        self.extractor = LicenseContractExtractor(model_path)
        self.graph = nx.MultiDiGraph()
        self.title_to_contract = {}  # For fast lookup

    def ingest_contract(self, contract_text: str, contract_id: str = None) -> LicenseContract:
        """Ingest a single license contract into the knowledge graph (NetworkX)"""
        cleaned_text = self._clean_contract_text(contract_text)
        contract_data = self.extractor.extract_contract_data(cleaned_text)
        if contract_id:
            contract_data.title = f"{contract_data.title} ({contract_id})"
        self._import_license_contract_to_networkx(contract_data)
        return contract_data

    def _clean_contract_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'<TYPE>.*?</TYPE>', '', text, flags=re.DOTALL)
        text = re.sub(r'<SEQUENCE>.*?</SEQUENCE>', '', text, flags=re.DOTALL)
        text = re.sub(r'<FILENAME>.*?</FILENAME>', '', text, flags=re.DOTALL)
        text = text.replace('\xa0', ' ')
        text = text.replace('\u2019', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        return text.strip()

    def _import_license_contract_to_networkx(self, contract_data: LicenseContract):
        # Add contract node
        self.graph.add_node(contract_data.title, **contract_data.dict())
        self.title_to_contract[contract_data.title] = contract_data
        # Add licensor
        if contract_data.licensor:
            licensor_name = contract_data.licensor.name
            self.graph.add_node(licensor_name, type="Licensor")
            self.graph.add_edge(licensor_name, contract_data.title, type="IS_LICENSOR_OF")
        # Add licensee
        if contract_data.licensee:
            licensee_name = contract_data.licensee.name
            self.graph.add_node(licensee_name, type="Licensee")
            self.graph.add_edge(licensee_name, contract_data.title, type="IS_LICENSEE_OF")
        # Add patents
        for patent in getattr(contract_data, 'licensed_patents', []):
            patent_number = getattr(patent, 'patent_number', None)
            if patent_number:
                self.graph.add_node(patent_number, type="Patent")
                self.graph.add_edge(contract_data.title, patent_number, type="LICENSES")
        # Add products
        for product in getattr(contract_data, 'licensed_products', []):
            product_name = getattr(product, 'product_name', None)
            if product_name:
                self.graph.add_node(product_name, type="Product")
                self.graph.add_edge(contract_data.title, product_name, type="LICENSES")
        # Add territories
        for territory in getattr(contract_data, 'licensed_territory', []):
            territory_name = getattr(territory, 'territory_name', None)
            if territory_name:
                self.graph.add_node(territory_name, type="Territory")
                self.graph.add_edge(contract_data.title, territory_name, type="COVERS_TERRITORY")

    def query_contracts(self, query: str) -> str:
        """Query the knowledge graph using natural language (simple demo)"""
        # For demo: support a few simple queries
        query = query.lower()
        if "upfront payment" in query:
            return self._summarize_upfront_payments()
        elif "exclusive" in query:
            return self._list_exclusive_contracts()
        elif "licensor" in query:
            return self._list_licensors()
        elif "licensee" in query:
            return self._list_licensees()
        elif "summary" in query:
            return self._summarize_contracts()
        else:
            return "Query type not recognized. Try asking about 'upfront payment', 'exclusive', 'licensor', 'licensee', or 'summary'."

    def _summarize_upfront_payments(self) -> str:
        results = []
        for n, d in self.graph.nodes(data=True):
            if d.get('contract_type') == 'License Agreement' and d.get('upfront_payment'):
                results.append(f"{n}: ${d['upfront_payment']}")
        if not results:
            return "No contracts with upfront payments found."
        return "Upfront payments by contract:\n" + "\n".join(results)

    def _list_exclusive_contracts(self) -> str:
        results = []
        for n, d in self.graph.nodes(data=True):
            if d.get('contract_type') == 'License Agreement' and d.get('exclusivity_grant_type') == 'Exclusive':
                results.append(n)
        if not results:
            return "No exclusive contracts found."
        return "Exclusive contracts:\n" + "\n".join(results)

    def _list_licensors(self) -> str:
        licensors = set()
        for u, v, d in self.graph.edges(data=True):
            if d.get('type') == 'IS_LICENSOR_OF':
                licensors.add(u)
        if not licensors:
            return "No licensors found."
        return "Licensors:\n" + "\n".join(licensors)

    def _list_licensees(self) -> str:
        licensees = set()
        for u, v, d in self.graph.edges(data=True):
            if d.get('type') == 'IS_LICENSEE_OF':
                licensees.add(u)
        if not licensees:
            return "No licensees found."
        return "Licensees:\n" + "\n".join(licensees)

    def _summarize_contracts(self) -> str:
        summaries = []
        for n, d in self.graph.nodes(data=True):
            if d.get('contract_type') == 'License Agreement':
                summaries.append(f"{n}: {d.get('summary', 'No summary')}")
        if not summaries:
            return "No contracts found."
        return "Contract summaries:\n" + "\n".join(summaries)

    def get_database_stats(self) -> Dict[str, int]:
        stats = {
            'license_contracts': sum(1 for n, d in self.graph.nodes(data=True) if d.get('contract_type') == 'License Agreement'),
            'licensors': sum(1 for n, d in self.graph.nodes(data=True) if d.get('type') == 'Licensor'),
            'licensees': sum(1 for n, d in self.graph.nodes(data=True) if d.get('type') == 'Licensee'),
            'patents': sum(1 for n, d in self.graph.nodes(data=True) if d.get('type') == 'Patent'),
            'products': sum(1 for n, d in self.graph.nodes(data=True) if d.get('type') == 'Product'),
            'territories': sum(1 for n, d in self.graph.nodes(data=True) if d.get('type') == 'Territory'),
        }
        return stats

    def save_graph(self, path: str):
        nx.write_gpickle(self.graph, path)

    def load_graph(self, path: str):
        self.graph = nx.read_gpickle(path) 