import type {
  CSSProperties,
} from "react";

type ScoreRingProps = {
  score: number;
  bucket?:
    | "high_confidence"
    | "discovery"
    | "stretch";
  size?: "small" | "large";
};

export function ScoreRing({
  score,
  bucket = "discovery",
  size = "small",
}: ScoreRingProps) {
  const clampedScore =
    Math.max(
      0,
      Math.min(
        100,
        score,
      ),
    );

  const style = {
    "--score-progress":
      `${clampedScore}%`,
  } as CSSProperties;

  return (
    <div
      className={[
        "score-ring",
        `score-ring-${bucket}`,
        `score-ring-${size}`,
      ].join(" ")}
      style={style}
      aria-label={`${score.toFixed(1)} percent match`}
    >
      <div className="score-ring-core">
        <strong>
          {score.toFixed(1)}
        </strong>

        <span>
          match
        </span>
      </div>
    </div>
  );
}
