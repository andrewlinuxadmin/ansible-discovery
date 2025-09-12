export interface JsonTreeOptions {
  // Field selection
  rootField?: string;
  
  // Display options
  showTypes?: boolean;
  expandLevel?: number;
  theme?: 'light' | 'dark' | 'auto';
  maxStringLength?: number;
  indentSize?: number; // Indentation in pixels
  
  // Tree behavior
  autoExpandLevels?: number;
}
