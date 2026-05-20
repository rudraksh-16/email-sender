import { cn, STATUS_COLOR } from "@/lib/utils";

interface BadgeProps {
  label: string;
  variant?: string;
  className?: string;
}

export function Badge({ label, variant, className }: BadgeProps) {
  const color = variant ? STATUS_COLOR[variant] ?? "bg-gray-100 text-gray-700" : "";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        color,
        className,
      )}
    >
      {label}
    </span>
  );
}
