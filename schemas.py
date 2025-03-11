from marshmallow import Schema, fields, pre_dump
import logging

logger = logging.getLogger(__name__)

class SearchResultSchema(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)
    description = fields.Str()
    type = fields.Str(required=True)
    relevance_score = fields.Float()
    # Make sure all filter fields are explicitly defined
    status = fields.Str(allow_none=True)
    phase = fields.Str(allow_none=True)
    indication_category = fields.Str(allow_none=True)
    procedure_category = fields.Str(allow_none=True)
    severity = fields.Str(allow_none=True)
    risk_level = fields.Str(allow_none=True)
    duration = fields.Int(allow_none=True)
    start_date = fields.DateTime(allow_none=True)
    end_date = fields.DateTime(allow_none=True)

class SearchResponseSchema(Schema):
    results = fields.List(fields.Nested(SearchResultSchema))
    total = fields.Int(required=True)
    page = fields.Int(required=True)
    per_page = fields.Int(required=True)

class SuggestionSchema(Schema):
    text = fields.Str(required=True)
    type = fields.Str(required=True)

class SuggestResponseSchema(Schema):
    suggestions = fields.List(fields.Nested(SuggestionSchema))

class TopResultSchema(Schema):
    id = fields.Int(allow_none=True)
    type = fields.Str(allow_none=True)
    title = fields.Str(allow_none=True)

class SearchHistoryItemSchema(Schema):
    id = fields.Int(required=True)
    query = fields.Str(required=True)
    category = fields.Str(allow_none=True)
    filters = fields.Dict(allow_none=True)
    results_count = fields.Int(allow_none=True)
    created_at = fields.DateTime(required=True)
    status = fields.Str(allow_none=True)
    execution_time = fields.Float(allow_none=True)
    top_result = fields.Nested(TopResultSchema, allow_none=True)

    @pre_dump
    def prepare_data(self, data, **kwargs):
        """Prepare data for serialization"""
        if not data:
            return {}

        try:
            top_result = None
            if data.top_result_id:
                top_result = {
                    'id': data.top_result_id,
                    'type': data.top_result_type,
                    'title': data.top_result_title
                }

            return {
                'id': data.id,
                'query': data.query,
                'category': data.category,
                'filters': data.filters if isinstance(data.filters, dict) else {},
                'results_count': data.results_count,
                'created_at': data.created_at,
                'status': data.status,
                'execution_time': data.execution_time,
                'top_result': top_result
            }
        except Exception as e:
            logger.error(f"Error preparing search history item: {e}")
            return {}

class SearchHistoryResponseSchema(Schema):
    history = fields.List(fields.Nested(SearchHistoryItemSchema))
    total = fields.Int(required=True)

class DataProductSchema(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)
    description = fields.Str()
    type = fields.Str()
    format = fields.Str()
    study_id = fields.Int(required=True)
    created_at = fields.DateTime()

class CollectionItemSchema(Schema):
    id = fields.Int(required=True)
    data_product = fields.Nested(DataProductSchema)
    added_at = fields.DateTime()

class CollectionSchema(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)
    description = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    items = fields.List(fields.Nested(CollectionItemSchema))