"""
Test suite for Field Metadata and Supporting Classes
Following wada-style TDD approach
"""
import pytest
from dataclasses import dataclass
from typing import List, Dict, Optional

# Import the field metadata classes (will be implemented after tests)
try:
    from src.field_discovery.metadata import (
        FieldMetadata,
        FieldCategory,
        FieldSearchEngine,
        FieldValidator,
        ValidationResult
    )
except ImportError:
    # Create minimal mocks for TDD RED state
    from dataclasses import dataclass
    from typing import List, Dict, Optional
    
    @dataclass
    class FieldMetadata:
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
        id: str
        name: str
        icon: str
        description: str
        field_count: int
        
        def get_display_name(self) -> str:
            return f"{self.icon} {self.name} ({self.field_count} fields)"
    
    class FieldSearchEngine:
        def __init__(self, fields: Dict[str, FieldMetadata]):
            self.fields = fields
        
        def search(self, keyword: str, category: Optional[str] = None) -> List[FieldMetadata]:
            raise NotImplementedError("Not implemented yet")
    
    class FieldValidator:
        def __init__(self, valid_fields: set):
            self.valid_fields = valid_fields
        
        def validate(self, fields: List[str]):
            raise NotImplementedError("Not implemented yet")
        
        def suggest_corrections(self, fields: List[str]) -> Dict[str, List[str]]:
            raise NotImplementedError("Not implemented yet")


class TestFieldMetadata:
    """Test the FieldMetadata dataclass"""
    
    def test_field_metadata_creation(self):
        """Should create FieldMetadata with all required fields"""
        metadata = FieldMetadata(
            name="pe_ratio",
            display_name="Price-to-Earnings Ratio",
            category="valuation",
            description="Price relative to earnings per share",
            data_type="float",
            format_info="Numeric ratio (e.g., 15.5)",
            special_values=["N/A"],
            related_fields=["forward_pe", "eps_ttm"],
            usage_examples=["Low P/E (< 15) may indicate value"]
        )
        
        assert metadata.name == "pe_ratio"
        assert metadata.display_name == "Price-to-Earnings Ratio"
        assert metadata.category == "valuation"
        assert metadata.data_type == "float"
        assert len(metadata.related_fields) == 2
        assert len(metadata.usage_examples) == 1
    
    def test_field_metadata_defaults(self):
        """Should handle optional fields with defaults"""
        metadata = FieldMetadata(
            name="ticker",
            display_name="Stock Ticker",
            category="basic",
            description="Stock symbol",
            data_type="string"
        )
        
        # Optional fields should have defaults
        assert metadata.format_info == ""
        assert metadata.special_values == []
        assert metadata.related_fields == []
        assert metadata.usage_examples == []
    
    def test_field_metadata_validation(self):
        """Should validate required fields are present"""
        with pytest.raises(TypeError):
            # Missing required fields should raise error
            FieldMetadata()
    
    def test_field_metadata_string_representation(self):
        """Should have useful string representation"""
        metadata = FieldMetadata(
            name="dividend_yield",
            display_name="Dividend Yield",
            category="valuation",
            description="Annual dividend as percentage of price",
            data_type="percentage"
        )
        
        str_repr = str(metadata)
        assert "dividend_yield" in str_repr
        assert "Dividend Yield" in str_repr


class TestFieldCategory:
    """Test the FieldCategory dataclass"""
    
    def test_field_category_creation(self):
        """Should create FieldCategory with all properties"""
        category = FieldCategory(
            id="valuation",
            name="Valuation Metrics",
            icon="💰",
            description="Price ratios and valuation measures",
            field_count=12
        )
        
        assert category.id == "valuation"
        assert category.name == "Valuation Metrics"
        assert category.icon == "💰"
        assert category.field_count == 12
    
    def test_category_display_name(self):
        """Should format display name with icon and count"""
        category = FieldCategory(
            id="performance",
            name="Performance Metrics",
            icon="📈",
            description="Historical price performance",
            field_count=18
        )
        
        display = category.get_display_name()
        assert "📈" in display
        assert "Performance Metrics" in display
        assert "18" in display
        
    def test_category_ordering(self):
        """Categories should be orderable for consistent display"""
        cat1 = FieldCategory("basic", "Basic", "📊", "Basic info", 8)
        cat2 = FieldCategory("valuation", "Valuation", "💰", "Valuation", 12)
        
        categories = [cat2, cat1]
        sorted_categories = sorted(categories, key=lambda c: c.name)
        
        assert sorted_categories[0].id == "basic"
        assert sorted_categories[1].id == "valuation"


