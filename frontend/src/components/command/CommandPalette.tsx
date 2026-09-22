import {
  BarChart3,
  Bot,
  BriefcaseBusiness,
  Building2,
  Command,
  Compass,
  MessageSquareText,
  Search,
  Settings,
  UserRound,
  X,
  Zap,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  useLocation,
  useNavigate,
} from "react-router-dom";

type CommandPaletteProps = {
  open: boolean;
  onOpenChange: (
    open: boolean,
  ) => void;
  onRunIntelligence: () => void;
  runDisabled?: boolean;
};

type PaletteCommand = {
  id: string;
  label: string;
  description: string;
  keywords: string;
  icon: typeof Search;
  path?: string;
  action?: () => void;
};

export function CommandPalette({
  open,
  onOpenChange,
  onRunIntelligence,
  runDisabled = false,
}: CommandPaletteProps) {
  const navigate =
    useNavigate();

  const location =
    useLocation();

  const inputRef =
    useRef<HTMLInputElement | null>(
      null,
    );

  const [
    query,
    setQuery,
  ] = useState("");

  const [
    selectedIndex,
    setSelectedIndex,
  ] = useState(0);

  const commands =
    useMemo<PaletteCommand[]>(
      () => [
        {
          id: "overview",
          label: "Overview",
          description:
            "Open your intelligence command center",
          keywords:
            "home dashboard command center metrics",
          icon: Command,
          path: "/overview",
        },
        {
          id: "discover",
          label: "Discover jobs",
          description:
            "Review ranked opportunities",
          keywords:
            "jobs rankings opportunities matches high confidence discovery stretch",
          icon: Compass,
          path: "/discover",
        },
        {
          id: "applications",
          label: "Applications",
          description:
            "Track application progress",
          keywords:
            "applications applied interview offer kanban",
          icon: BriefcaseBusiness,
          path: "/applications",
        },
        {
          id: "companies",
          label: "Companies",
          description:
            "Explore company intelligence",
          keywords:
            "companies employers organization intelligence",
          icon: Building2,
          path: "/companies",
        },
        {
          id: "outreach",
          label: "Outreach",
          description:
            "Manage recruiter and networking outreach",
          keywords:
            "recruiter outreach linkedin message email networking",
          icon: MessageSquareText,
          path: "/outreach",
        },
        {
          id: "profile",
          label: "Profile",
          description:
            "Manage your universal career profile",
          keywords:
            "profile resume skills roles experience candidate",
          icon: UserRound,
          path: "/profile",
        },
        {
          id: "analytics",
          label: "Analytics",
          description:
            "Review job-search performance",
          keywords:
            "analytics metrics performance conversion outcomes",
          icon: BarChart3,
          path: "/analytics",
        },
        {
          id: "automations",
          label: "Automations",
          description:
            "Manage intelligence workflows",
          keywords:
            "automation pipeline temporal schedule workflows",
          icon: Bot,
          path: "/automations",
        },
        {
          id: "settings",
          label: "Settings",
          description:
            "Configure Job Intelligence",
          keywords:
            "settings preferences configuration",
          icon: Settings,
          path: "/settings",
        },
        {
          id: "run-intelligence",
          label: "Run Intelligence",
          description:
            runDisabled
              ? "Intelligence pipeline is already running"
              : "Start a fresh discovery and ranking run",
          keywords:
            "run pipeline refresh jobs scan intelligence temporal",
          icon: Zap,
          action:
            onRunIntelligence,
        },
      ],
      [
        onRunIntelligence,
        runDisabled,
      ],
    );

  const filteredCommands =
    useMemo(() => {
      const normalized =
        query
          .trim()
          .toLowerCase();

      if (!normalized) {
        return commands;
      }

      return commands.filter(
        (command) => {
          const haystack = [
            command.label,
            command.description,
            command.keywords,
          ]
            .join(" ")
            .toLowerCase();

          return haystack.includes(
            normalized,
          );
        },
      );
    }, [
      commands,
      query,
    ]);

  const closePalette =
    useCallback(() => {
      setQuery("");
      setSelectedIndex(0);

      onOpenChange(
        false,
      );
    }, [
      onOpenChange,
    ]);

  const executeCommand =
    useCallback(
      (
        command: PaletteCommand,
      ) => {
        if (
          command.id ===
            "run-intelligence" &&
          runDisabled
        ) {
          return;
        }

        if (command.path) {
          if (
            location.pathname !==
            command.path
          ) {
            navigate(
              command.path,
            );
          }

          closePalette();

          return;
        }

        command.action?.();

        closePalette();
      },
      [
        closePalette,
        location.pathname,
        navigate,
        runDisabled,
      ],
    );

  useEffect(() => {
    if (!open) {
      return;
    }

    const focusTimer =
      window.setTimeout(
        () => {
          inputRef.current?.focus();
        },
        0,
      );

    return () => {
      window.clearTimeout(
        focusTimer,
      );
    };
  }, [
    open,
  ]);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (
        event.key ===
        "Escape"
      ) {
        event.preventDefault();

        closePalette();

        return;
      }

      if (
        event.key ===
        "ArrowDown"
      ) {
        event.preventDefault();

        setSelectedIndex(
          (current) =>
            filteredCommands.length
              ? (
                  current +
                  1
                ) %
                filteredCommands.length
              : 0,
        );

        return;
      }

      if (
        event.key ===
        "ArrowUp"
      ) {
        event.preventDefault();

        setSelectedIndex(
          (current) =>
            filteredCommands.length
              ? (
                  current -
                  1 +
                  filteredCommands.length
                ) %
                filteredCommands.length
              : 0,
        );

        return;
      }

      if (
        event.key ===
        "Enter"
      ) {
        event.preventDefault();

        const command =
          filteredCommands[
            selectedIndex
          ];

        if (command) {
          executeCommand(
            command,
          );
        }
      }
    }

    window.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [
    open,
    closePalette,
    executeCommand,
    filteredCommands,
    selectedIndex,
  ]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="command-palette-backdrop"
      role="presentation"
      onMouseDown={(
        event,
      ) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          closePalette();
        }
      }}
    >
      <section
        className="command-palette"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
      >
        <div className="command-palette-search">
          <Search
            size={18}
            aria-hidden="true"
          />

          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(
              event,
            ) => {
              setQuery(
                event.target.value,
              );

              setSelectedIndex(
                0,
              );
            }}
            placeholder="Search commands..."
            aria-label="Search commands"
          />

          <button
            type="button"
            className="command-close"
            onClick={
              closePalette
            }
            aria-label="Close command palette"
          >
            <X
              size={16}
              aria-hidden="true"
            />
          </button>
        </div>

        <div className="command-palette-body">
          <div className="command-section-label">
            Commands
          </div>

          {filteredCommands.length ? (
            <div
              className="command-list"
              role="listbox"
            >
              {filteredCommands.map(
                (
                  command,
                  index,
                ) => {
                  const Icon =
                    command.icon;

                  const disabled =
                    command.id ===
                      "run-intelligence" &&
                    runDisabled;

                  return (
                    <button
                      key={
                        command.id
                      }
                      type="button"
                      className={[
                        "command-item",
                        index ===
                        selectedIndex
                          ? "command-item-selected"
                          : "",
                      ]
                        .filter(
                          Boolean,
                        )
                        .join(" ")}
                      disabled={
                        disabled
                      }
                      role="option"
                      aria-selected={
                        index ===
                        selectedIndex
                      }
                      onMouseEnter={() =>
                        setSelectedIndex(
                          index,
                        )
                      }
                      onClick={() =>
                        executeCommand(
                          command,
                        )
                      }
                    >
                      <span className="command-item-icon">
                        <Icon
                          size={17}
                          aria-hidden="true"
                        />
                      </span>

                      <span className="command-item-copy">
                        <strong>
                          {
                            command.label
                          }
                        </strong>

                        <span>
                          {
                            command.description
                          }
                        </span>
                      </span>

                      {index ===
                        selectedIndex && (
                        <span className="command-enter">
                          Enter
                        </span>
                      )}
                    </button>
                  );
                },
              )}
            </div>
          ) : (
            <div className="command-empty">
              No matching commands
            </div>
          )}
        </div>

        <footer className="command-palette-footer">
          <span>
            ↑↓ Navigate
          </span>

          <span>
            Enter Select
          </span>

          <span>
            Esc Close
          </span>
        </footer>
      </section>
    </div>
  );
}
