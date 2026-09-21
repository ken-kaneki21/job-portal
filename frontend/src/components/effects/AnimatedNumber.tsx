import {
  useEffect,
  useRef,
  useState,
} from "react";

type AnimatedNumberProps = {
  value: string;
  duration?: number;
};

function parseValue(
  value: string,
): number | null {
  const normalized =
    value.replace(
      /[^0-9.-]/g,
      "",
    );

  if (!normalized) {
    return null;
  }

  const number =
    Number(normalized);

  return Number.isFinite(
    number,
  )
    ? number
    : null;
}

function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-IN",
    {
      maximumFractionDigits:
        Number.isInteger(value)
          ? 0
          : 1,
    },
  ).format(value);
}

export function AnimatedNumber({
  value,
  duration = 650,
}: AnimatedNumberProps) {
  const numericValue =
    parseValue(value);

  const [
    displayed,
    setDisplayed,
  ] = useState(
    numericValue ?? 0,
  );

  const previousValue =
    useRef(
      numericValue ?? 0,
    );

  useEffect(() => {
    if (
      numericValue === null
    ) {
      return;
    }

    const targetValue =
      numericValue;

    const prefersReducedMotion =
      window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;

    const startValue =
      previousValue.current;

    let frameId = 0;

    if (
      prefersReducedMotion
    ) {
      frameId =
        requestAnimationFrame(
          () => {
            setDisplayed(
              targetValue,
            );

            previousValue.current =
              targetValue;
          },
        );

      return () => {
        cancelAnimationFrame(
          frameId,
        );
      };
    }

    const difference =
      targetValue -
      startValue;

    const startTime =
      performance.now();

    function update(
      now: number,
    ) {
      const elapsed =
        now - startTime;

      const progress =
        Math.min(
          elapsed / duration,
          1,
        );

      const eased =
        1 -
        Math.pow(
          1 - progress,
          3,
        );

      const current =
        startValue +
        difference *
          eased;

      setDisplayed(
        current,
      );

      if (
        progress < 1
      ) {
        frameId =
          requestAnimationFrame(
            update,
          );
      } else {
        previousValue.current =
          targetValue;
      }
    }

    frameId =
      requestAnimationFrame(
        update,
      );

    return () => {
      cancelAnimationFrame(
        frameId,
      );
    };
  }, [
    numericValue,
    duration,
  ]);

  if (
    numericValue === null
  ) {
    return <>{value}</>;
  }

  return (
    <>
      {formatNumber(
        displayed,
      )}
    </>
  );
}
