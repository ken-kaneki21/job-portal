import {
  useEffect,
  useRef,
} from "react";

type NetworkNode = {
  x: number;
  y: number;

  baseX: number;
  baseY: number;

  velocityX: number;
  velocityY: number;

  radius: number;
  phase: number;
};

type Pulse = {
  x: number;
  y: number;

  radius: number;
  opacity: number;
};

type RGB = {
  r: number;
  g: number;
  b: number;
};

function parseHexColor(
  value: string,
): RGB {
  const normalized =
    value
      .trim()
      .replace("#", "");

  if (
    normalized.length === 3
  ) {
    return {
      r: parseInt(
        normalized[0] +
          normalized[0],
        16,
      ),

      g: parseInt(
        normalized[1] +
          normalized[1],
        16,
      ),

      b: parseInt(
        normalized[2] +
          normalized[2],
        16,
      ),
    };
  }

  if (
    normalized.length === 6
  ) {
    return {
      r: parseInt(
        normalized.slice(
          0,
          2,
        ),
        16,
      ),

      g: parseInt(
        normalized.slice(
          2,
          4,
        ),
        16,
      ),

      b: parseInt(
        normalized.slice(
          4,
          6,
        ),
        16,
      ),
    };
  }

  return {
    r: 141,
    g: 214,
    b: 202,
  };
}

function rgba(
  rgb: RGB,
  alpha: number,
): string {
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
}

function distanceBetween(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
): number {
  const dx =
    x1 - x2;

  const dy =
    y1 - y2;

  return Math.sqrt(
    dx * dx +
      dy * dy,
  );
}

