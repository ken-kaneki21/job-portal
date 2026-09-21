import {
  type ReactNode,
  useEffect,
  useRef,
  useState,
} from "react";

type RevealProps = {
  children: ReactNode;
  className?: string;
  delay?: number;
};

function shouldReduceMotion(): boolean {
  if (
    typeof window ===
    "undefined"
  ) {
    return false;
  }

  return window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
}

export function Reveal({
  children,
  className = "",
  delay = 0,
}: RevealProps) {
  const elementRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const [
    visible,
    setVisible,
  ] = useState(
    () =>
      shouldReduceMotion(),
  );

  useEffect(() => {
    if (visible) {
      return;
    }

    const element =
      elementRef.current;

    if (!element) {
      return;
    }

    const observer =
      new IntersectionObserver(
        ([entry]) => {
          if (
            entry.isIntersecting
          ) {
            setVisible(true);

            observer.unobserve(
              entry.target,
            );
          }
        },
        {
          threshold: 0.08,
          rootMargin:
            "0px 0px -30px 0px",
        },
      );

    observer.observe(
      element,
    );

    return () => {
      observer.disconnect();
    };
  }, [
    visible,
  ]);

  return (
    <div
      ref={elementRef}
      className={[
        "reveal",
        visible
          ? "reveal-visible"
          : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      style={{
        transitionDelay:
          visible
            ? `${delay}ms`
            : "0ms",
      }}
    >
      {children}
    </div>
  );
}
