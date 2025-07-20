"""
Test suite for Field Discovery MCP Tools
Following wada-style TDD approach - write tests first, then implement
"""
import pytest
from unittest.mock import Mock, patch
from typing import List, Optional

# Import the field discovery tools (will be implemented after tests)
# Note: These imports will initially fail - that's expected in TDD
try:
    from src.field_discovery.tools import (
        list_available_fields,
        get_field_categories, 
        describe_field,
        search_fields,
        validate_fields,
        TextContent
    )
except ImportError:
    # Create minimal TextContent mock for testing
    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text
    
    # Create mock functions for initial TDD RED state
    def list_available_fields():
        raise NotImplementedError("Not implemented yet")
    
    def get_field_categories():
        raise NotImplementedError("Not implemented yet")
        
    def describe_field(field_name: str):
        raise NotImplementedError("Not implemented yet")
        
    def search_fields(keyword: str, category: Optional[str] = None):
        raise NotImplementedError("Not implemented yet")
        
    def validate_fields(field_names: List[str]):
        raise NotImplementedError("Not implemented yet")


class TestListAvailableFields:
    """Test the list_available_fields MCP tool"""
    
    def test_returns_text_content_list(self):
        """Should return a list containing TextContent objects"""
        result = list_available_fields()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"
    
    def test_includes_all_field_categories(self):
        """Should include all major field categories in output"""
        result = list_available_fields()
        content = result[0].text
        
        expected_categories = [
            "Basic Information",
            "Valuation Metrics", 
            "Performance Metrics",
            "Technical Indicators",
            "Fundamental Data",
            "Earnings & Growth",
            "ETF Specific",
            "News & Sentiment",
            "Trading Data"
        ]
        
        for category in expected_categories:
            assert category in content
    
    def test_includes_field_count(self):
        """Should show total number of available fields"""
        result = list_available_fields()
        content = result[0].text
        
        assert "128 total" in content or "128 fields" in content
    
    def test_includes_sample_fields(self):
        """Should include key field names in the output"""
        result = list_available_fields()
        content = result[0].text
        
        key_fields = [
            "ticker", "company", "sector", "industry",
            "pe_ratio", "pb_ratio", "dividend_yield",
            "performance_1w", "performance_1m",
            "eps_growth_qtr", "market_cap"
        ]
        
        for field in key_fields:
            assert field in content


class TestGetFieldCategories:
    """Test the get_field_categories MCP tool"""
    
    def test_returns_text_content_list(self):
        """Should return a list containing TextContent objects"""
        result = get_field_categories()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"
    
    def test_categories_have_icons_and_descriptions(self):
        """Each category should have an icon and description"""
        result = get_field_categories()
        content = result[0].text
        
        # Check for category icons
        category_icons = ["📊", "💰", "📈", "🔧", "📋", "📅", "🏢", "📰", "🎯"]
        for icon in category_icons:
            assert icon in content
    
    def test_shows_field_counts_per_category(self):
        """Should show number of fields in each category"""
        result = get_field_categories()
        content = result[0].text
        
        # Should have patterns like "(8 fields)" or "(12 fields)"
        import re
        field_count_pattern = r'\(\d+ fields?\)'
        matches = re.findall(field_count_pattern, content)
        assert len(matches) >= 8  # At least 8 categories should show field counts
    
    def test_lists_sample_fields_per_category(self):
        """Should list sample fields for each category"""
        result = get_field_categories()
        content = result[0].text
        
        # Basic Information category should list key fields
        assert "ticker, company, sector" in content
        # Valuation category should list ratios
        assert "pe_ratio, pb_ratio" in content


