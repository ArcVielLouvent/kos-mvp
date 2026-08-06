import type { ReactNode } from "react";

export function TopBar({
    title,
    description,
    action,
}: {
    title: string;
    description?: string;
    action?: ReactNode;
}) {
    return (
        <div className="flex items-center justify-between border-b border-navy-100 bg-white px-8 py-5">
            <div>
                <h2 className="text-lg font-semibold text-ink">{title}</h2>
                {description && (
                    <p className="mt-0.5 text-sm text-ink-muted">{description}</p>
                )}
            </div>
            {action}
        </div>
    );
}