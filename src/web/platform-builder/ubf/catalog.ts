export const UBF_STEPS = [
  "Universal Builder Template",
  "Universal UI Components",
  "Validation Framework",
  "Live Preview Engine",
  "Builder Registry",
  "Template Engine",
  "Extension System",
  "Builder SDK",
  "Summary",
  "Create",
] as const;

export const LIFECYCLE = [
  "Initialize",
  "Configure",
  "Validate",
  "Preview",
  "Summary",
  "Create",
  "Register",
  "Finish",
] as const;

export const UI_COMPONENTS = [
  "Wizard",
  "Cards",
  "Forms",
  "Progress Bar",
  "Stepper",
  "Preview Window",
  "Summary Screen",
  "Confirmation Screen",
  "Live Validation",
  "Animations",
] as const;

export const VALIDATION_RULES = [
  { id: "required_fields", name: "Required Fields" },
  { id: "duplicate_detection", name: "Duplicate Detection" },
  { id: "registry_validation", name: "Registry Validation" },
  { id: "dependency_validation", name: "Dependency Validation" },
  { id: "knowledge_validation", name: "Knowledge Validation" },
  { id: "relationship_validation", name: "Relationship Validation" },
  { id: "live_error_detection", name: "Live Error Detection" },
  { id: "suggestion_engine", name: "Suggestion Engine" },
] as const;

export const PREVIEW_CAPABILITIES = [
  "Instant Preview",
  "Live Update",
  "Realtime Validation",
  "Visual Summary",
] as const;

export const TARGET_BUILDERS = [
  "AI Builder",
  "Concierge Builder",
  "Vertical Builder",
  "Workflow Builder",
  "CRM Builder",
  "ERP Builder",
  "Knowledge Builder",
  "Marketplace Builder",
  "Dashboard Builder",
  "Automation Builder",
  "Document Builder",
  "Department Builder",
  "User Builder",
  "Future Builders",
] as const;

export const EXTENSION_TYPES = [
  "Plugins",
  "Custom Steps",
  "Custom Validation",
  "Custom Components",
  "Future Marketplace Extensions",
] as const;

export type UbfDraft = {
  name: string;
  builderType: string;
  version: string;
  components: string[];
  validationRules: string[];
  saveAsTemplate: boolean;
  extensions: string[];
};

export function emptyUbfDraft(): UbfDraft {
  return {
    name: "",
    builderType: "",
    version: "1.0.0",
    components: [...UI_COMPONENTS],
    validationRules: VALIDATION_RULES.map((r) => r.id),
    saveAsTemplate: true,
    extensions: ["Plugins"],
  };
}
