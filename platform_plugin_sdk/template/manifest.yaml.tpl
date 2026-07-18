id: {{PLUGIN_ID}}
name: {{PLUGIN_NAME}}
version: 1.0.0
author: {{AUTHOR}}
description: {{DESCRIPTION}}
platform_version: ">=1.0.0"
dependencies:
  required: []
  optional: []
permissions:
  - {{PLUGIN_ID}}.read
  - {{PLUGIN_ID}}.write
configuration:
  vertical_code: {{VERTICAL_CODE}}
routes: []
workflows: []
entry_point: plugin:create_plugin
