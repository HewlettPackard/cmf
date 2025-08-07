"""
Advanced search utilities for label content with comparison operators.
Supports queries like: lines>240, score<=0.5, name="test", status!=active
"""

import re
from typing import Dict, List, Tuple, Any, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ComparisonOperator(Enum):
    """Supported comparison operators"""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "="
    NOT_EQUAL = "!="
    CONTAINS = "~"  # For text contains (case-insensitive)
    NOT_CONTAINS = "!~"  # For text does not contain

class SearchCondition:
    """Represents a single search condition"""
    def __init__(self, column: str, operator: ComparisonOperator, value: Union[str, int, float]):
        self.column = column.strip()
        self.operator = operator
        self.value = value
        
    def __repr__(self):
        return f"SearchCondition({self.column} {self.operator.value} {self.value})"

class AdvancedSearchParser:
    """Parser for advanced search queries with comparison operators"""
    
    # Regex pattern to match search conditions
    # Supports: column>value, column<=value, column="quoted value", etc.
    CONDITION_PATTERN = re.compile(
        r'(\w+)\s*(>=|<=|!=|!~|>|<|=|~)\s*("([^"]*)"|\'([^\']*)\'|([^\s,]+))',
        re.IGNORECASE
    )
    
    @classmethod
    def parse_search_query(cls, query: str) -> Tuple[List[SearchCondition], List[str], List[str]]:
        """
        Parse a search query into structured conditions and plain text terms.
        
        Args:
            query: Search query string (e.g., "lines>240 score<=0.5 test")
            
        Returns:
            Tuple of (conditions, plain_text_terms, errors)
        """
        conditions = []
        errors = []
        
        # Find all structured conditions
        matches = cls.CONDITION_PATTERN.findall(query)
        matched_positions = []
        
        for match in cls.CONDITION_PATTERN.finditer(query):
            matched_positions.append((match.start(), match.end()))
            
        for match in matches:
            column, operator_str, _, quoted_value1, quoted_value2, unquoted_value = match
            
            # Get the actual value (quoted or unquoted)
            value = quoted_value1 or quoted_value2 or unquoted_value
            
            try:
                # Parse operator
                operator = ComparisonOperator(operator_str)
                
                # Convert value to appropriate type
                parsed_value = cls._parse_value(value, operator)
                
                conditions.append(SearchCondition(column, operator, parsed_value))
                
            except ValueError as e:
                errors.append(f"Invalid condition '{column}{operator_str}{value}': {str(e)}")
                
        # Extract remaining text as plain search terms
        remaining_text = query
        for start, end in reversed(matched_positions):
            remaining_text = remaining_text[:start] + remaining_text[end:]
            
        plain_terms = [term.strip() for term in remaining_text.split() if term.strip()]
        
        return conditions, plain_terms, errors
    
    @classmethod
    def _parse_value(cls, value: str, operator: ComparisonOperator) -> Union[str, int, float]:
        """Parse value string to appropriate type based on operator"""
        if operator in [ComparisonOperator.CONTAINS, ComparisonOperator.NOT_CONTAINS]:
            return value  # Keep as string for text operations
            
        if operator in [ComparisonOperator.EQUAL, ComparisonOperator.NOT_EQUAL]:
            # Try to parse as number, fall back to string
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                return value
                
        # For numeric comparisons, try to parse as number
        if operator in [ComparisonOperator.GREATER_THAN, ComparisonOperator.LESS_THAN,
                       ComparisonOperator.GREATER_EQUAL, ComparisonOperator.LESS_EQUAL]:
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                raise ValueError(f"Numeric value expected for operator {operator.value}, got '{value}'")
                
        return value

