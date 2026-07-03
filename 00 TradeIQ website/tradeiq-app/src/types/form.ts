export type FieldType = 'text' | 'tel' | 'email' | 'textarea' | 'radio';

export interface FormCondition {
  fieldId: string;
  equals: string;
}

export interface FormField {
  id: string;
  label: string;
  type: FieldType;
  required?: boolean;
  placeholder?: string;
  options?: string[]; // For radio types
  condition?: FormCondition; // Field will only render if this condition is true
}

export interface FormSection {
  id: number;
  title: string;
  fields: FormField[];
}

// We use a generic Record for the form data so it naturally scales 
// as fields are added or removed from the configuration.
export type RegistrationFormData = Record<string, string>;
