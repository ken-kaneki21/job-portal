import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  Command,
  LoaderCircle,
  Moon,
  Search,
  Sun,
  Zap,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { CommandPalette } from "../command/CommandPalette";
import {
  getPipelineHealth,
  getWorkflowStatus,
  startPipeline,
} from "../../features/automations/pipelineApi";

const POLL_INTERVAL_MS =
  3_000;

const MAX_RUNTIME_MS =
  20 * 60 * 1_000;

const STORAGE_WORKFLOW_ID =
  "jobintel-active-workflow-id";

const STORAGE_STARTED_AT =
  "jobintel-active-workflow-started-at";

type RunState =
  | "idle"
  | "starting"
  | "running"
  | "completed"
  | "failed";

function normalizeWorkflowStatus(
  value: string | null,
): RunState {
  if (!value) {
    return "idle";
  }

  const status =
    value.toUpperCase();

  if (
    status === "RUNNING" ||
    status === "STARTED"
  ) {
    return "running";
  }

  if (
    status === "COMPLETED"
  ) {
    return "completed";
  }

  if (
    status === "FAILED" ||
    status === "CANCELED" ||
    status === "TERMINATED" ||
    status === "TIMED_OUT"
  ) {
    return "failed";
  }

  return "running";
}

export function Topbar() {
  const queryClient =
    useQueryClient();

  const [
    commandPaletteOpen,
    setCommandPaletteOpen,
  ] = useState(false);

  const [
    darkMode,
    setDarkMode,
  ] = useState(() => {
    return (
      localStorage.getItem(
        "jobintel-theme",
      ) !== "light"
    );
  });

  const [
    workflowId,
    setWorkflowId,
  ] = useState<string | null>(
    () =>
      localStorage.getItem(
        STORAGE_WORKFLOW_ID,
      ),
  );

  const [
    runState,
    setRunState,
  ] = useState<RunState>(
    workflowId
      ? "running"
      : "idle",
  );

  const [
    statusMessage,
    setStatusMessage,
  ] = useState<string | null>(
    workflowId
      ? "Restoring run status"
      : null,
  );

  const [
    progressPercent,
    setProgressPercent,
  ] = useState<number | null>(
    workflowId
      ? 0
      : null,
  );

  const pollingRef =
    useRef<number | null>(
      null,
    );

  const startedAtRef =
    useRef<number | null>(
      (() => {
        const saved =
          localStorage.getItem(
            STORAGE_STARTED_AT,
          );

        if (!saved) {
          return null;
        }

        const parsed =
          Number(saved);

        return Number.isFinite(
          parsed,
        )
          ? parsed
          : null;
      })(),
    );

  useEffect(() => {
    document.documentElement.dataset.theme =
      darkMode
        ? "dark"
        : "light";

    localStorage.setItem(
      "jobintel-theme",
      darkMode
        ? "dark"
        : "light",
    );
  }, [
    darkMode,
  ]);

  useEffect(() => {
    function handleCommandShortcut(
      event: KeyboardEvent,
    ) {
      const commandPressed =
        event.ctrlKey ||
        event.metaKey;

      if (
        commandPressed &&
        event.key.toLowerCase() ===
          "k"
      ) {
        event.preventDefault();

        setCommandPaletteOpen(
          (current) =>
            !current,
        );
      }
    }

    window.addEventListener(
      "keydown",
      handleCommandShortcut,
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleCommandShortcut,
      );
    };
  }, []);

  const clearStoredRun =
    useCallback(() => {
      localStorage.removeItem(
        STORAGE_WORKFLOW_ID,
      );

      localStorage.removeItem(
        STORAGE_STARTED_AT,
      );

      startedAtRef.current =
        null;
    }, []);

  const refreshApplicationData =
    useCallback(async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            "overview",
          ],
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "discover-rankings",
          ],
        }),
      ]);
    }, [
      queryClient,
    ]);

  const resolveFromHealth =
    useCallback(async () => {
      try {
        const health =
          await getPipelineHealth();

        const latest =
          health.latest_pipeline_run;

        if (!latest) {
          return false;
        }

        const workflowStartedAt =
          startedAtRef.current;

        if (
          workflowStartedAt ===
          null
        ) {
          return false;
        }

        const latestStartedAt =
          new Date(
            latest.started_at,
          ).getTime();

        if (
          !Number.isFinite(
            latestStartedAt,
          ) ||
          latestStartedAt <
            workflowStartedAt -
              10_000
        ) {
          return false;
        }

        if (
          latest.finished_at
        ) {
          if (
            latest.success
          ) {
            setRunState(
              "completed",
            );

            setProgressPercent(100);

            setStatusMessage(
              `Run ${latest.id} · ${latest.rankings_persisted} ranked`,
            );

            setWorkflowId(
              null,
            );

            clearStoredRun();

            await refreshApplicationData();

            return true;
          }

          setRunState(
            "failed",
          );

          setProgressPercent(null);

          setStatusMessage(
            latest.error_message ??
              `Run ${latest.id} failed`,
          );

          setWorkflowId(
            null,
          );

          clearStoredRun();

          return true;
        }

        setRunState(
          "running",
        );

        setStatusMessage(
          `Run ${latest.id} is active`,
        );

        return false;
      } catch {
        return false;
      }
    }, [
      clearStoredRun,
      refreshApplicationData,
    ]);

  const pollWorkflow =
    useCallback(async () => {
      if (!workflowId) {
        return;
      }

      const startedAt =
        startedAtRef.current;

      if (
        startedAt &&
        Date.now() -
          startedAt >
          MAX_RUNTIME_MS
      ) {
        const resolved =
          await resolveFromHealth();

        if (!resolved) {
          setRunState(
            "failed",
          );

          setProgressPercent(null);

          setStatusMessage(
            "Run status timed out",
          );

          setWorkflowId(
            null,
          );

          clearStoredRun();
        }

        return;
      }

      try {
        const response =
          await getWorkflowStatus(
            workflowId,
          );

        const nextState =
          normalizeWorkflowStatus(
            response.status,
          );

        if (
          nextState ===
          "completed"
        ) {
          setRunState(
            "completed",
          );

          setProgressPercent(100);

          setStatusMessage(
            "Intelligence updated",
          );

          setWorkflowId(
            null,
          );

          clearStoredRun();

          await refreshApplicationData();

          return;
        }

        if (
          nextState ===
          "failed"
        ) {
          setRunState(
            "failed",
          );

          setStatusMessage(
            response.error ??
              "Pipeline failed",
          );

          setWorkflowId(
            null,
          );

          clearStoredRun();

          return;
        }

        setRunState(
          "running",
        );

        setProgressPercent(
          response.progress?.percent ??
            null,
        );

        setStatusMessage(
          response.progress?.current_step ??
            "Temporal workflow active",
        );
      } catch {
        await resolveFromHealth();
      }
    }, [
      workflowId,
      clearStoredRun,
      refreshApplicationData,
      resolveFromHealth,
    ]);

  useEffect(() => {
    if (!workflowId) {
      return;
    }

    const initialPoll =
      window.setTimeout(
        () => {
          void pollWorkflow();
        },
        0,
      );

    pollingRef.current =
      window.setInterval(
        () => {
          void pollWorkflow();
        },
        POLL_INTERVAL_MS,
      );

    return () => {
      window.clearTimeout(
        initialPoll,
      );

      if (
        pollingRef.current !==
        null
      ) {
        window.clearInterval(
          pollingRef.current,
        );

        pollingRef.current =
          null;
      }
    };
  }, [
    workflowId,
    pollWorkflow,
  ]);

  useEffect(() => {
    function handleVisibility() {
      if (
        document.visibilityState ===
          "visible" &&
        workflowId
      ) {
        void pollWorkflow();
      }
    }

    window.addEventListener(
      "focus",
      handleVisibility,
    );

    document.addEventListener(
      "visibilitychange",
      handleVisibility,
    );

    return () => {
      window.removeEventListener(
        "focus",
        handleVisibility,
      );

      document.removeEventListener(
        "visibilitychange",
        handleVisibility,
      );
    };
  }, [
    workflowId,
    pollWorkflow,
  ]);

  const pipelineMutation =
    useMutation({
      mutationFn:
        startPipeline,

      onMutate: () => {
        setRunState(
          "starting",
        );

        setStatusMessage(
          "Starting workflow",
        );
      },

      onSuccess: (
        response,
      ) => {
        const startedAt =
          Date.now();

        setWorkflowId(
          response.workflow_id,
        );

        setRunState(
          "running",
        );

        setProgressPercent(0);

        setStatusMessage(
          "Starting pipeline",
        );

        startedAtRef.current =
          startedAt;

        localStorage.setItem(
          STORAGE_WORKFLOW_ID,
          response.workflow_id,
        );

        localStorage.setItem(
          STORAGE_STARTED_AT,
          String(
            startedAt,
          ),
        );
      },

      onError: () => {
        setRunState(
          "failed",
        );

        setProgressPercent(null);

        setStatusMessage(
          "Unable to start workflow",
        );

        clearStoredRun();
      },
    });

  const isRunning =
    runState ===
      "starting" ||
    runState ===
      "running" ||
    pipelineMutation.isPending;

  const runIntelligence =
    useCallback(() => {
      if (isRunning) {
        return;
      }

      pipelineMutation.mutate();
    }, [
      isRunning,
      pipelineMutation,
    ]);

  function renderRunButton() {
    if (
      runState ===
      "starting"
    ) {
      return (
        <>
          <LoaderCircle
            size={16}
            className="run-status-spinner"
          />
          Starting
        </>
      );
    }

    if (
      runState ===
      "running"
    ) {
      return (
        <>
          <span className="run-live-dot" />
          <span className="run-progress-label">
            Running
            {progressPercent !== null
              ? ` ${Math.round(progressPercent)}%`
              : ""}
          </span>

          <span
            className="run-progress-track"
            aria-hidden="true"
          >
            <span
              style={{
                width: `${Math.max(
                  3,
                  progressPercent ?? 3,
                )}%`,
              }}
            />
          </span>
        </>
      );
    }

    if (
      runState ===
      "completed"
    ) {
      return (
        <>
          <CheckCircle2
            size={16}
          />
          Completed
        </>
      );
    }

    if (
      runState ===
      "failed"
    ) {
      return (
        <>
          <AlertTriangle
            size={16}
          />
          Retry
        </>
      );
    }

    return (
      <>
        <Zap
          size={16}
          fill="currentColor"
        />
        Run Intelligence
      </>
    );
  }

  return (
    <>
      <header className="topbar">
        <button
          type="button"
          className="search-box command-trigger"
          onClick={() =>
            setCommandPaletteOpen(
              true,
            )
          }
          aria-label="Open command palette"
        >
          <Search
            size={17}
            aria-hidden="true"
          />

          <span className="command-trigger-label">
            Search jobs, companies, recruiters...
          </span>

          <span className="search-shortcut">
            <Command
              size={13}
              aria-hidden="true"
            />
            K
          </span>
        </button>

        <div className="topbar-actions">
          {statusMessage &&
            runState !==
              "idle" && (
              <div
                className={`run-status-caption run-status-caption-${runState}`}
              >
                {statusMessage}
              </div>
            )}

          <button
            type="button"
            className="icon-button"
            aria-label="Toggle theme"
            onClick={() =>
              setDarkMode(
                (current) =>
                  !current,
              )
            }
          >
            {darkMode ? (
              <Sun
                size={18}
                aria-hidden="true"
              />
            ) : (
              <Moon
                size={18}
                aria-hidden="true"
              />
            )}
          </button>

          <button
            type="button"
            className="icon-button"
            aria-label="Notifications"
          >
            <Bell
              size={18}
              aria-hidden="true"
            />
          </button>

          <button
            type="button"
            className={[
              "run-button",
              `run-button-${runState}`,
            ].join(" ")}
            disabled={
              isRunning
            }
            onClick={
              runIntelligence
            }
            title={
              statusMessage ??
              undefined
            }
          >
            {renderRunButton()}
          </button>
        </div>
      </header>

      <CommandPalette
        open={
          commandPaletteOpen
        }
        onOpenChange={
          setCommandPaletteOpen
        }
        onRunIntelligence={
          runIntelligence
        }
        runDisabled={
          isRunning
        }
      />
    </>
  );
}
