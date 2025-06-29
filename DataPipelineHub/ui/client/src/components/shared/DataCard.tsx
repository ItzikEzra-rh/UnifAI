import { useState } from "react";
import { motion } from "framer-motion";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ConfirmDialog } from "./ConfirmDialog";

export interface CardAction {
    icon: React.ReactNode;
    onClick: () => void;
    confirm?: {
        title: string;
        message: string;
        confirmLabel?: string;
        cancelLabel?: string;
        onConfirm: () => void;
        loading?: boolean;
    };
}

interface DataCardProps {
    icon?: React.ReactNode;
    iconRenderer?: () => React.ReactNode;
    iconBgClass?: string;
    title?: React.ReactNode;
    subtitle?: React.ReactNode;
    metadata?: React.ReactNode;
    footer?: React.ReactNode;
    actions?: CardAction[];
    statusBadge?: { label: string; className?: string };
    extraTopRight?: React.ReactNode;
    onClick?: () => void;
    selected?: boolean;
    hoverable?: boolean;
    className?: string;
}

export const DataCard: React.FC<DataCardProps> = ({
    icon,
    iconRenderer,
    iconBgClass = "bg-muted",
    title,
    subtitle,
    metadata,
    footer,
    actions = [],
    statusBadge,
    extraTopRight,
    onClick,
    selected = false,
    hoverable = true,
    className = "",
}) => {
    const [confirmAction, setConfirmAction] = useState<CardAction | null>(null);

    const cardClasses = `
        bg-background-dark p-4 rounded-lg border 
        ${selected ? "border-primary" : "border-gray-800"} 
        ${hoverable ? "hover:border-primary transition-colors cursor-pointer" : ""}
        ${className}
    `;

    return (
        <>
            <motion.div
                whileHover={hoverable ? { y: -5, transition: { duration: 0.2 } } : {}}
                className={cardClasses}
                onClick={onClick}
            >
                {/* Icon + Title/Subtitle */}
                <div className="flex items-start justify-between">
                    <div className="flex items-start">
                        {(icon || iconRenderer) && (
                            <div className={`mr-3 p-2 rounded-md shrink-0 ${iconBgClass}`}>
                                {icon || (iconRenderer && iconRenderer())}
                            </div>
                        )}
                        <div className="flex-1 min-w-0">
                            {title && (
                                <h4 className="font-medium text-sm break-words line-clamp-2">
                                    {title}
                                </h4>
                            )}
                            {subtitle && <div className="text-xs text-gray-400 mt-1 truncate">{subtitle}</div>}
                        </div>

                    </div>
                    {extraTopRight}
                </div>

                {/* Metadata and Status */}
                {(metadata || statusBadge) && (
                    <div className="mt-3 flex items-center justify-between text-xs">
                        {metadata && <div className="text-gray-400">{metadata}</div>}
                        {statusBadge && (
                            <Badge className={`text-xs ${statusBadge.className || ""}`}>
                                {statusBadge.label}
                            </Badge>
                        )}
                    </div>
                )}

                {/* Footer and Actions */}
                {(footer || actions.length > 0) && (
                    <div className="mt-3 flex justify-between text-xs items-center">
                        {footer && <div className="text-gray-400">{footer}</div>}
                        {actions.length > 0 && (
                            <div className="flex items-center space-x-2">
                                {actions.map((action, idx) => (
                                    <Button
                                        key={idx}
                                        variant="ghost"
                                        size="sm"
                                        className="h-7 w-7 p-0"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            if (action.confirm) { setConfirmAction(action); } else { action.onClick(); }
                                        }}>
                                        {action.icon}
                                    </Button>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </motion.div>

            {/* Confirm Modal */}
            {confirmAction && (
                <ConfirmDialog
                    open={true}
                    title={confirmAction.confirm?.title || ""}
                    message={confirmAction.confirm?.message || ""}
                    confirmLabel={confirmAction.confirm?.confirmLabel}
                    cancelLabel={confirmAction.confirm?.cancelLabel}
                    onConfirm={() => {
                        confirmAction.confirm?.onConfirm();
                        setConfirmAction(null);
                    }}
                    onCancel={() => setConfirmAction(null)}
                    loading={confirmAction.confirm?.loading}
                />
            )}

        </>
    );
};
