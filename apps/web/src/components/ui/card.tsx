import { cn } from "@/lib/utils";

export function Card({
  className,
  flat = false,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { flat?: boolean }) {
  return (
    <div
      className={cn(
        flat ? "glass-panel-flat" : "glass-panel",
        "p-5",
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center justify-between gap-3 mb-4", className)}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "text-sm font-medium text-foreground-muted tracking-wide uppercase",
        className
      )}
      {...props}
    />
  );
}

export function CardContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn(className)} {...props} />;
}
