"""
Schema transformers for different output formats.
"""
from typing import List, Dict, Any
from services.search.base import SchemaTransformer, SearchResult
import logging

class DefaultSchemaTransformer(SchemaTransformer):
    """Default transformer that maintains the basic structure"""

    def transform(self, results: List[SearchResult]) -> Dict[str, Any]:
        transformed_results = [
            {
                'id': result.id,
                'type': result.type,
                'title': result.title,
                'description': result.description,
                'data': result.data
            }
            for result in results
        ]
        
        # Get pagination info from the first result
        query = results[0]._query if results else None
        total = results[0]._total if results else 0
        page = query.page if query else 1
        per_page = query.per_page if query else 10
        
        return {
            'results': transformed_results,
            'total': total,  # Total number of results from database
            'page': page,  # Current page
            'per_page': per_page  # Results per page
        }

class CompactSchemaTransformer(SchemaTransformer):
    """Transformer that provides a minimal response format"""

    def transform(self, results: List[SearchResult]) -> Dict[str, Any]:
        return {
            'results': [
                {
                    'id': result.id,
                    'title': result.title,
                    'type': result.type
                }
                for result in results
            ]
        }

class DetailedSchemaTransformer(SchemaTransformer):
    """Transformer that provides an expanded response format with all data"""

    def transform(self, results: List[SearchResult]) -> Dict[str, Any]:
        transformed = []
        for result in results:
            item = {
                'id': result.id,
                'type': result.type,
                'title': result.title,
                'description': result.description
            }

            # Flatten data into root level
            if result.data:
                item.update(result.data)

            transformed.append(item)

        return {
            'results': transformed,
            'result_count': len(transformed)
        }

class ClinicalStudyCustomTransformer(SchemaTransformer):
    """Custom transformer for clinical studies with specific response format"""
    
    def transform(self, results: List[SearchResult]) -> Dict[str, Any]:
        logger = logging.getLogger(__name__)
        logger.debug(f"ClinicalStudyCustomTransformer.transform called with {len(results)} results")
        
        # Get pagination info from the first result
        query = results[0]._query if results else None
        total = results[0]._total if results else 0
        page = query.page if query else 1
        per_page = query.per_page if query else 10
        
        logger.debug(f"Input results types: {type(results[0]) if results else 'No results'}")
        logger.debug(f"First result fields: {vars(results[0]) if results else 'No results'}")
        
        transformed_results = []
        for i, result in enumerate(results):
            data = result.data or {}
            
            # Get data_products from result
            data_products = result.data_products or []
            logger.debug(f"Processing result {i} ID {result.id} with {len(data_products)} data products and {len(data)} data fields")
            logger.debug(f"Data fields: {list(data.keys())}")
            
            # Create the restructured result
            transformed_result = {
                'id': result.id,
                'title': result.title,
                'description': result.description,
                'relevance_score': result.relevance_score,
                'study_details': {
                    'status': data.get('status'),
                    'phase': data.get('phase'),
                    'drug': data.get('drug'),
                    'institution': data.get('institution'),
                    'participant_count': data.get('participant_count'),
                    'start_date': data.get('start_date'),
                    'end_date': data.get('end_date'),
                    'indication_category': data.get('indication_category'),
                    'procedure_category': data.get('procedure_category'),
                    'severity': data.get('severity'),
                    'risk_level': data.get('risk_level'),
                    'duration': data.get('duration')
                },
                'data_products': data_products
            }
            
            transformed_results.append(transformed_result)
        
        final_result = {
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page
            },
            'results': transformed_results
        }
        
        logger.debug(f"Transformed structure: {list(final_result.keys())}")
        logger.debug(f"First transformed result keys: {list(transformed_results[0].keys()) if transformed_results else 'No results'}")
        
        return final_result

class ScientificPaperSchemaTransformer(SchemaTransformer):
    """Specific transformer for scientific paper results with citation formatting"""

    def transform(self, results: List[SearchResult]) -> Dict[str, Any]:
        transformed_results = []
        for result in results:
            data = result.data or {}

            transformed_result = {
                'id': result.id,
                'type': result.type,
                'title': result.title,
                'description': result.description,
                'data': {
                    'authors': data.get('authors', []),
                    'publication_date': data.get('publication_date'),
                    'journal': data.get('journal'),
                    'doi': data.get('doi'),
                    'keywords': data.get('keywords', []),
                    'citations_count': data.get('citations_count', 0),
                    'references': data.get('references', [])
                }
            }
            transformed_results.append(transformed_result)

        return {
            'results': transformed_results,
            'result_count': len(transformed_results)
        }

class DataDomainSchemaTransformer(SchemaTransformer):
    """Specific transformer for data domain data with schema validation info"""

    def transform(self, results: List[SearchResult]) -> Dict[str, Any]:
        transformed_results = []
        for result in results:
            data = result.data or {}

            transformed_result = {
                'id': result.id,
                'domain_name': result.title,
                'description': result.description,
                'schema': {
                    'format': data.get('data_format'),
                    'definition': data.get('schema_definition'),
                    'validation_rules': data.get('validation_rules'),
                },
                'examples': {
                    'sample_data': data.get('sample_data')
                },
                'ownership': {
                    'owner': data.get('owner'),
                    'created_at': data.get('created_at'),
                    'updated_at': data.get('updated_at')
                }
            }
            transformed_results.append(transformed_result)

        return {
            'results': transformed_results
        }