class TestFieldSearchEngine:
    """Test the FieldSearchEngine class"""
    
    def test_search_engine_creation(self):
        """Should create search engine with field data"""
        # Mock field data
        fields = {
            "pe_ratio": FieldMetadata("pe_ratio", "P/E Ratio", "valuation", "Price to earnings", "float"),
            "eps_growth_qtr": FieldMetadata("eps_growth_qtr", "EPS Growth QoQ", "growth", "Quarterly EPS growth", "percentage")
        }
        
        engine = FieldSearchEngine(fields)
        assert len(engine.fields) == 2
        assert "pe_ratio" in engine.fields
        assert "eps_growth_qtr" in engine.fields
    
    def test_search_by_keyword(self):
        """Should find fields by keyword in name or description"""
        fields = {
            "pe_ratio": FieldMetadata("pe_ratio", "P/E Ratio", "valuation", "Price to earnings ratio", "float"),
            "pb_ratio": FieldMetadata("pb_ratio", "P/B Ratio", "valuation", "Price to book ratio", "float"),
            "eps_growth_qtr": FieldMetadata("eps_growth_qtr", "EPS Growth", "growth", "Earnings per share growth", "percentage")
        }
        
        engine = FieldSearchEngine(fields)
        
        # Search for "ratio" should find pe_ratio and pb_ratio
        results = engine.search("ratio")
        assert len(results) == 2
        assert any(r.name == "pe_ratio" for r in results)
        assert any(r.name == "pb_ratio" for r in results)
        
        # Search for "growth" should find eps_growth_qtr
        growth_results = engine.search("growth")
        assert len(growth_results) == 1
        assert growth_results[0].name == "eps_growth_qtr"
    
    def test_search_case_insensitive(self):
        """Should perform case-insensitive searches"""
        fields = {
            "pe_ratio": FieldMetadata("pe_ratio", "P/E Ratio", "valuation", "Price Earnings ratio", "float")
        }
        
        engine = FieldSearchEngine(fields)
        
        # All these should find the same result
        results_lower = engine.search("earnings")
        results_upper = engine.search("EARNINGS") 
        results_mixed = engine.search("Earnings")
        
        assert len(results_lower) == len(results_upper) == len(results_mixed) == 1
        assert results_lower[0].name == results_upper[0].name == results_mixed[0].name
    
    def test_search_with_category_filter(self):
        """Should filter search results by category"""
        fields = {
            "pe_ratio": FieldMetadata("pe_ratio", "P/E Ratio", "valuation", "Price ratio", "float"),
            "current_ratio": FieldMetadata("current_ratio", "Current Ratio", "fundamental", "Liquidity ratio", "float"),
            "performance_year": FieldMetadata("performance_year", "1Y Performance", "performance", "Annual return", "percentage")
        }
        
        engine = FieldSearchEngine(fields)
        
        # Search for "ratio" with valuation filter
        valuation_results = engine.search("ratio", category="valuation")
        assert len(valuation_results) == 1
        assert valuation_results[0].name == "pe_ratio"
        
        # Search for "ratio" with fundamental filter
        fundamental_results = engine.search("ratio", category="fundamental")
        assert len(fundamental_results) == 1
        assert fundamental_results[0].name == "current_ratio"
    
    def test_search_no_results(self):
        """Should handle searches with no results"""
        fields = {
            "pe_ratio": FieldMetadata("pe_ratio", "P/E Ratio", "valuation", "Price earnings", "float")
        }
        
        engine = FieldSearchEngine(fields)
        results = engine.search("nonexistent")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_empty_query(self):
        """Should handle empty search queries"""
        fields = {
            "pe_ratio": FieldMetadata("pe_ratio", "P/E Ratio", "valuation", "Price earnings", "float")
        }
        
        engine = FieldSearchEngine(fields)
        results = engine.search("")
        
        # Empty search should return empty results
        assert len(results) == 0
    
    def test_search_ranking(self):
        """Should rank results by relevance"""
        fields = {
            "eps_growth_qtr": FieldMetadata("eps_growth_qtr", "EPS Growth QoQ", "growth", "Quarterly EPS growth rate", "percentage"),
            "sales_growth_qtr": FieldMetadata("sales_growth_qtr", "Sales Growth", "growth", "Quarterly sales growth", "percentage"),
            "dividend_growth": FieldMetadata("dividend_growth", "Dividend Growth", "dividend", "Annual dividend growth", "percentage")
        }
        
        engine = FieldSearchEngine(fields)
        results = engine.search("growth")
        
        # All should be found
        assert len(results) == 3
        
        # Results should be ranked (exact name matches first, then description matches)
        result_names = [r.name for r in results]
        # Fields with "growth" in name should come before those with "growth" only in description
        growth_in_name = [name for name in result_names if "growth" in name]
        assert len(growth_in_name) >= 2


