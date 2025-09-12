import React, { useState, useCallback, useEffect } from 'react';
import { PanelProps } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';
import { css } from '@emotion/css';
import { JsonTreeOptions } from './types';
import { VERSION } from './version';

interface Props extends PanelProps<JsonTreeOptions> {}

interface TreeNodeProps {
  data: any;
  keyName: string;
  level: number;
  isLast: boolean;
  indentSize: number;
  expandLevel: number;
}

const TreeNode: React.FC<TreeNodeProps> = ({ data, keyName, level, isLast, indentSize, expandLevel }) => {
  // Determine initial expansion state based on expandLevel option
  const getExpansionState = () => {
    if (expandLevel === -1) return true;  // -1 means expand all
    if (expandLevel === 0) return false;  // 0 means expand none
    return level < expandLevel;           // Expand up to specified level
  };
  
  const [isExpanded, setIsExpanded] = useState(getExpansionState);
  const styles = useStyles2((theme) => getStyles(theme, indentSize));

  // Update expansion state when expandLevel changes
  useEffect(() => {
    setIsExpanded(getExpansionState());
  }, [expandLevel, level]);

  const toggleExpanded = useCallback(() => {
    setIsExpanded(!isExpanded);
  }, [isExpanded]);

  const getDataType = (value: any): string => {
    if (value === null) { return 'null'; }
    if (Array.isArray(value)) { return 'array'; }
    return typeof value;
  };

  const getValuePreview = (value: any): string => {
    if (value === null) { return 'null'; }
    if (value === undefined) { return 'undefined'; }
    if (typeof value === 'string') { return `"${value.length > 50 ? value.substring(0, 50) + '...' : value}"`; }
    if (typeof value === 'number' || typeof value === 'boolean') { return String(value); }
    if (Array.isArray(value)) { return `Array(${value.length})`; }
    if (typeof value === 'object') { return `Object(${Object.keys(value).length})`; }
    return String(value);
  };

  const isExpandable = (value: any): boolean => {
    return (typeof value === 'object' && value !== null) || Array.isArray(value);
  };

  const renderValue = () => {
    if (!isExpandable(data)) {
      return (
        <span className={styles.value} data-type={getDataType(data)}>
          {getValuePreview(data)}
        </span>
      );
    }

    const childKeys = Array.isArray(data) 
      ? data.map((_, index) => index.toString())
      : Object.keys(data);

    return (
      <div className={styles.objectContainer}>
        <span className={styles.objectHeader} onClick={toggleExpanded}>
          <span className={styles.expandIcon}>
            {isExpanded ? '▼' : '▶'}
          </span>
          <span className={styles.key}>{keyName}</span>
          <span className={styles.objectInfo}>
            {Array.isArray(data) ? `Array(${data.length})` : `Object(${childKeys.length})`}
          </span>
        </span>
        
        {isExpanded && (
          <div className={styles.children}>
            {childKeys.map((key, index) => (
              <TreeNode
                key={key}
                data={data[key]}
                keyName={key}
                level={level + 1}
                isLast={index === childKeys.length - 1}
                indentSize={indentSize}
                expandLevel={expandLevel}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={styles.treeNode} data-level={level}>
      {!isExpandable(data) ? (
        <div className={styles.leafNode}>
          <span className={styles.key}>{keyName}:</span>
          {renderValue()}
        </div>
      ) : (
        renderValue()
      )}
    </div>
  );
};

export const JsonTreePanel: React.FC<Props> = ({ options, data, width, height, replaceVariables }) => {
  const styles = useStyles2(getStyles);
  const [showDebug, setShowDebug] = useState(false);

  // Log version information on component mount
  React.useEffect(() => {
    console.log(`[JsonTreePanel] Plugin loaded - Version: ${VERSION.version}, Build: ${VERSION.buildNumber}, Date: ${VERSION.buildDate}`);
    console.log(`[JsonTreePanel] Features:`, VERSION.features);
  }, []);

  // Helper function to resolve nested field paths
  function resolveNestedField(data: any, fieldPath: string): any {
    if (!fieldPath || !data) return null;
    
    console.log(`[JsonTreePanel] Resolving nested field path: '${fieldPath}'`);
    
    // Split by dots first, but handle quoted strings and brackets
    const parts: string[] = [];
    let current = '';
    let inQuotes = false;
    let inBrackets = false;
    let quoteChar = '';
    
    for (let i = 0; i < fieldPath.length; i++) {
      const char = fieldPath[i];
      
      if ((char === '"' || char === "'") && !inBrackets) {
        if (!inQuotes) {
          inQuotes = true;
          quoteChar = char;
        } else if (char === quoteChar) {
          inQuotes = false;
          quoteChar = '';
        }
        // Don't include quotes in the field name
        continue;
      }
      
      if (char === '[' && !inQuotes) {
        inBrackets = true;
        if (current.trim()) {
          parts.push(current.trim());
          current = '';
        }
        continue;
      }
      
      if (char === ']' && !inQuotes) {
        inBrackets = false;
        if (current.trim()) {
          parts.push(current.trim());
          current = '';
        }
        continue;
      }
      
      if (char === '.' && !inQuotes && !inBrackets) {
        if (current.trim()) {
          parts.push(current.trim());
          current = '';
        }
        continue;
      }
      
      current += char;
    }
    
    if (current.trim()) {
      parts.push(current.trim());
    }
    
    console.log(`[JsonTreePanel] Parsed field path parts:`, parts);
    
    // Navigate through the object
    let result = data;
    for (const part of parts) {
      if (result === null || result === undefined) {
        console.log(`[JsonTreePanel] Path resolution failed at part '${part}' - result is null/undefined`);
        return null;
      }
      
      if (typeof result === 'object' && part in result) {
        result = result[part];
        console.log(`[JsonTreePanel] Navigated to '${part}':`, typeof result);
      } else {
        console.log(`[JsonTreePanel] Part '${part}' not found in object. Available keys:`, 
          typeof result === 'object' ? Object.keys(result) : 'not an object');
        return null;
      }
    }
    
    console.log(`[JsonTreePanel] Successfully resolved nested field:`, typeof result);
    return result;
  }

  if (!data.series?.length) {
    return (
      <div className={styles.noData}>
        <p>No data available</p>
        <p>Configure your data source to return JSON data</p>
      </div>
    );
  }

  // Try to parse JSON from the data series
  let jsonData: any = {};
  let errorMessage: string | null = null;
  
  // Log all incoming data for debugging
  console.log(`[JsonTreePanel] Received data:`, {
    seriesCount: data.series?.length || 0,
    options: options,
    allSeries: data.series?.map((series, idx) => ({
      index: idx,
      fieldsCount: series.fields?.length || 0,
      fields: series.fields?.map(field => ({
        name: field.name,
        type: field.type,
        valuesLength: field.values?.length || 0,
        firstValue: field.values?.length > 0 ? field.values.get(0) : null,
        firstValueType: field.values?.length > 0 ? typeof field.values.get(0) : null
      }))
    }))
  });
  
  try {
    const firstSeries = data.series[0];
    if (firstSeries.fields?.length > 0) {
      console.log(`[JsonTreePanel] Processing first series with ${firstSeries.fields.length} fields`);
      
      // Look for a specific field if rootField is specified
      let foundData = false;
      
      if (options.rootField && options.rootField.trim() !== '') {
        // Interpolate Grafana variables in the rootField
        const interpolatedRootField = replaceVariables(options.rootField);
        console.log(`[JsonTreePanel] Looking for specific field:`, {
          original: options.rootField,
          interpolated: interpolatedRootField
        });
        
        // Look for the specified field
        const targetField = firstSeries.fields.find(field => 
          field.name === interpolatedRootField || 
          field.name?.toLowerCase() === interpolatedRootField?.toLowerCase()
        );
        
        console.log(`[JsonTreePanel] Field search result:`, {
          targetFieldFound: !!targetField,
          targetFieldName: targetField?.name,
          targetFieldType: targetField?.type,
          hasValues: !!targetField?.values?.length
        });
        
        if (targetField && targetField.values?.length > 0) {
          const rawValue = targetField.values.get(0);
          console.log(`[JsonTreePanel] Found target field '${targetField.name}', processing value...`);
          
          // Check if this is a nested field path
          if (interpolatedRootField.includes('.') || interpolatedRootField.includes('[')) {
            console.log(`[JsonTreePanel] Detected nested field path in field content`);
            const parsedData = processFieldValue(rawValue, targetField.name || 'data');
            const nestedResult = resolveNestedField(parsedData, interpolatedRootField);
            if (nestedResult !== null) {
              jsonData = nestedResult;
              foundData = true;
            } else {
              console.log(`[JsonTreePanel] Nested field resolution failed, using full field content`);
              jsonData = parsedData;
              foundData = true;
            }
          } else {
            jsonData = processFieldValue(rawValue, targetField.name || 'data');
            foundData = true;
          }
        } else {
          // If simple field not found, try to find any field and then resolve nested path
          if (interpolatedRootField.includes('.') || interpolatedRootField.includes('[')) {
            console.log(`[JsonTreePanel] Simple field not found, trying nested path resolution across all fields`);
            
            for (const field of firstSeries.fields) {
              if (field.values?.length > 0) {
                const rawValue = field.values.get(0);
                const parsedData = processFieldValue(rawValue, field.name || 'data');
                const nestedResult = resolveNestedField(parsedData, interpolatedRootField);
                
                if (nestedResult !== null) {
                  console.log(`[JsonTreePanel] Successfully resolved nested path in field '${field.name}'`);
                  jsonData = nestedResult;
                  foundData = true;
                  break;
                }
              }
            }
            
            if (!foundData) {
              errorMessage = `Nested field path "${interpolatedRootField}" not found in any field. Available fields: ${firstSeries.fields.map(f => f.name).join(', ')}`;
              console.log(`[JsonTreePanel] Nested field resolution failed:`, errorMessage);
            }
          } else {
            errorMessage = `Field "${interpolatedRootField}" not found. Available fields: ${firstSeries.fields.map(f => f.name).join(', ')}`;
            console.log(`[JsonTreePanel] Target field not found:`, errorMessage);
          }
        }
      }
      
      // If no specific field requested or field not found, use auto-detection
      if (!foundData) {
        console.log(`[JsonTreePanel] Using auto-detection, iterating through fields...`);
        for (const field of firstSeries.fields) {
          console.log(`[JsonTreePanel] Checking field '${field.name}':`, {
            type: field.type,
            hasValues: !!field.values?.length,
            valuesLength: field.values?.length || 0
          });
          
          if (field.values?.length > 0) {
            const rawValue = field.values.get(0);
            console.log(`[JsonTreePanel] Auto-detection: processing field '${field.name}' with value`);
            jsonData = processFieldValue(rawValue, field.name || 'data');
            foundData = true;
            break;
          }
        }
      }
      
      if (!foundData) {
        jsonData = { message: 'No data found in any field' };
      }
    } else {
      jsonData = { message: 'No fields found in data series' };
    }
  } catch (error) {
    errorMessage = `Error processing data: ${String(error)}`;
    // Create a debug object with available data
    jsonData = {
      error: String(error),
      debug: {
        seriesCount: data.series?.length || 0,
        firstSeriesInfo: data.series?.[0] ? {
          fieldsCount: data.series[0].fields?.length || 0,
          fieldNames: data.series[0].fields?.map(f => f.name) || []
        } : null
      }
    };
  }

  // Helper function to process field values with detailed logging
  function processFieldValue(rawValue: any, fieldName: string): any {
    console.log(`[JsonTreePanel] Processing field '${fieldName}':`, {
      type: typeof rawValue,
      value: rawValue,
      length: typeof rawValue === 'string' ? rawValue.length : 'N/A',
      first100chars: typeof rawValue === 'string' ? rawValue.substring(0, 100) + '...' : 'N/A'
    });

    // If it's already an object, use it directly
    if (typeof rawValue === 'object' && rawValue !== null) {
      console.log(`[JsonTreePanel] Field '${fieldName}' is already an object`);
      return rawValue;
    } else if (typeof rawValue === 'string') {
      // Log the raw string for debugging
      console.log(`[JsonTreePanel] Raw string value for '${fieldName}':`, rawValue);
      
      // Try to parse as JSON string
      try {
        console.log(`[JsonTreePanel] Attempting JSON.parse for field '${fieldName}'`);
        const parsed = JSON.parse(rawValue);
        console.log(`[JsonTreePanel] Successfully parsed JSON for '${fieldName}':`, parsed);
        return parsed;
      } catch (parseError) {
        console.log(`[JsonTreePanel] JSON.parse failed for '${fieldName}':`, parseError);
        console.log(`[JsonTreePanel] First 200 characters:`, rawValue.substring(0, 200));
        console.log(`[JsonTreePanel] Character codes of first 10 chars:`, 
          rawValue.substring(0, 10).split('').map((char, idx) => `${idx}: '${char}' (${char.charCodeAt(0)})`));
        
        // If JSON parse fails, check if it's a MongoDB-style string
        if (rawValue.includes('"_ansible_facts_gathered"') || rawValue.includes('"_collector_')) {
          console.log(`[JsonTreePanel] Detected MongoDB-style string, attempting cleanup for '${fieldName}'`);
          
          // Try to fix common MongoDB string format issues
          let fixedValue = rawValue;
          
          // Remove any leading/trailing quotes or escape characters
          fixedValue = fixedValue.replace(/^["']|["']$/g, '');
          console.log(`[JsonTreePanel] After quote removal:`, fixedValue.substring(0, 100));
          
          // Try to parse the fixed value
          try {
            console.log(`[JsonTreePanel] Attempting to parse cleaned MongoDB string for '${fieldName}'`);
            const parsed = JSON.parse(fixedValue);
            console.log(`[JsonTreePanel] Successfully parsed cleaned MongoDB string for '${fieldName}':`, parsed);
            return parsed;
          } catch (secondParseError) {
            console.log(`[JsonTreePanel] Second parse attempt failed for '${fieldName}':`, secondParseError);
            console.log(`[JsonTreePanel] Cleaned value first 200 chars:`, fixedValue.substring(0, 200));
            // Still can't parse, treat as string
            return { [fieldName]: rawValue };
          }
        } else {
          // For non-JSON strings, create a simple object
          console.log(`[JsonTreePanel] Treating as non-JSON string for '${fieldName}'`);
          return { [fieldName]: rawValue };
        }
      }
    } else {
      // For other data types (numbers, booleans, etc.)
      console.log(`[JsonTreePanel] Non-string data type for '${fieldName}':`, typeof rawValue);
      return { [fieldName]: rawValue };
    }
  }

  if (errorMessage) {
    return (
      <div className={styles.error}>
        <p>Error parsing JSON data:</p>
        <pre>{errorMessage}</pre>
        <details>
          <summary>Debug Information</summary>
          <TreeNode data={jsonData} keyName="debug" level={0} isLast={true} indentSize={options.indentSize || 8} expandLevel={options.expandLevel || 2} />
        </details>
      </div>
    );
  }

  // Get the interpolated root field value for display
  const interpolatedRootField = options.rootField ? replaceVariables(options.rootField) : '';

  return (
    <div className={styles.panel} style={{ width, height }}>
      <div className={styles.header}>
        <h3>JSON Tree View 
          <span className={styles.versionInfo}> v{VERSION.version} (build {VERSION.buildNumber})</span>
        </h3>
        {options.rootField && (
          <div className={styles.fieldInfo}>
            Root Field: <strong>{interpolatedRootField}</strong>
            {options.rootField !== interpolatedRootField && (
              <span className={styles.variableInfo}> (from: {options.rootField})</span>
            )}
          </div>
        )}
        <div className={styles.controls}>
          <button 
            className={styles.button}
            onClick={() => setShowDebug(!showDebug)}
          >
            {showDebug ? 'Hide Debug' : 'Show Debug'}
          </button>
          <button 
            className={styles.button}
            onClick={() => window.location.reload()}
          >
            Refresh
          </button>
        </div>
      </div>
      
      {showDebug && (
        <div className={styles.debugSection}>
          <h4>Debug Information</h4>
          <div className={styles.debugContent}>
            <h5>Plugin Version</h5>
            <div className={styles.debugItem}>
              <strong>Version:</strong> {VERSION.version}<br/>
              <strong>Build Number:</strong> {VERSION.buildNumber}<br/>
              <strong>Build Date:</strong> {VERSION.buildDate}<br/>
              <strong>Features:</strong> {VERSION.features.join(', ')}
            </div>
            
            <h5>Data Series ({data.series?.length || 0})</h5>
            {data.series?.map((series, idx) => (
              <div key={idx} className={styles.debugItem}>
                <strong>Series {idx}:</strong>
                <ul>
                  <li>Fields: {series.fields?.length || 0}</li>
                  {series.fields?.map((field, fieldIdx) => (
                    <li key={fieldIdx}>
                      <strong>{field.name}</strong> (type: {field.type}) - 
                      Values: {field.values?.length || 0}
                      {field.values?.length > 0 && (
                        <div>
                          First value: {typeof field.values.get(0)} - {String(field.values.get(0)).substring(0, 100)}...
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            
            <h5>Plugin Options</h5>
            <div className={styles.debugItem}>
              <pre>{JSON.stringify(options, null, 2)}</pre>
            </div>
            
            <h5>Processed JSON Data</h5>
            <div className={styles.debugItem}>
              <pre>{JSON.stringify(jsonData, null, 2).substring(0, 1000)}...</pre>
            </div>
          </div>
        </div>
      )}
      
      <div className={styles.content}>
        <TreeNode 
          data={jsonData} 
          keyName={options.rootField || "root"} 
          level={0} 
          isLast={true}
          indentSize={options.indentSize || 8}
          expandLevel={options.expandLevel || 2}
        />
      </div>
    </div>
  );
};

const getStyles = (theme: any, indentSize: number = 8) => {
  return {
    panel: css`
      display: flex;
      flex-direction: column;
      height: 100%;
      background: var(--background-primary);
      border: 1px solid var(--border-weak);
      border-radius: 4px;
      overflow: hidden;
    `,
    
    header: css`
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-weak);
      background: var(--background-secondary);
      
      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 500;
        color: var(--text-primary);
      }
    `,
    
    fieldInfo: css`
      font-size: 12px;
      color: var(--text-secondary);
      font-style: italic;
      
      strong {
        color: var(--text-primary);
        font-style: normal;
      }
    `,
    
    variableInfo: css`
      color: var(--text-disabled);
      font-size: 11px;
      font-style: italic;
    `,
    
    versionInfo: css`
      color: var(--text-secondary);
      font-size: 10px;
      font-weight: normal;
      margin-left: 8px;
    `,
    
    controls: css`
      display: flex;
      gap: 8px;
    `,
    
    button: css`
      padding: 6px 12px;
      background: var(--button-primary-bg);
      color: var(--button-primary-text);
      border: 1px solid var(--button-primary-border);
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      
      &:hover {
        background: var(--button-primary-bg-hover);
      }
    `,
    
    content: css`
      flex: 1;
      overflow: auto;
      padding: 16px;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 13px;
      line-height: 1.4;
    `,
    
    treeNode: css`
      margin-left: 0;
      
      &[data-level="0"] {
        margin-left: 0;
      }
      
      &[data-level="1"] {
        margin-left: ${indentSize}px;
      }
      
      &[data-level="2"] {
        margin-left: ${indentSize * 2}px;
      }
      
      &[data-level="3"] {
        margin-left: ${indentSize * 3}px;
      }
      
      &[data-level]:not([data-level="0"]):not([data-level="1"]):not([data-level="2"]):not([data-level="3"]) {
        margin-left: calc(${indentSize}px * var(--level, 4));
      }
    `,
    
    leafNode: css`
      display: flex;
      align-items: center;
      padding: 2px 0;
      gap: 8px;
    `,
    
    objectContainer: css`
      margin: 2px 0;
    `,
    
    objectHeader: css`
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      padding: 2px 4px;
      border-radius: 3px;
      
      &:hover {
        background: var(--background-secondary);
      }
    `,
    
    expandIcon: css`
      font-size: 10px;
      color: var(--text-secondary);
      user-select: none;
      width: 12px;
      text-align: center;
    `,
    
    key: css`
      color: var(--palette-blue-95);
      font-weight: 500;
    `,
    
    value: css`
      color: var(--text-primary);
      
      &[data-type="string"] {
        color: var(--palette-green-95);
      }
      
      &[data-type="number"] {
        color: var(--palette-yellow-95);
      }
      
      &[data-type="boolean"] {
        color: var(--palette-orange-95);
      }
      
      &[data-type="null"] {
        color: var(--text-disabled);
        font-style: italic;
      }
    `,
    
    objectInfo: css`
      color: var(--text-secondary);
      font-size: 11px;
      font-style: italic;
    `,
    
    children: css`
      margin-left: 0;
      border-left: 1px solid var(--border-weak);
      padding-left: ${Math.max(2, indentSize / 2)}px;
      margin-top: 1px;
    `,
    
    noData: css`
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: var(--text-secondary);
      text-align: center;
      
      p {
        margin: 8px 0;
      }
    `,
    
    error: css`
      padding: 16px;
      color: var(--palette-red-95);
      background: var(--background-primary);
      
      pre {
        background: var(--background-secondary);
        padding: 12px;
        border-radius: 4px;
        overflow: auto;
        font-size: 12px;
        margin-top: 8px;
      }
    `,
    
    debugSection: css`
      background: var(--background-secondary);
      border: 1px solid var(--border-medium);
      border-radius: 4px;
      margin: 8px 0;
      padding: 12px;
      
      h4, h5 {
        margin: 8px 0 4px 0;
        color: var(--text-primary);
        font-size: 14px;
      }
      
      h5 {
        font-size: 12px;
        color: var(--text-secondary);
      }
    `,
    
    debugContent: css`
      font-size: 11px;
      color: var(--text-secondary);
    `,
    
    debugItem: css`
      margin: 8px 0;
      padding: 8px;
      background: var(--background-primary);
      border-radius: 3px;
      
      pre {
        background: var(--background-canvas);
        padding: 8px;
        border-radius: 3px;
        overflow: auto;
        font-size: 10px;
        max-height: 200px;
      }
      
      ul {
        margin: 4px 0;
        padding-left: 16px;
      }
      
      li {
        margin: 2px 0;
        font-size: 10px;
      }
    `
  };
};
