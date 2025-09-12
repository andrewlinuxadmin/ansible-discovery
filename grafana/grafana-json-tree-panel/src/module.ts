import { PanelPlugin } from '@grafana/data';
import { JsonTreeOptions } from './types';
import { JsonTreePanel } from './JsonTreePanel';

export const plugin = new PanelPlugin<JsonTreeOptions>(JsonTreePanel).setPanelOptions(builder => {
  return builder
    .addTextInput({
      path: 'rootField',
      name: 'Root field name',
      description: 'Specify which field to use as the root of the tree. Supports nested paths with dot notation (e.g., data.ansible_dns) or bracket notation (e.g., data["ansible_dns"]). Also supports Grafana variables like $__field, $variable.',
      defaultValue: '',
      settings: {
        placeholder: 'e.g., data, data.ansible_dns, data["ansible_dns"], $__field, $myVariable',
      },
    })
    .addBooleanSwitch({
      path: 'showTypes',
      name: 'Show data types',
      description: 'Display data type indicators next to values',
      defaultValue: true,
    })
    .addNumberInput({
      path: 'expandLevel',
      name: 'Auto-expand levels',
      description: 'Number of levels to automatically expand (0 = collapsed, -1 = all)',
      defaultValue: 2,
      settings: {
        min: -1,
        max: 10,
      },
    })
    .addNumberInput({
      path: 'maxStringLength',
      name: 'Max string preview length',
      description: 'Maximum length for string value previews',
      defaultValue: 50,
      settings: {
        min: 10,
        max: 200,
      },
    })
    .addNumberInput({
      path: 'indentSize',
      name: 'Indentation size (px)',
      description: 'Size of indentation per level in pixels',
      defaultValue: 8,
      settings: {
        min: 2,
        max: 32,
        step: 2,
      },
    });
});

// Export the plugin
export { JsonTreePanel };