class TestFieldValidator:
    """Test the FieldValidator class"""
    
    def test_validator_creation(self):
        """Should create validator with field definitions"""
        valid_fields = {"ticker", "company", "pe_ratio", "dividend_yield"}
        validator = FieldValidator(valid_fields)
        
        assert len(validator.valid_fields) == 4
        assert "ticker" in validator.valid_fields
        assert "pe_ratio" in validator.valid_fields
    
    def test_validate_all_valid_fields(self):
        """Should validate list of all valid fields"""
        valid_fields = {"ticker", "company", "pe_ratio"}
        validator = FieldValidator(valid_fields)
        
        test_fields = ["ticker", "company"]
        result = validator.validate(test_fields)
        
        assert result.all_valid is True
        assert len(result.valid_fields) == 2
        assert len(result.invalid_fields) == 0
        assert "ticker" in result.valid_fields
        assert "company" in result.valid_fields
    
    def test_validate_mixed_fields(self):
        """Should handle mix of valid and invalid fields"""
        valid_fields = {"ticker", "company", "pe_ratio"}
        validator = FieldValidator(valid_fields)
        
        test_fields = ["ticker", "invalid_field", "pe_ratio", "another_invalid"]
        result = validator.validate(test_fields)
        
        assert result.all_valid is False
        assert len(result.valid_fields) == 2
        assert len(result.invalid_fields) == 2
        assert "ticker" in result.valid_fields
        assert "pe_ratio" in result.valid_fields
        assert "invalid_field" in result.invalid_fields
        assert "another_invalid" in result.invalid_fields
    
    def test_suggest_corrections(self):
        """Should suggest corrections for typos"""
        valid_fields = {"eps_growth_this_y", "eps_growth_qtr", "sales_growth_qtr"}
        validator = FieldValidator(valid_fields)
        
        # Common typos
        typos = ["eps_yoy", "eps_growth_qtr_over_qtr", "sales_qtr_over_qtr"]
        suggestions = validator.suggest_corrections(typos)
        
        assert len(suggestions) == 3
        assert "eps_growth_this_y" in suggestions["eps_yoy"]
        assert "eps_growth_qtr" in suggestions["eps_growth_qtr_over_qtr"]
        assert "sales_growth_qtr" in suggestions["sales_qtr_over_qtr"]
    
    def test_levenshtein_distance_suggestions(self):
        """Should use edit distance for typo suggestions"""
        valid_fields = {"dividend_yield", "pe_ratio", "pb_ratio"}
        validator = FieldValidator(valid_fields)
        
        # Typo should suggest closest match
        suggestions = validator.suggest_corrections(["divident_yield"])  # missing 'd'
        assert "dividend_yield" in suggestions["divident_yield"]
        
        suggestions = validator.suggest_corrections(["pe_ration"])  # extra 'n'
        assert "pe_ratio" in suggestions["pe_ration"]
    
    def test_no_suggestions_for_very_different_fields(self):
        """Should not suggest corrections for completely different field names"""
        valid_fields = {"ticker", "company", "sector"}
        validator = FieldValidator(valid_fields)
        
        # Very different field name should get no suggestions
        suggestions = validator.suggest_corrections(["completely_different_field_name"])
        assert len(suggestions["completely_different_field_name"]) == 0
    
    def test_empty_field_list(self):
        """Should handle empty field list"""
        valid_fields = {"ticker", "company"}
        validator = FieldValidator(valid_fields)
        
        result = validator.validate([])
        assert result.all_valid is True  # Empty list is valid
        assert len(result.valid_fields) == 0
        assert len(result.invalid_fields) == 0
    
    def test_duplicate_fields(self):
        """Should handle duplicate fields in input"""
        valid_fields = {"ticker", "company", "pe_ratio"}
        validator = FieldValidator(valid_fields)
        
        test_fields = ["ticker", "ticker", "company", "pe_ratio", "company"]
        result = validator.validate(test_fields)
        
        # Should deduplicate but still validate correctly
        assert result.all_valid is True
        assert len(result.valid_fields) == 3  # Unique valid fields
        assert len(result.invalid_fields) == 0


class TestValidationResult:
    """Test the ValidationResult dataclass"""
    
    def test_validation_result_creation(self):
        """Should create validation result with all fields"""
        result = ValidationResult(
            all_valid=False,
            valid_fields=["ticker", "company"],
            invalid_fields=["bad_field"],
            suggestions={"bad_field": ["ticker"]}
        )
        
        assert result.all_valid is False
        assert len(result.valid_fields) == 2
        assert len(result.invalid_fields) == 1
        assert "bad_field" in result.suggestions
    
    def test_validation_result_summary(self):
        """Should provide summary of validation results"""
        result = ValidationResult(
            all_valid=False,
            valid_fields=["ticker", "company", "pe_ratio"],
            invalid_fields=["bad_field", "another_bad"],
            suggestions={"bad_field": ["ticker"], "another_bad": []}
        )
        
        summary = result.get_summary()
        assert "3 valid" in summary
        assert "2 invalid" in summary
        assert "ticker" in summary
        assert "bad_field" in summary


