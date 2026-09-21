import {
  type ComponentPropsWithoutRef,
  type PointerEvent,
  useCallback,
} from "react";

type InteractiveSurfaceProps =
  ComponentPropsWithoutRef<"div"> & {
    glow?: boolean;
    lift?: boolean;
  };

export function InteractiveSurface({
  children,
  className = "",
  glow = true,
  lift = true,
  onPointerMove,
  onPointerLeave,
  ...props
}: InteractiveSurfaceProps) {
  const handlePointerMove = useCallback(
    (
      event: PointerEvent<HTMLDivElement>,
    ) => {
      if (glow) {
        const element =
          event.currentTarget;

        const rect =
          element.getBoundingClientRect();

        const x =
          event.clientX - rect.left;

        const y =
          event.clientY - rect.top;

        element.style.setProperty(
          "--pointer-x",
          `${x}px`,
        );

        element.style.setProperty(
          "--pointer-y",
          `${y}px`,
        );

        element.style.setProperty(
          "--pointer-opacity",
          "1",
        );
      }

      onPointerMove?.(event);
    },
    [
      glow,
      onPointerMove,
    ],
  );

  const handlePointerLeave =
    useCallback(
      (
        event: PointerEvent<HTMLDivElement>,
      ) => {
        event.currentTarget.style.setProperty(
          "--pointer-opacity",
          "0",
        );

        onPointerLeave?.(
          event,
        );
      },
      [
        onPointerLeave,
      ],
    );

  const classes = [
    "interactive-surface",
    glow
      ? "interactive-surface-glow"
      : "",
    lift
      ? "interactive-surface-lift"
      : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={classes}
      onPointerMove={
        handlePointerMove
      }
      onPointerLeave={
        handlePointerLeave
      }
      {...props}
    >
      {children}
    </div>
  );
}
