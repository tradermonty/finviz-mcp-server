"""
Field Discovery Metadata Classes
Supporting classes for field metadata management and validation
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import difflib


@dataclass
class FieldMetadata:
    """Metadata for a single field"""
    name: str
    display_name: str
    category: str
    description: str
    data_type: str
    format_info: str = ""
    special_values: List[str] = None
    related_fields: List[str] = None
    usage_examples: List[str] = None
    
    def __post_init__(self):
        if self.special_values is None:
            self.special_values = []
        if self.related_fields is None:
            self.related_fields = []
        if self.usage_examples is None:
            self.usage_examples = []


@dataclass
class FieldCategory:
    """Category information for field grouping"""
    id: str
    name: str
    icon: str
    description: str
    field_count: int
    
    def get_display_name(self) -> str:
        return f"{self.icon} {self.name} ({self.field_count} fields)"


@dataclass
class ValidationResult:
    """Result of field validation"""
    all_valid: bool
    valid_fields: List[str]
    invalid_fields: List[str] 
    suggestions: Dict[str, List[str]]
    
    def get_summary(self) -> str:
        """Get summary string of validation results"""
        summary = f"{len(self.valid_fields)} valid, {len(self.invalid_fields)} invalid fields"
        if self.valid_fields:
            summary += f" - Valid: {', '.join(self.valid_fields[:3])}"
            if len(self.valid_fields) > 3:
                summary += f" and {len(self.valid_fields) - 3} more"
        if self.invalid_fields:
            summary += f" - Invalid: {', '.join(self.invalid_fields[:3])}"
            if len(self.invalid_fields) > 3:
                summary += f" and {len(self.invalid_fields) - 3} more"
        return summary


class FieldSearchEngine:
    """Search engine for field discovery"""
    
    def __init__(self, fields: Dict[str, FieldMetadata]):
        self.fields = fields
    
    def search(self, keyword: str, category: Optional[str] = None) -> List[FieldMetadata]:
        """Search for fields matching keyword and optional category"""
        if not keyword or not keyword.strip():
            return []
        
        keyword_lower = keyword.strip().lower()
        matches = []
        
        for field_name, metadata in self.fields.items():
            # Skip if category filter doesn't match
            if category and metadata.category.lower() != category.lower():
                continue
            
            # Check for matches in field name
            if keyword_lower in field_name.lower():
                matches.append((metadata, self._calculate_relevance(keyword_lower, metadata, "name")))
                continue
            
            # Check for matches in display name
            if keyword_lower in metadata.display_name.lower():
                matches.append((metadata, self._calculate_relevance(keyword_lower, metadata, "display")))
                continue
            
            # Check for matches in description
            if keyword_lower in metadata.description.lower():
                matches.append((metadata, self._calculate_relevance(keyword_lower, metadata, "description")))
                continue
        
        # Sort by relevance (higher scores first) and return metadata objects
        matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in matches]
    
    def _calculate_relevance(self, keyword: str, metadata: FieldMetadata, match_type: str) -> int:
        """Calculate relevance score for ranking"""
        score = 0
        
        # Higher score for name matches
        if match_type == "name":
            score += 100
            # Even higher for exact matches
            if keyword == metadata.name.lower():
                score += 100
        elif match_type == "display":
            score += 50
        elif match_type == "description":
            score += 10
        
        # Bonus for keyword at start of field name
        if metadata.name.lower().startswith(keyword):
            score += 50
        
        return score


class FieldValidator:
    """Validator for field names with suggestion capabilities"""
    
    def __init__(self, valid_fields: set):
        self.valid_fields = valid_fields
        
        # Common field name corrections
        self.common_corrections = {
            "eps_yoy": "eps_growth_this_y",
            "sales_qtr_over_qtr": "sales_growth_qtr", 
            "sales_growth_yoy": "sales_growth_this_y",
            "div_yield": "dividend_yield",
            "market_capitalication": "market_cap",
            "pe": "pe_ratio",
            "pb": "pb_ratio",
            "ps": "ps_ratio",
            "eps_growth_qtr_over_qtr": "eps_growth_qtr",
            "divident_yield": "dividend_yield",
            "pe_ration": "pe_ratio"
        }
    
    def validate(self, fields: List[str]) -> ValidationResult:
        """Validate a list of field names"""
        if not fields:
            return ValidationResult(
                all_valid=True,
                valid_fields=[],
                invalid_fields=[],
                suggestions={}
            )
        
        # Remove duplicates while preserving order
        unique_fields = []
        seen = set()
        for field in fields:
            if field not in seen:
                unique_fields.append(field)
                seen.add(field)
        
        valid_fields = []
        invalid_fields = []
        suggestions = {}
        
        for field in unique_fields:
            if field in self.valid_fields:
                valid_fields.append(field)
            else:
                invalid_fields.append(field)
                field_suggestions = self.suggest_corrections([field])
                suggestions.update(field_suggestions)
        
        return ValidationResult(
            all_valid=len(invalid_fields) == 0,
            valid_fields=valid_fields,
            invalid_fields=invalid_fields,
            suggestions=suggestions
        )
    
    def suggest_corrections(self, fields: List[str]) -> Dict[str, List[str]]:
        """Suggest corrections for invalid field names"""
        suggestions = {}
        
        for field in fields:
            field_suggestions = []
            
            # Check common corrections first
            if field in self.common_corrections:
                field_suggestions.append(self.common_corrections[field])
            else:
                # Use difflib for similarity matching
                close_matches = difflib.get_close_matches(
                    field, 
                    self.valid_fields, 
                    n=3, 
                    cutoff=0.6
                )
                field_suggestions.extend(close_matches)
            
            suggestions[field] = field_suggestions
        
        return suggestions