class TestDescribeField:
    """Test the describe_field MCP tool"""
    
    def test_returns_text_content_list(self):
        """Should return a list containing TextContent objects"""
        result = describe_field("pe_ratio")
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"
    
    def test_describes_valid_field(self):
        """Should provide detailed description for valid field"""
        result = describe_field("pe_ratio")
        content = result[0].text
        
        # Should include field name
        assert "pe_ratio" in content
        # Should include display name
        assert "Price-to-Earnings" in content
        # Should include category
        assert "Valuation" in content
        # Should include description
        assert "earnings" in content.lower()
    
    def test_includes_field_metadata(self):
        """Should include comprehensive field metadata"""
        result = describe_field("dividend_yield")
        content = result[0].text
        
        expected_sections = [
            "Basic Info:",
            "Description:",
            "Format:",
            "Usage Examples:",
            "Related Fields:"
        ]
        
        for section in expected_sections:
            assert section in content
    
    def test_handles_invalid_field(self):
        """Should handle invalid field names gracefully"""
        result = describe_field("invalid_field_name")
        content = result[0].text
        
        assert "not found" in content.lower() or "invalid" in content.lower()
        # Should suggest similar fields
        assert "similar" in content.lower() or "suggestions" in content.lower()
    
    def test_provides_usage_examples(self):
        """Should provide practical usage examples"""
        result = describe_field("pe_ratio")
        content = result[0].text
        
        # Should include example interpretations
        assert "Low P/E" in content or "High P/E" in content
        # Should mention numerical ranges
        assert any(char.isdigit() for char in content)


class TestSearchFields:
    """Test the search_fields MCP tool"""
    
    def test_returns_text_content_list(self):
        """Should return a list containing TextContent objects"""
        result = search_fields("growth")
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"
    
    def test_finds_growth_related_fields(self):
        """Should find all growth-related fields"""
        result = search_fields("growth")
        content = result[0].text
        
        growth_fields = [
            "eps_growth_qtr",
            "eps_growth_this_y", 
            "sales_growth_qtr",
            "dividend_growth"
        ]
        
        for field in growth_fields:
            assert field in content
    
    def test_finds_ratio_fields(self):
        """Should find ratio-related fields"""
        result = search_fields("ratio")
        content = result[0].text
        
        ratio_fields = ["pe_ratio", "pb_ratio", "payout_ratio", "current_ratio"]
        
        for field in ratio_fields:
            assert field in content
    
    def test_case_insensitive_search(self):
        """Should work with different case inputs"""
        result_lower = search_fields("growth")
        result_upper = search_fields("GROWTH")
        result_mixed = search_fields("Growth")
        
        # All should return the same results
        assert result_lower[0].text == result_upper[0].text == result_mixed[0].text
    
    def test_empty_search_returns_message(self):
        """Should handle empty search terms gracefully"""
        result = search_fields("")
        content = result[0].text
        
        assert "no search term" in content.lower() or "empty" in content.lower()
    
    def test_no_matches_returns_suggestions(self):
        """Should provide suggestions when no matches found"""
        result = search_fields("xyz123nonexistent")
        content = result[0].text
        
        assert "no matches" in content.lower() or "not found" in content.lower()
        assert "suggestions" in content.lower() or "try" in content.lower()
    
    def test_category_filtering(self):
        """Should support category filtering"""
        result = search_fields("ratio", category="valuation")
        content = result[0].text
        
        # Should find valuation ratios but not other ratios
        assert "pe_ratio" in content
        assert "pb_ratio" in content
        # Should indicate category filter was applied
        assert "valuation" in content.lower()


class TestValidateFields:
    """Test the validate_fields MCP tool"""
    
    def test_returns_text_content_list(self):
        """Should return a list containing TextContent objects"""
        result = validate_fields(["ticker", "company"])
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"
    
    def test_validates_correct_fields(self):
        """Should mark valid fields as correct"""
        valid_fields = ["ticker", "company", "pe_ratio", "dividend_yield"]
        result = validate_fields(valid_fields)
        content = result[0].text
        
        assert "✅" in content or "VALID" in content
        for field in valid_fields:
            assert field in content
    
    def test_identifies_invalid_fields(self):
        """Should identify and flag invalid fields"""
        invalid_fields = ["eps_yoy", "sales_growth_yoy", "nonexistent_field"]
        result = validate_fields(invalid_fields)
        content = result[0].text
        
        assert "❌" in content or "INVALID" in content
        for field in invalid_fields:
            assert field in content
    
    def test_suggests_corrections(self):
        """Should suggest corrections for common typos"""
        typo_fields = ["eps_yoy", "sales_qtr_over_qtr"]
        result = validate_fields(typo_fields)
        content = result[0].text
        
        # Should suggest correct alternatives
        assert "eps_growth_this_y" in content
        assert "sales_growth_qtr" in content
        # Should use suggestion indicators
        assert "→" in content or "Did you mean" in content
    
    def test_mixed_valid_invalid_fields(self):
        """Should handle mix of valid and invalid fields"""
        mixed_fields = ["ticker", "eps_yoy", "company", "invalid_field"]
        result = validate_fields(mixed_fields)
        content = result[0].text
        
        # Should show both valid and invalid sections
        assert "✅" in content and "❌" in content
        assert "VALID" in content and "INVALID" in content
        
        # Valid fields should be listed
        assert "ticker" in content
        assert "company" in content
        
        # Invalid fields should be listed with suggestions
        assert "eps_yoy" in content
        assert "invalid_field" in content
    
    def test_empty_field_list(self):
        """Should handle empty field list gracefully"""
        result = validate_fields([])
        content = result[0].text
        
        assert "no fields" in content.lower() or "empty" in content.lower()
    
    def test_provides_usage_guidance(self):
        """Should provide helpful usage guidance"""
        result = validate_fields(["eps_yoy", "sales_growth_yoy"])
        content = result[0].text
        
        # Should include helpful suggestions section
        assert "💡" in content or "SUGGESTIONS" in content
        # Should explain proper naming patterns
        assert "yearly growth" in content.lower() or "growth metrics" in content.lower()


