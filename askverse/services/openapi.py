from typing import List, Dict, Any
import json
import yaml
from pathlib import Path
import hashlib

class OpenAPIService:
    def __init__(self, specs_dir: str = "specs"):
        self.specs_dir = Path(specs_dir)
        self.specs_dir.mkdir(exist_ok=True)
    
    def _generate_spec_id(self, spec_path: str) -> str:
        """Generate a unique spec ID."""
        return f"api_{hashlib.md5(spec_path.encode()).hexdigest()}"
    
    def _parse_spec(self, spec_path: Path) -> Dict[str, Any]:
        """Parse OpenAPI spec file."""
        content = spec_path.read_text()
        
        # Try parsing as JSON first
        try:
            spec = json.loads(content)
        except json.JSONDecodeError:
            # Try parsing as YAML
            spec = yaml.safe_load(content)
        
        return spec
    
    def _extract_endpoints(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract endpoints from OpenAPI spec."""
        endpoints = []
        
        # Get base URL
        base_url = spec.get("servers", [{}])[0].get("url", "")
        
        # Process paths
        for path, path_item in spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                # Extract endpoint details
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "parameters": operation.get("parameters", []),
                    "request_body": operation.get("requestBody", {}),
                    "responses": operation.get("responses", {}),
                    "tags": operation.get("tags", []),
                    "operation_id": operation.get("operationId", ""),
                    "url": f"{base_url}{path}"
                }
                endpoints.append(endpoint)
        
        return endpoints
    
    def process_spec(self, spec_path: str) -> Dict[str, Any]:
        """Process a single OpenAPI spec file."""
        spec_path = Path(spec_path)
        if not spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")
        
        # Parse spec
        spec = self._parse_spec(spec_path)
        
        # Extract endpoints
        endpoints = self._extract_endpoints(spec)
        
        # Create document
        doc = {
            "id": self._generate_spec_id(str(spec_path)),
            "content": json.dumps(spec, indent=2),
            "source_type": "openapi",
            "source_id": str(spec_path),
            "title": spec.get("info", {}).get("title", spec_path.name),
            "version": spec.get("info", {}).get("version", "unknown"),
            "endpoints": endpoints,
            "last_updated": spec_path.stat().st_mtime
        }
        
        return doc
    
    def process_all_specs(self) -> List[Dict[str, Any]]:
        """Process all OpenAPI spec files in the specs directory."""
        specs = []
        for spec_path in self.specs_dir.glob("**/*.{json,yaml,yml}"):
            try:
                spec = self.process_spec(str(spec_path))
                specs.append(spec)
            except Exception as e:
                print(f"Error processing spec {spec_path}: {e}")
        
        return specs
    
    def search_endpoints(self, query: str) -> List[Dict[str, Any]]:
        """Search for endpoints matching the query."""
        matching_endpoints = []
        
        for spec_path in self.specs_dir.glob("**/*.{json,yaml,yml}"):
            try:
                spec = self.process_spec(str(spec_path))
                
                # Search in endpoints
                for endpoint in spec["endpoints"]:
                    # Check if query matches endpoint details
                    if (
                        query.lower() in endpoint["summary"].lower() or
                        query.lower() in endpoint["description"].lower() or
                        query.lower() in endpoint["path"].lower() or
                        query.lower() in endpoint["operation_id"].lower()
                    ):
                        matching_endpoints.append({
                            "spec_id": spec["id"],
                            "spec_title": spec["title"],
                            "endpoint": endpoint
                        })
            except Exception as e:
                print(f"Error searching spec {spec_path}: {e}")
        
        return matching_endpoints 