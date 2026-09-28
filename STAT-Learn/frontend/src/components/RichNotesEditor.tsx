"use client";

import { useEffect, useRef, type ReactNode } from "react";
import {
  Bold,
  Italic,
  Heading1,
  Heading2,
  List,
  ListOrdered,
  Table,
  Underline,
} from "lucide-react";

type Props = {
  value: string;
  onChange: (html: string) => void;
  disabled?: boolean;
  placeholder?: string;
};

function exec(cmd: string, value?: string) {
  document.execCommand(cmd, false, value);
}

export function RichNotesEditor({ value, onChange, disabled, placeholder }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const lastExternal = useRef<string>("");

  useEffect(() => {
    if (!ref.current) return;
    if (value !== lastExternal.current && value !== ref.current.innerHTML) {
      ref.current.innerHTML = value || "";
      lastExternal.current = value;
    }
  }, [value]);

  const emit = () => {
    if (!ref.current) return;
    const html = ref.current.innerHTML;
    lastExternal.current = html;
    onChange(html);
  };

  const insertTable = () => {
    const html =
      "<table style='width:100%;border-collapse:collapse;margin:8px 0'>" +
      "<tr><th style='border:1px solid #444;padding:6px'>Header</th><th style='border:1px solid #444;padding:6px'>Header</th></tr>" +
      "<tr><td style='border:1px solid #444;padding:6px'>Cell</td><td style='border:1px solid #444;padding:6px'>Cell</td></tr>" +
      "</table><p><br/></p>";
    document.execCommand("insertHTML", false, html);
    emit();
  };

  return (
    <div className="flex flex-col h-full min-h-0 rounded-xl border border-border/60 bg-black/30 overflow-hidden">
      <div className="flex flex-wrap items-center gap-1 px-2 py-2 border-b border-border/50 bg-card/40 shrink-0">
        <ToolbarButton
          title="Title"
          disabled={disabled}
          onClick={() => {
            exec("formatBlock", "h1");
            emit();
          }}
        >
          <Heading1 className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton
          title="Heading"
          disabled={disabled}
          onClick={() => {
            exec("formatBlock", "h2");
            emit();
          }}
        >
          <Heading2 className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton
          title="Bold"
          disabled={disabled}
          onClick={() => {
            exec("bold");
            emit();
          }}
        >
          <Bold className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton
          title="Italic"
          disabled={disabled}
          onClick={() => {
            exec("italic");
            emit();
          }}
        >
          <Italic className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton
          title="Underline"
          disabled={disabled}
          onClick={() => {
            exec("underline");
            emit();
          }}
        >
          <Underline className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton
          title="Bullets"
          disabled={disabled}
          onClick={() => {
            exec("insertUnorderedList");
            emit();
          }}
        >
          <List className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton
          title="Numbered list"
          disabled={disabled}
          onClick={() => {
            exec("insertOrderedList");
            emit();
          }}
        >
          <ListOrdered className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton title="Table" disabled={disabled} onClick={insertTable}>
          <Table className="w-4 h-4" />
        </ToolbarButton>
      </div>
      <div
        ref={ref}
        contentEditable={!disabled}
        suppressContentEditableWarning
        onInput={emit}
        onBlur={emit}
        data-placeholder={placeholder || "Write structured notes…"}
        className="flex-1 min-h-[200px] overflow-y-auto px-4 py-3 text-sm text-zinc-200 leading-relaxed outline-none empty:before:content-[attr(data-placeholder)] empty:before:text-zinc-600 prose prose-invert prose-sm max-w-none
          [&_h1]:text-xl [&_h1]:font-bold [&_h1]:mb-2
          [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:mb-2
          [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5
          [&_table]:w-full [&_th]:text-left"
      />
    </div>
  );
}

function ToolbarButton({
  children,
  onClick,
  disabled,
  title,
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  title: string;
}) {
  return (
    <button
      type="button"
      title={title}
      disabled={disabled}
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
      className="p-1.5 rounded-md text-zinc-300 hover:bg-white/10 hover:text-white disabled:opacity-40"
    >
      {children}
    </button>
  );
}