class TestFieldDiscoveryIntegration:
    """Integration tests for field discovery tools"""
    
    def test_tools_are_consistent(self):
        """Field lists should be consistent across tools"""
        # Get all fields from list tool
        all_fields_result = list_available_fields()
        all_fields_content = all_fields_result[0].text
        
        # Search for a common field
        search_result = search_fields("ticker")
        search_content = search_result[0].text
        
        # ticker should appear in both
        assert "ticker" in all_fields_content
        assert "ticker" in search_content
    
    def test_describe_field_matches_categories(self):
        """Field descriptions should match category assignments"""
        # Get categories
        categories_result = get_field_categories()
        categories_content = categories_result[0].text
        
        # Check that pe_ratio is in valuation category
        describe_result = describe_field("pe_ratio")
        describe_content = describe_result[0].text
        
        # Both should mention valuation
        assert "valuation" in categories_content.lower()
        assert "valuation" in describe_content.lower()
    
    def test_search_finds_described_fields(self):
        """Search should find fields that can be described"""
        # Search for growth fields
        search_result = search_fields("growth")
        search_content = search_result[0].text
        
        # Extract a field name (eps_growth_qtr should be found)
        assert "eps_growth_qtr" in search_content
        
        # That field should be describable
        describe_result = describe_field("eps_growth_qtr")
        describe_content = describe_result[0].text
        
        assert "eps_growth_qtr" in describe_content
        assert "not found" not in describe_content.lower()
    
    def test_validation_accepts_listed_fields(self):
        """Validation should accept fields from the main list"""
        # Get some fields from the main list
        fields_to_test = ["ticker", "company", "pe_ratio", "dividend_yield"]
        
        # These should all validate successfully
        validation_result = validate_fields(fields_to_test)
        validation_content = validation_result[0].text
        
        # Should show as valid
        assert "✅" in validation_content or "VALID" in validation_content
        # Should not show any invalid fields
        assert "❌" not in validation_content or "INVALID FIELDS (0)" in validation_content


# Integration with existing MCP server structure
class TestMCPServerIntegration:
    """Test integration with existing MCP server"""
    
    @patch('src.server.server')
    def test_tools_register_with_mcp_server(self, mock_server):
        """Field discovery tools should register with MCP server"""
        from src.field_discovery.tools import register_field_discovery_tools
        
        register_field_discovery_tools(mock_server)
        
        # Should register all 5 tools
        assert mock_server.tool.call_count == 5
        
        # Check tool names
        registered_tools = [call[0][0] for call in mock_server.tool.call_args_list]
        expected_tools = [
            "list_available_fields",
            "get_field_categories", 
            "describe_field",
            "search_fields",
            "validate_fields"
        ]
        
        for tool in expected_tools:
            assert tool in registered_tools
    
    def test_tools_follow_mcp_patterns(self):
        """Tools should follow existing MCP patterns"""
        # All tools should return List[TextContent]
        tools = [
            list_available_fields,
            get_field_categories,
            lambda: describe_field("ticker"),
            lambda: search_fields("growth"),
            lambda: validate_fields(["ticker"])
        ]
        
        for tool in tools:
            result = tool()
            assert isinstance(result, list)
            assert len(result) >= 1
            assert isinstance(result[0], TextContent)
            assert result[0].type == "text"