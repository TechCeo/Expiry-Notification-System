import { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

type FieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
};

export function Field({ label, error, ...props }: FieldProps) {
  return (
    <label className="field">
      <span>{label}</span>
      <input {...props} />
      {error ? <small role="alert">{error}</small> : null}
    </label>
  );
}

type SelectFieldProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  error?: string;
};

export function SelectField({ label, error, children, ...props }: SelectFieldProps) {
  return (
    <label className="field">
      <span>{label}</span>
      <select {...props}>{children}</select>
      {error ? <small role="alert">{error}</small> : null}
    </label>
  );
}

type TextAreaFieldProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  error?: string;
};

export function TextAreaField({ label, error, ...props }: TextAreaFieldProps) {
  return (
    <label className="field field-wide">
      <span>{label}</span>
      <textarea {...props} />
      {error ? <small role="alert">{error}</small> : null}
    </label>
  );
}