export function IntelligenceBackground() {
  const canvasRef =
    useRef<HTMLCanvasElement | null>(
      null,
    );

  useEffect(() => {
    const canvasElement =
      canvasRef.current;

    if (!canvasElement) {
      return;
    }

    const drawingContext =
      canvasElement.getContext(
        "2d",
      );

    if (!drawingContext) {
      return;
    }

    const canvas =
      canvasElement;

    const context =
      drawingContext;

    const reducedMotionQuery =
      window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      );

    const prefersReducedMotion =
      reducedMotionQuery.matches;

    let width =
      window.innerWidth;

    let height =
      window.innerHeight;

    let nodes:
      NetworkNode[] = [];

    let pulses:
      Pulse[] = [];

    let frameId = 0;

    let previousFrame = 0;

    let hidden =
      document.hidden;

    let isDarkTheme =
      document
        .documentElement
        .dataset
        .theme ===
      "dark";

    let accent =
      parseHexColor(
        getComputedStyle(
          document.documentElement,
        )
          .getPropertyValue(
            "--accent",
          )
          .trim(),
      );

    const pointer = {
      x: width * 0.6,
      y: height * 0.4,
      active: false,
    };

    function refreshTheme() {
      isDarkTheme =
        document
          .documentElement
          .dataset
          .theme ===
        "dark";

      accent =
        parseHexColor(
          getComputedStyle(
            document.documentElement,
          )
            .getPropertyValue(
              "--accent",
            )
            .trim(),
        );
    }

    function createNodes() {
      const area =
        width * height;

      const targetCount =
        Math.max(
          24,
          Math.min(
            48,
            Math.round(
              area /
                32000,
            ),
          ),
        );

      nodes =
        Array.from(
          {
            length:
              targetCount,
          },
          (
            _,
            index,
          ) => {
            const x =
              Math.random() *
              width;

            const y =
              Math.random() *
              height;

            return {
              x,
              y,

              baseX: x,
              baseY: y,

              velocityX:
                (
                  Math.random() -
                  0.5
                ) *
                0.08,

              velocityY:
                (
                  Math.random() -
                  0.5
                ) *
                0.08,

              radius:
                index % 8 ===
                0
                  ? 1.8
                  : 1.1,

              phase:
                Math.random() *
                Math.PI *
                2,
            };
          },
        );
    }

    function resize() {
      width =
        window.innerWidth;

      height =
        window.innerHeight;

      const ratio =
        Math.min(
          window.devicePixelRatio ||
            1,
          1.5,
        );

      canvas.width =
        Math.floor(
          width * ratio,
        );

      canvas.height =
        Math.floor(
          height * ratio,
        );

      canvas.style.width =
        `${width}px`;

      canvas.style.height =
        `${height}px`;

      context.setTransform(
        ratio,
        0,
        0,
        ratio,
        0,
        0,
      );

      refreshTheme();

      createNodes();
    }

    function updateNodes(
      time: number,
    ) {
      for (
        const node of nodes
      ) {
        const driftX =
          Math.cos(
            time *
              0.00022 +
              node.phase,
          ) *
          7;

        const driftY =
          Math.sin(
            time *
              0.00018 +
              node.phase,
          ) *
          7;

        const targetX =
          node.baseX +
          driftX;

        const targetY =
          node.baseY +
          driftY;

        node.velocityX +=
          (
            targetX -
            node.x
          ) *
          0.002;

        node.velocityY +=
          (
            targetY -
            node.y
          ) *
          0.002;

        if (
          pointer.active
        ) {
          const dx =
            node.x -
            pointer.x;

          const dy =
            node.y -
            pointer.y;

          const distance =
            Math.max(
              1,
              Math.sqrt(
                dx * dx +
                  dy * dy,
              ),
            );

          const influenceRadius =
            270;

          if (
            distance <
            influenceRadius
          ) {
            const influence =
              1 -
              distance /
                influenceRadius;

            const force =
              influence *
              influence *
              0.18;

            node.velocityX +=
              (
                dx /
                distance
              ) *
              force;

            node.velocityY +=
              (
                dy /
                distance
              ) *
              force;

            const tangentX =
              -dy /
              distance;

            const tangentY =
              dx /
              distance;

            node.velocityX +=
              tangentX *
              influence *
              0.015;

            node.velocityY +=
              tangentY *
              influence *
              0.015;
          }
        }

        node.velocityX *=
          0.94;

        node.velocityY *=
          0.94;

        node.x +=
          node.velocityX;

        node.y +=
          node.velocityY;

        if (
          node.x < -40 ||
          node.x >
            width + 40 ||
          node.y < -40 ||
          node.y >
            height + 40
        ) {
          node.x =
            node.baseX;

          node.y =
            node.baseY;

          node.velocityX =
            0;

          node.velocityY =
            0;
        }
      }
    }

    function drawConnections() {
      const maximumDistance =
        isDarkTheme
          ? 155
          : 175;

      const baseAlpha =
        isDarkTheme
          ? 0.035
          : 0.075;

      const strengthAlpha =
        isDarkTheme
          ? 0.06
          : 0.105;

      for (
        let i = 0;
        i <
        nodes.length;
        i += 1
      ) {
        for (
          let j =
            i + 1;
          j <
          nodes.length;
          j += 1
        ) {
          const first =
            nodes[i];

          const second =
            nodes[j];

          const distance =
            distanceBetween(
              first.x,
              first.y,
              second.x,
              second.y,
            );

          if (
            distance >
            maximumDistance
          ) {
            continue;
          }

          const strength =
            1 -
            distance /
              maximumDistance;

          let pointerBoost = 0;

          if (
            pointer.active
          ) {
            const midpointX =
              (
                first.x +
                second.x
              ) /
              2;

            const midpointY =
              (
                first.y +
                second.y
              ) /
              2;

            const pointerDistance =
              distanceBetween(
                midpointX,
                midpointY,
                pointer.x,
                pointer.y,
              );

            if (
              pointerDistance <
              250
            ) {
              pointerBoost =
                (
                  1 -
                  pointerDistance /
                    250
                ) *
                (
                  isDarkTheme
                    ? 0.065
                    : 0.09
                );
            }
          }

          context.strokeStyle =
            rgba(
              accent,
              baseAlpha +
                strength *
                  strengthAlpha +
                pointerBoost,
            );

          context.lineWidth =
            isDarkTheme
              ? 0.75
              : 0.9;

          context.beginPath();

          context.moveTo(
            first.x,
            first.y,
          );

          context.lineTo(
            second.x,
            second.y,
          );

          context.stroke();
        }
      }
    }

    function drawPointerLinks() {
      if (
        !pointer.active ||
        prefersReducedMotion
      ) {
        return;
      }

      const closestNodes =
        nodes
          .map(
            (node) => ({
              node,

              distance:
                distanceBetween(
                  pointer.x,
                  pointer.y,
                  node.x,
                  node.y,
                ),
            }),
          )
          .filter(
            ({ distance }) =>
              distance <
              265,
          )
          .sort(
            (
              first,
              second,
            ) =>
              first.distance -
              second.distance,
          )
          .slice(
            0,
            6,
          );

      for (
        const {
          node,
          distance,
        } of closestNodes
      ) {
        const strength =
          1 -
          distance /
            265;

        const gradient =
          context.createLinearGradient(
            pointer.x,
            pointer.y,
            node.x,
            node.y,
          );

        gradient.addColorStop(
          0,
          rgba(
            accent,
            (
              isDarkTheme
                ? 0.2
                : 0.24
            ) *
              strength,
          ),
        );

        gradient.addColorStop(
          1,
          rgba(
            accent,
            0.02,
          ),
        );

        context.strokeStyle =
          gradient;

        context.lineWidth =
          0.8;

        context.beginPath();

        context.moveTo(
          pointer.x,
          pointer.y,
        );

        context.lineTo(
          node.x,
          node.y,
        );

        context.stroke();
      }
    }

    function drawNodes(
      time: number,
    ) {
      for (
        const node of nodes
      ) {
        const pulse =
          0.7 +
          Math.sin(
            time *
              0.0011 +
              node.phase,
          ) *
            0.2;

        context.fillStyle =
          rgba(
            accent,
            (
              isDarkTheme
                ? 0.14
                : 0.24
            ) *
              pulse,
          );

        context.beginPath();

        context.arc(
          node.x,
          node.y,
          node.radius,
          0,
          Math.PI * 2,
        );

        context.fill();
      }
    }

    function drawPointerField() {
      if (
        !pointer.active
      ) {
        return;
      }

      const radius =
        210;

      const gradient =
        context.createRadialGradient(
          pointer.x,
          pointer.y,
          0,
          pointer.x,
          pointer.y,
          radius,
        );

      gradient.addColorStop(
        0,
        rgba(
          accent,
          isDarkTheme
            ? 0.045
            : 0.065,
        ),
      );

      gradient.addColorStop(
        1,
        rgba(
          accent,
          0,
        ),
      );

      context.fillStyle =
        gradient;

      context.fillRect(
        pointer.x -
          radius,
        pointer.y -
          radius,
        radius * 2,
        radius * 2,
      );

      if (
        !prefersReducedMotion
      ) {
        context.fillStyle =
          rgba(
            accent,
            isDarkTheme
              ? 0.3
              : 0.4,
          );

        context.beginPath();

        context.arc(
          pointer.x,
          pointer.y,
          1.6,
          0,
          Math.PI * 2,
        );

        context.fill();
      }
    }

    function drawPulses() {
      pulses =
        pulses.filter(
          (pulse) =>
            pulse.opacity >
            0.003,
        );

      for (
        const pulse of pulses
      ) {
        context.strokeStyle =
          rgba(
            accent,
            pulse.opacity,
          );

        context.lineWidth =
          1;

        context.beginPath();

        context.arc(
          pulse.x,
          pulse.y,
          pulse.radius,
          0,
          Math.PI * 2,
        );

        context.stroke();

        pulse.radius +=
          3.1;

        pulse.opacity *=
          0.95;
      }
    }

    function render(
      time: number,
    ) {
      frameId =
        requestAnimationFrame(
          render,
        );

      if (
        hidden ||
        time -
          previousFrame <
          33
      ) {
        return;
      }

      previousFrame =
        time;

      context.clearRect(
        0,
        0,
        width,
        height,
      );

      if (
        !prefersReducedMotion
      ) {
        updateNodes(
          time,
        );
      }

      drawPointerField();

      drawConnections();

      drawPointerLinks();

      drawNodes(
        time,
      );

      drawPulses();
    }

    function handlePointerMove(
      event: PointerEvent,
    ) {
      pointer.x =
        event.clientX;

      pointer.y =
        event.clientY;

      pointer.active =
        true;
    }

    function handlePointerLeave() {
      pointer.active =
        false;
    }

    function handlePointerDown(
      event: PointerEvent,
    ) {
      if (
        prefersReducedMotion
      ) {
        return;
      }

      pulses.push({
        x: event.clientX,
        y: event.clientY,
        radius: 7,
        opacity:
          isDarkTheme
            ? 0.22
            : 0.3,
      });

      if (
        pulses.length >
        7
      ) {
        pulses.shift();
      }

      for (
        const node of nodes
      ) {
        const dx =
          node.x -
          event.clientX;

        const dy =
          node.y -
          event.clientY;

        const distance =
          Math.max(
            1,
            Math.sqrt(
              dx * dx +
                dy * dy,
            ),
          );

        const radius =
          320;

        if (
          distance <
          radius
        ) {
          const influence =
            1 -
            distance /
              radius;

          const force =
            influence *
            1.7;

          node.velocityX +=
            (
              dx /
              distance
            ) *
            force;

          node.velocityY +=
            (
              dy /
              distance
            ) *
            force;
        }
      }
    }

    function handleVisibility() {
      hidden =
        document.hidden;
    }

    const themeObserver =
      new MutationObserver(
        refreshTheme,
      );

    themeObserver.observe(
      document.documentElement,
      {
        attributes: true,
        attributeFilter: [
          "data-theme",
        ],
      },
    );

    resize();

    window.addEventListener(
      "resize",
      resize,
    );

    window.addEventListener(
      "pointermove",
      handlePointerMove,
      {
        passive: true,
      },
    );

    document.addEventListener(
      "pointerleave",
      handlePointerLeave,
    );

    window.addEventListener(
      "pointerdown",
      handlePointerDown,
      {
        passive: true,
      },
    );

    document.addEventListener(
      "visibilitychange",
      handleVisibility,
    );

    frameId =
      requestAnimationFrame(
        render,
      );

    return () => {
      cancelAnimationFrame(
        frameId,
      );

      themeObserver.disconnect();

      window.removeEventListener(
        "resize",
        resize,
      );

      window.removeEventListener(
        "pointermove",
        handlePointerMove,
      );

      document.removeEventListener(
        "pointerleave",
        handlePointerLeave,
      );

      window.removeEventListener(
        "pointerdown",
        handlePointerDown,
      );

      document.removeEventListener(
        "visibilitychange",
        handleVisibility,
      );
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="intelligence-background"
      aria-hidden="true"
    />
  );
}
