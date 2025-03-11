from datetime import datetime
from flask_login import UserMixin
from extensions import db
import logging

logger = logging.getLogger(__name__)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    api_token = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

class ClinicalStudy(db.Model):
    """Model for clinical studies"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Active')
    phase = db.Column(db.String(50))  # Phase I, II, III, IV
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    institution = db.Column(db.String(255))
    participant_count = db.Column(db.Integer)

    # Relationships
    indications = db.relationship('StudyIndication', back_populates='study')
    procedures = db.relationship('StudyProcedure', back_populates='study')

    def __repr__(self):
        return f'<ClinicalStudy {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'phase': self.phase,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'institution': self.institution,
            'participant_count': self.participant_count
        }

class Indication(db.Model):
    """Model for medical indications"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # e.g., Cardiovascular, Neurological, etc.
    severity = db.Column(db.String(50))   # e.g., Mild, Moderate, Severe
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    studies = db.relationship('StudyIndication', back_populates='indication')

    def __repr__(self):
        return f'<Indication {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'severity': self.severity
        }

class Procedure(db.Model):
    """Model for medical procedures"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # e.g., Surgical, Diagnostic, etc.
    risk_level = db.Column(db.String(50)) # e.g., Low, Medium, High
    duration = db.Column(db.Integer)      # Typical duration in minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    studies = db.relationship('StudyProcedure', back_populates='procedure')

    def __repr__(self):
        return f'<Procedure {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'risk_level': self.risk_level,
            'duration': self.duration
        }

class StudyIndication(db.Model):
    """Association table between studies and indications"""
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('clinical_study.id'), nullable=False)
    indication_id = db.Column(db.Integer, db.ForeignKey('indication.id'), nullable=False)
    primary = db.Column(db.Boolean, default=False)  # Flag for primary indication
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    study = db.relationship('ClinicalStudy', back_populates='indications')
    indication = db.relationship('Indication', back_populates='studies')

    def __repr__(self):
        return f'<StudyIndication {self.study_id}:{self.indication_id}>'

class StudyProcedure(db.Model):
    """Association table between studies and procedures"""
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('clinical_study.id'), nullable=False)
    procedure_id = db.Column(db.Integer, db.ForeignKey('procedure.id'), nullable=False)
    required = db.Column(db.Boolean, default=True)  # Flag if procedure is required
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    study = db.relationship('ClinicalStudy', back_populates='procedures')
    procedure = db.relationship('Procedure', back_populates='studies')

    def __repr__(self):
        return f'<StudyProcedure {self.study_id}:{self.procedure_id}>'

class SearchLog(db.Model):
    """Model for logging search queries with enhanced details for timeline view"""
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50))
    filters = db.Column(db.JSON)  # Store applied filters
    results_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # IPv6 compatible length

    # New fields for enhanced search history
    status = db.Column(db.String(20), default='completed')  # Status of the search (completed, failed)
    execution_time = db.Column(db.Float)  # Time taken to execute the search in seconds
    top_result_id = db.Column(db.Integer)  # ID of the top result
    top_result_type = db.Column(db.String(50))  # Type of the top result (study, indication, procedure)
    top_result_title = db.Column(db.String(255))  # Title of the top result

    def __repr__(self):
        return f'<SearchLog {self.query}>'

    def to_dict(self):
        """Convert search log to dictionary for API response"""
        try:
            return {
                'id': self.id,
                'query': self.query,
                'category': self.category,
                'filters': self.filters if isinstance(self.filters, dict) else {},
                'results_count': self.results_count,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'status': self.status,
                'execution_time': self.execution_time,
                'top_result': {
                    'id': self.top_result_id,
                    'type': self.top_result_type,
                    'title': self.top_result_title
                } if self.top_result_id else None
            }
        except Exception as e:
            logger.error(f"Error converting SearchLog to dict: {e}")
            return {}