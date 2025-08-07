/***
 * Copyright (2025) Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ***/

import React from 'react';

const AdvancedHighlight = ({ text, highlight, columnName, searchMetadata }) => {
    // If no search metadata or not a search result, fall back to basic highlighting
    if (!searchMetadata || !searchMetadata.is_search_result) {
        return <BasicHighlight text={text} highlight={highlight} />;
    }

    // Ensure text is a string
    const textStr = String(text || '');

    // Check if this column matches any advanced search conditions
    const matchingConditions = searchMetadata.advanced_conditions?.filter(
        condition => condition.column === columnName
    ) || [];

    // Check if this column value matches any plain text terms
    const plainTermsMatch = searchMetadata.plain_terms?.some(term =>
        textStr.toLowerCase().includes(term.toLowerCase())
    ) || false;

    // If this column has matching conditions, highlight it differently
    if (matchingConditions.length > 0) {
        const conditionMatches = matchingConditions.some(condition => {
            return evaluateConditionForHighlight(textStr, condition);
        });

        if (conditionMatches) {
            return (
                <span className="bg-yellow-300 text-black font-semibold" title={`Matches: ${matchingConditions.map(c => `${c.column}${c.operator}${c.value}`).join(', ')}`}>
                    {textStr}
                </span>
            );
        }
    }

    // If it matches plain text terms, use regular highlighting
    if (plainTermsMatch) {
        return <BasicHighlight text={textStr} highlight={searchMetadata.plain_terms.join(' ')} />;
    }

    // No match, return plain text
    return <span>{textStr}</span>;
};

const BasicHighlight = ({ text, highlight }) => {
    // If the highlight text is empty or contains only whitespace, return the original text
    if (!highlight || !highlight.trim()) {
        return <span>{text}</span>;
    }

    // Create a regular expression to match the highlight text, case insensitive
    const regex = new RegExp(`(${highlight})`, 'gi');
    // Split the text into parts based on the highlight text
    const parts = text.split(regex);

    return (
        <span>
            {parts.map((part, index) =>
                // If the part matches the highlight text, wrap it in a mark element
                regex.test(part) ? (
                    <mark key={index} className="bg-yellow-300 text-black font-semibold">
                        {part}
                    </mark>
                ) : (
                    part
                )
            )}
        </span>
    );
};

// Helper function to evaluate if a condition matches for highlighting purposes
const evaluateConditionForHighlight = (text, condition) => {
    const value = String(text).trim();
    
    try {
        switch (condition.operator) {
            case '~': // Contains
                return value.toLowerCase().includes(String(condition.value).toLowerCase());
                
            case '!~': // Not contains
                return !value.toLowerCase().includes(String(condition.value).toLowerCase());
                
            case '=': // Equal
                return compareValuesForHighlight(value, condition.value, '==');
                
            case '!=': // Not equal
                return compareValuesForHighlight(value, condition.value, '!=');
                
            case '>': // Greater than
                return compareValuesForHighlight(value, condition.value, '>');
                
            case '<': // Less than
                return compareValuesForHighlight(value, condition.value, '<');
                
            case '>=': // Greater than or equal
                return compareValuesForHighlight(value, condition.value, '>=');
                
            case '<=': // Less than or equal
                return compareValuesForHighlight(value, condition.value, '<=');
                
            default:
                return false;
        }
    } catch (error) {
        return false;
    }
};

// Helper function to compare values for highlighting
const compareValuesForHighlight = (columnValue, conditionValue, operator) => {
    // If condition value is numeric, try to parse column value as numeric
    if (typeof conditionValue === 'number') {
        try {
            const columnNumeric = parseFloat(columnValue);
            if (!isNaN(columnNumeric)) {
                switch (operator) {
                    case '==': return columnNumeric === conditionValue;
                    case '!=': return columnNumeric !== conditionValue;
                    case '>': return columnNumeric > conditionValue;
                    case '<': return columnNumeric < conditionValue;
                    case '>=': return columnNumeric >= conditionValue;
                    case '<=': return columnNumeric <= conditionValue;
                }
            }
        } catch (error) {
            // Fall back to string comparison
        }
    }
    
    // String comparison
    const columnStr = columnValue.toLowerCase();
    const conditionStr = String(conditionValue).toLowerCase();
    
    switch (operator) {
        case '==': return columnStr === conditionStr;
        case '!=': return columnStr !== conditionStr;
        case '>': return columnStr > conditionStr;
        case '<': return columnStr < conditionStr;
        case '>=': return columnStr >= conditionStr;
        case '<=': return columnStr <= conditionStr;
        default: return false;
    }
};

export default AdvancedHighlight;
