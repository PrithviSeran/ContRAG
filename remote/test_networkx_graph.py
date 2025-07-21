import os
from license_data_models import LicenseContract, Party, LicensedPatent, LicensedProduct, LicensedTerritory
from license_pipeline_runner import LicenseGraphRAGPipeline

def build_manual_contracts(pipeline):
    # Create a few manual contracts
    contract1 = LicenseContract(
        title="LICENSE AGREEMENT - ALPHA",
        contract_type="License Agreement",
        summary="Alpha Corp grants Beta LLC an exclusive license to use Patent 123 in the US.",
        execution_date="2023-01-01",
        effective_date="2023-01-15",
        licensor=Party(name="Alpha Corp", entity_type="corporation", jurisdiction="Delaware"),
        licensee=Party(name="Beta LLC", entity_type="LLC", jurisdiction="California"),
        exclusivity_grant_type="Exclusive",
        upfront_payment=100000.0,
        licensed_patents=[LicensedPatent(patent_number="123", patent_title="Super Widget")],
        licensed_products=[LicensedProduct(product_name="WidgetX", description="Advanced widget")],
        licensed_territory=[LicensedTerritory(territory_name="United States")],
    )
    contract2 = LicenseContract(
        title="LICENSE AGREEMENT - GAMMA",
        contract_type="License Agreement",
        summary="Gamma Inc grants Delta Ltd a nonexclusive license to use Patent 456 in Canada.",
        execution_date="2022-06-01",
        effective_date="2022-07-01",
        licensor=Party(name="Gamma Inc", entity_type="corporation", jurisdiction="New York"),
        licensee=Party(name="Delta Ltd", entity_type="Ltd", jurisdiction="Ontario"),
        exclusivity_grant_type="Nonexclusive",
        upfront_payment=50000.0,
        licensed_patents=[LicensedPatent(patent_number="456", patent_title="Mega Gadget")],
        licensed_products=[LicensedProduct(product_name="GadgetPro", description="Professional gadget")],
        licensed_territory=[LicensedTerritory(territory_name="Canada")],
    )
    contract3 = LicenseContract(
        title="LICENSE AGREEMENT - EPSILON",
        contract_type="License Agreement",
        summary="Epsilon LLC grants Zeta GmbH a sole license to use Patent 789 in Europe.",
        execution_date="2021-03-15",
        effective_date="2021-04-01",
        licensor=Party(name="Epsilon LLC", entity_type="LLC", jurisdiction="Texas"),
        licensee=Party(name="Zeta GmbH", entity_type="GmbH", jurisdiction="Germany"),
        exclusivity_grant_type="Sole",
        upfront_payment=75000.0,
        licensed_patents=[LicensedPatent(patent_number="789", patent_title="Ultra Device")],
        licensed_products=[LicensedProduct(product_name="DeviceUltra", description="Ultra device")],
        licensed_territory=[LicensedTerritory(territory_name="Europe")],
    )
    # Ingest contracts
    pipeline._import_license_contract_to_networkx(contract1)
    pipeline._import_license_contract_to_networkx(contract2)
    pipeline._import_license_contract_to_networkx(contract3)

def main():
    print("🧪 TESTING NETWORKX KNOWLEDGE GRAPH (NO LLAMA)")
    from license_pipeline_runner import LicenseGraphRAGPipeline
    pipeline = LicenseGraphRAGPipeline(model_path=None)  # model_path not needed
    build_manual_contracts(pipeline)
    print("\nDatabase stats:")
    print(pipeline.get_database_stats())
    print("\n--- Contract Summaries ---")
    print(pipeline.query_contracts("summary"))
    print("\n--- Licensors ---")
    print(pipeline.query_contracts("licensor"))
    print("\n--- Licensees ---")
    print(pipeline.query_contracts("licensee"))
    print("\n--- Exclusive Contracts ---")
    print(pipeline.query_contracts("exclusive"))
    print("\n--- Upfront Payments ---")
    print(pipeline.query_contracts("upfront payment"))

if __name__ == "__main__":
    main() 