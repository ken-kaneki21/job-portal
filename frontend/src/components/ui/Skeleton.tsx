type SkeletonProps = {
  className?: string;
};

export function Skeleton({
  className = "",
}: SkeletonProps) {
  return (
    <div
      className={[
        "skeleton",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-hidden="true"
    />
  );
}
