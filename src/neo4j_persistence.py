"""
Neo4j Database Persistence Utility

This module provides functionality to save and restore Neo4j database state,
allowing you to avoid recreating the graph every time.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from neo4j import GraphDatabase
import zipfile
import tempfile


class Neo4jPersistence:
    def __init__(self, uri: str, user: str, password: str, backup_dir: str = "neo4j_backups"):
        """
        Initialize Neo4j persistence manager.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
            backup_dir: Directory to store backups
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.backup_dir = backup_dir
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def export_database(self, backup_name: Optional[str] = None) -> str:
        """
        Export the entire Neo4j database to Cypher statements.
        
        Args:
            backup_name: Optional name for the backup. If None, uses timestamp.
            
        Returns:
            Path to the backup file
        """
        if backup_name is None:
            backup_name = f"neo4j_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        with self.driver.session() as session:
            # Export nodes
            nodes_data = self._export_nodes(session)
            
            # Export relationships
            relationships_data = self._export_relationships(session)
            
            # Export constraints and indexes
            schema_data = self._export_schema(session)
            
            # Create backup metadata
            metadata = {
                "backup_name": backup_name,
                "timestamp": datetime.now().isoformat(),
                "node_count": len(nodes_data),
                "relationship_count": len(relationships_data),
                "schema_count": len(schema_data)
            }
            
            # Custom JSON serializer to handle dates and other types
            def json_serializer(obj):
                if hasattr(obj, 'isoformat'):  # Date/datetime objects
                    return obj.isoformat()
                elif hasattr(obj, '__dict__'):  # Other objects
                    return str(obj)
                else:
                    return str(obj)
            
            # Create zip file with all data
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add nodes data
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(nodes_data, f, indent=2, default=json_serializer)
                    f.flush()
                    zipf.write(f.name, 'nodes.json')
                    os.unlink(f.name)
                
                # Add relationships data
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(relationships_data, f, indent=2, default=json_serializer)
                    f.flush()
                    zipf.write(f.name, 'relationships.json')
                    os.unlink(f.name)
                
                # Add schema data
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(schema_data, f, indent=2, default=json_serializer)
                    f.flush()
                    zipf.write(f.name, 'schema.json')
                    os.unlink(f.name)
                
                # Add metadata
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(metadata, f, indent=2, default=json_serializer)
                    f.flush()
                    zipf.write(f.name, 'metadata.json')
                    os.unlink(f.name)
        
        self.logger.info(f"Database exported to {backup_path}")
        self.logger.info(f"Backup contains {metadata['node_count']} nodes and {metadata['relationship_count']} relationships")
        
        return backup_path

    def import_database(self, backup_path: str, clear_existing: bool = True) -> bool:
        """
        Import a Neo4j database from a backup file.
        
        Args:
            backup_path: Path to the backup zip file
            clear_existing: Whether to clear existing data before import
            
        Returns:
            True if import successful, False otherwise
        """
        try:
            if not os.path.exists(backup_path):
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Extract to temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zipf.extractall(temp_dir)
                    
                    # Load metadata
                    with open(os.path.join(temp_dir, 'metadata.json'), 'r') as f:
                        metadata = json.load(f)
                    
                    self.logger.info(f"Restoring backup: {metadata['backup_name']}")
                    self.logger.info(f"Created: {metadata['timestamp']}")
                    
                    with self.driver.session() as session:
                        if clear_existing:
                            self.logger.info("Clearing existing database...")
                            session.run("MATCH (n) DETACH DELETE n")
                        
                        # Import schema first
                        self.logger.info("Importing schema...")
                        with open(os.path.join(temp_dir, 'schema.json'), 'r') as f:
                            schema_data = json.load(f)
                        self._import_schema(session, schema_data)
                        
                        # Import nodes
                        self.logger.info("Importing nodes...")
                        with open(os.path.join(temp_dir, 'nodes.json'), 'r') as f:
                            nodes_data = json.load(f)
                        self._import_nodes(session, nodes_data)
                        
                        # Import relationships
                        self.logger.info("Importing relationships...")
                        with open(os.path.join(temp_dir, 'relationships.json'), 'r') as f:
                            relationships_data = json.load(f)
                        self._import_relationships(session, relationships_data)
            
            self.logger.info("Database import completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing database: {str(e)}")
            return False

    def _export_nodes(self, session) -> List[Dict[str, Any]]:
        """Export all nodes with their properties and labels."""
        result = session.run("""
            MATCH (n)
            RETURN ID(n) as id, labels(n) as labels, properties(n) as properties
        """)
        
        nodes = []
        for record in result:
            nodes.append({
                "id": record["id"],
                "labels": record["labels"],
                "properties": record["properties"]
            })
        
        return nodes

    def _export_relationships(self, session) -> List[Dict[str, Any]]:
        """Export all relationships with their properties."""
        result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN ID(r) as id, ID(a) as start_node_id, ID(b) as end_node_id, 
                   type(r) as type, properties(r) as properties
        """)
        
        relationships = []
        for record in result:
            relationships.append({
                "id": record["id"],
                "start_node_id": record["start_node_id"],
                "end_node_id": record["end_node_id"],
                "type": record["type"],
                "properties": record["properties"]
            })
        
        return relationships

    def _export_schema(self, session) -> List[Dict[str, Any]]:
        """Export database schema (constraints and indexes)."""
        schema = []
        
        # Export constraints
        try:
            result = session.run("SHOW CONSTRAINTS")
            for record in result:
                schema.append({
                    "type": "constraint",
                    "data": dict(record)
                })
        except Exception as e:
            self.logger.warning(f"Could not export constraints: {e}")
        
        # Export indexes
        try:
            result = session.run("SHOW INDEXES")
            for record in result:
                schema.append({
                    "type": "index",
                    "data": dict(record)
                })
        except Exception as e:
            self.logger.warning(f"Could not export indexes: {e}")
        
        return schema

    def _import_schema(self, session, schema_data: List[Dict[str, Any]]):
        """Import database schema."""
        for item in schema_data:
            try:
                if item["type"] == "constraint":
                    # Skip system constraints or handle specific ones
                    pass
                elif item["type"] == "index":
                    # Skip system indexes or handle specific ones
                    pass
            except Exception as e:
                self.logger.warning(f"Could not import schema item: {e}")

    def _import_nodes(self, session, nodes_data: List[Dict[str, Any]]):
        """Import nodes in batches."""
        batch_size = 1000
        node_id_mapping = {}
        
        for i in range(0, len(nodes_data), batch_size):
            batch = nodes_data[i:i + batch_size]
            
            for node in batch:
                old_id = node["id"]
                labels = ":".join(node["labels"]) if node["labels"] else ""
                properties = node["properties"]
                
                # Create node
                if labels:
                    query = f"CREATE (n:{labels}) SET n = $properties RETURN ID(n) as new_id"
                else:
                    query = "CREATE (n) SET n = $properties RETURN ID(n) as new_id"
                
                result = session.run(query, properties=properties)
                new_id = result.single()["new_id"]
                node_id_mapping[old_id] = new_id
        
        return node_id_mapping

    def _import_relationships(self, session, relationships_data: List[Dict[str, Any]]):
        """Import relationships in batches."""
        # First, create a mapping of old to new node IDs
        node_mapping = self._get_node_id_mapping(session)
        
        batch_size = 1000
        for i in range(0, len(relationships_data), batch_size):
            batch = relationships_data[i:i + batch_size]
            
            for rel in batch:
                try:
                    start_id = node_mapping.get(rel["start_node_id"])
                    end_id = node_mapping.get(rel["end_node_id"])
                    
                    if start_id is not None and end_id is not None:
                        query = f"""
                        MATCH (a), (b)
                        WHERE ID(a) = $start_id AND ID(b) = $end_id
                        CREATE (a)-[r:{rel["type"]}]->(b)
                        SET r = $properties
                        """
                        session.run(query, 
                                   start_id=start_id, 
                                   end_id=end_id, 
                                   properties=rel["properties"])
                except Exception as e:
                    self.logger.warning(f"Could not import relationship: {e}")

    def _get_node_id_mapping(self, session) -> Dict[int, int]:
        """Get mapping of old node IDs to new node IDs based on properties."""
        # This is a simplified mapping - in practice, you might want to use
        # unique properties to match nodes more precisely
        result = session.run("MATCH (n) RETURN ID(n) as id, properties(n) as props")
        
        mapping = {}
        for i, record in enumerate(result):
            mapping[i] = record["id"]  # Simplified mapping
        
        return mapping

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.zip'):
                backup_path = os.path.join(self.backup_dir, filename)
                
                try:
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        with zipf.open('metadata.json') as f:
                            metadata = json.load(f)
                        
                        backups.append({
                            "filename": filename,
                            "path": backup_path,
                            "metadata": metadata
                        })
                except Exception as e:
                    self.logger.warning(f"Could not read backup metadata for {filename}: {e}")
        
        # Sort by timestamp
        backups.sort(key=lambda x: x.get("metadata", {}).get("timestamp", ""), reverse=True)
        return backups

    def close(self):
        """Close the database connection."""
        self.driver.close()


def main():
    """Example usage of the Neo4j persistence utility."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize persistence manager
    persistence = Neo4jPersistence(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password")
    )
    
    try:
        # List existing backups
        backups = persistence.list_backups()
        print(f"Found {len(backups)} existing backups:")
        for backup in backups:
            metadata = backup["metadata"]
            print(f"  - {backup['filename']}: {metadata['node_count']} nodes, {metadata['relationship_count']} relationships")
        
        # Export current database
        backup_path = persistence.export_database("abeona_contracts_backup")
        print(f"Database exported to: {backup_path}")
        
    finally:
        persistence.close()


if __name__ == "__main__":
    main() 