class LabelSearchFilter:
    """Filter label data based on advanced search conditions"""
    
    @classmethod
    def apply_conditions(cls, label_data: List[Dict[str, Any]], conditions: List[SearchCondition]) -> List[Dict[str, Any]]:
        """
        Apply search conditions to filter label data.
        
        Args:
            label_data: List of label row dictionaries
            conditions: List of search conditions to apply
            
        Returns:
            Filtered list of label rows
        """
        if not conditions:
            return label_data
            
        filtered_data = []
        
        for row in label_data:
            if cls._row_matches_conditions(row, conditions):
                filtered_data.append(row)
                
        return filtered_data
    
    @classmethod
    def _row_matches_conditions(cls, row: Dict[str, Any], conditions: List[SearchCondition]) -> bool:
        """Check if a row matches all search conditions"""
        for condition in conditions:
            if not cls._evaluate_condition(row, condition):
                return False
        return True
    
    @classmethod
    def _evaluate_condition(cls, row: Dict[str, Any], condition: SearchCondition) -> bool:
        """Evaluate a single condition against a row"""
        # Try case-insensitive column lookup
        column_value = None
        condition_column_lower = condition.column.lower()

        # First try exact match
        if condition.column in row:
            column_value = row[condition.column]
        else:
            # Try case-insensitive match
            for col_name, col_value in row.items():
                if col_name.lower().strip() == condition_column_lower:
                    column_value = col_value
                    break

        if column_value is None:
            return False
            
        # Convert column value to string for processing
        column_str = str(column_value).strip()
        
        try:
            if condition.operator == ComparisonOperator.CONTAINS:
                return condition.value.lower() in column_str.lower()
                
            elif condition.operator == ComparisonOperator.NOT_CONTAINS:
                return condition.value.lower() not in column_str.lower()
                
            elif condition.operator == ComparisonOperator.EQUAL:
                return cls._compare_values(column_str, condition.value, "==")
                
            elif condition.operator == ComparisonOperator.NOT_EQUAL:
                return cls._compare_values(column_str, condition.value, "!=")
                
            elif condition.operator == ComparisonOperator.GREATER_THAN:
                return cls._compare_values(column_str, condition.value, ">")
                
            elif condition.operator == ComparisonOperator.LESS_THAN:
                return cls._compare_values(column_str, condition.value, "<")
                
            elif condition.operator == ComparisonOperator.GREATER_EQUAL:
                return cls._compare_values(column_str, condition.value, ">=")
                
            elif condition.operator == ComparisonOperator.LESS_EQUAL:
                return cls._compare_values(column_str, condition.value, "<=")
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error evaluating condition {condition}: {e}")
            return False
            
        return False
    
    @classmethod
    def _compare_values(cls, column_value: str, condition_value: Union[str, int, float], operator: str) -> bool:
        """Compare values with type coercion"""
        # If condition value is numeric, try to parse column value as numeric
        if isinstance(condition_value, (int, float)):
            try:
                if isinstance(condition_value, float):
                    column_numeric = float(column_value)
                else:
                    column_numeric = int(column_value)
                    
                if operator == "==":
                    return column_numeric == condition_value
                elif operator == "!=":
                    return column_numeric != condition_value
                elif operator == ">":
                    return column_numeric > condition_value
                elif operator == "<":
                    return column_numeric < condition_value
                elif operator == ">=":
                    return column_numeric >= condition_value
                elif operator == "<=":
                    return column_numeric <= condition_value
                    
            except ValueError:
                # Fall back to string comparison if numeric parsing fails
                pass
                
        # String comparison
        if operator == "==":
            return column_value.lower() == str(condition_value).lower()
        elif operator == "!=":
            return column_value.lower() != str(condition_value).lower()
        else:
            # For other operators on strings, try lexicographic comparison
            if operator == ">":
                return column_value.lower() > str(condition_value).lower()
            elif operator == "<":
                return column_value.lower() < str(condition_value).lower()
            elif operator == ">=":
                return column_value.lower() >= str(condition_value).lower()
            elif operator == "<=":
                return column_value.lower() <= str(condition_value).lower()

        return False
