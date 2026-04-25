import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense, useMemo, useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const SensorsMap = lazy(() => import("@/components/SensorsMap"));
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Battery,
  Bell,
  CheckCircle2,
  ChevronRight,
  Clock,
  Cpu,
  Lock,
  MapPin,
  Moon,
  Shield,
  Sun,
  Wifi,
  Wrench,
  X,
} from "lucide-react";
import { useTheme } from "@/lib/theme";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import {
  initialSensors,
  type Sensor,
  type SensorCategory,
  type SensorUrgency,
} from "@/lib/sensors";

export const Route = createFileRoute("/sensors")({
  component: SensorsPage,
  head: () => ({
    meta: [
      { title: "Field Alerts — Sensor-SmAArt-City" },
      {
        name: "description",
        content:
          "Technician field app for Sensor-SmAArt-City: triage broken sensors, see locations and root cause, log resolutions.",
      },
    ],
  }),
});

const urgencyMeta: Record<
  SensorUrgency,
  { label: string; bar: string; dot: string; chip: string }
> = {
  critical: {
    label: "Critical",
    bar: "bg-[var(--critical)]",
    dot: "bg-[var(--critical)]",
    chip: "bg-[var(--critical-soft)] text-[var(--critical)]",
  },
  medium: {
    label: "Medium",
    bar: "bg-[var(--warning)]",
    dot: "bg-[var(--warning)]",
    chip: "bg-[var(--warning-soft)] text-[oklch(0.45_0.12_70)]",
  },
  low: {
    label: "Low",
    bar: "bg-[var(--info)]",
    dot: "bg-[var(--info)]",
    chip: "bg-[var(--info-soft)] text-[var(--info)]",
  },
};

const categoryMeta: Record<
  SensorCategory,
  { chip: string; Icon: typeof Cpu }
> = {
  Hardware: {
    chip: "bg-violet-50 text-violet-700",
    Icon: Cpu,
  },
  Battery: {
    chip: "bg-emerald-50 text-emerald-700",
    Icon: Battery,
  },
  Software: {
    chip: "bg-sky-50 text-sky-700",
    Icon: AlertCircle,
  },
  Connectivity: {
    chip: "bg-amber-50 text-amber-700",
    Icon: Wifi,
  },
  Environment: {
    chip: "bg-teal-50 text-teal-700",
    Icon: Activity,
  },
};

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="relative flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card transition-colors hover:bg-accent"
    >
      {isDark ? (
        <Sun className="h-4 w-4 text-muted-foreground" />
      ) : (
        <Moon className="h-4 w-4 text-muted-foreground" />
      )}
    </button>
  );
}

type StatusFilter = "all" | "critical" | "unstable";

function FilterPill({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`shrink-0 rounded-full px-3.5 py-1.5 text-xs font-semibold transition-colors ${
        active
          ? "bg-foreground text-background"
          : "border border-border bg-card text-muted-foreground hover:text-foreground"
      }`}
    >
      {label}
    </button>
  );
}

function SensorsPage() {
  const [sensors, setSensors] = useState<Sensor[]>(initialSensors);
  const [active, setActive] = useState<Sensor | null>(null);
  const [resolving, setResolving] = useState<Sensor | null>(null);
  const [comment, setComment] = useState("");
  const [lastResolved, setLastResolved] = useState<Sensor | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [districtFilter, setDistrictFilter] = useState<string>("all");

  const broken = useMemo(() => sensors.filter((s) => !s.resolvedAt), [sensors]);

  const districts = useMemo(
    () => Array.from(new Set(broken.map((s) => s.district))).sort(),
    [broken],
  );

  const sortedBroken = useMemo(() => {
    const order: Record<SensorUrgency, number> = {
      critical: 0,
      medium: 1,
      low: 2,
    };
    return [...broken].sort((a, b) => order[a.urgency] - order[b.urgency]);
  }, [broken]);

  const filteredBroken = useMemo(() => {
    return sortedBroken.filter((s) => {
      if (statusFilter === "critical" && s.urgency !== "critical") return false;
      if (statusFilter === "unstable" && s.status !== "Unstable") return false;
      if (districtFilter !== "all" && s.district !== districtFilter) return false;
      return true;
    });
  }, [sortedBroken, statusFilter, districtFilter]);

  const counts = {
    total: sortedBroken.length,
    critical: sortedBroken.filter((s) => s.urgency === "critical").length,
    unstable: sortedBroken.filter((s) => s.status === "Unstable").length,
    resolved: sensors.filter((s) => !!s.resolvedAt).length,
  };

  const openResolve = (s: Sensor) => {
    setActive(null);
    setResolving(s);
    setComment("");
  };

  const submitResolution = () => {
    if (!resolving) return;
    const trimmed = comment.trim();
    if (!trimmed) {
      toast.error("Please add a brief comment about the fix.");
      return;
    }
    const updated: Sensor = {
      ...resolving,
      resolutionComment: trimmed,
      resolvedAt: new Date().toLocaleString(),
    };
    setSensors((prev) => prev.map((s) => (s.id === resolving.id ? updated : s)));
    setResolving(null);
    setComment("");
    setLastResolved(updated);
    toast.success(`${updated.code} marked as resolved.`);
  };

  return (
    <div className="min-h-dvh bg-background text-foreground">
      <Toaster />

      {/* Branded header — mirrors the desktop sidebar identity */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-md items-center justify-between px-5 py-3.5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sky-100 text-sky-600">
              <Activity className="h-5 w-5" strokeWidth={2.5} />
            </div>
            <div className="leading-tight">
              <p className="text-sm font-bold">Sensor-SmAArt-City</p>
              <p className="text-[11px] text-muted-foreground">Field Technician</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <button
              className="relative flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4 text-muted-foreground" />
              {counts.critical > 0 && (
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[var(--critical)] ring-2 ring-background" />
              )}
            </button>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500 text-xs font-bold text-white">
              TB
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-md px-5 pb-24 pt-5">
        {/* Title */}
        <section className="mb-5">
          <p className="text-xs font-medium text-muted-foreground">Field Alerts</p>
          <h1 className="mt-0.5 font-display text-[28px] font-bold leading-tight">
            Broken sensors
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            System events assigned to you
          </p>
        </section>

        {/* Summary tiles — match the dashboard "Total / Unresolved / Critical / Resolved" row */}
        <section className="mb-6 grid grid-cols-2 gap-3">
          <SummaryTile label="Unresolved" value={counts.total} accent="text-foreground" />
          <SummaryTile
            label="Critical"
            value={counts.critical}
            accent="text-[var(--critical)]"
          />
          <SummaryTile
            label="Unstable"
            value={counts.unstable}
            accent="text-[oklch(0.50_0.12_70)]"
          />
          <SummaryTile
            label="Resolved (24h)"
            value={counts.resolved}
            accent="text-emerald-600"
          />
        </section>

        {/* Map of broken sensors in Aalen */}
        <div className="mb-4">
          <Suspense
            fallback={
              <div className="h-56 w-full animate-pulse rounded-2xl border border-border bg-muted" />
            }
          >
            <SensorsMap sensors={filteredBroken} onSelect={(s) => setActive(s)} />
          </Suspense>
          <p className="mt-1.5 text-[10px] text-muted-foreground">
            Map data © OpenStreetMap contributors
          </p>
        </div>

        {/* Status filter pills */}
        <div className="mb-3 flex items-center gap-2 overflow-x-auto pb-1">
          <FilterPill
            active={statusFilter === "all"}
            onClick={() => setStatusFilter("all")}
            label={`All (${counts.total})`}
          />
          <FilterPill
            active={statusFilter === "critical"}
            onClick={() => setStatusFilter("critical")}
            label={`Critical (${counts.critical})`}
          />
          <FilterPill
            active={statusFilter === "unstable"}
            onClick={() => setStatusFilter("unstable")}
            label={`Unstable (${counts.unstable})`}
          />
        </div>

        {/* Location filter (dropdown) */}
        <div className="mb-4 flex items-center gap-2">
          <MapPin className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <Select value={districtFilter} onValueChange={setDistrictFilter}>
            <SelectTrigger className="h-9 flex-1 rounded-full border-border bg-card text-xs font-semibold">
              <SelectValue placeholder="All districts" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All districts</SelectItem>
              {districts.map((d) => (
                <SelectItem key={d} value={d}>
                  {d}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Alert cards */}
        {filteredBroken.length === 0 ? (
          <div className="rounded-2xl border border-border bg-card p-8 text-center">
            <CheckCircle2 className="mx-auto mb-3 h-10 w-10 text-emerald-500" />
            <p className="font-display text-lg font-bold">No matching sensors</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Try clearing a filter to see more results.
            </p>
          </div>
        ) : (
          <ul className="space-y-3">
            {filteredBroken.map((s) => {
              const u = urgencyMeta[s.urgency];
              const c = categoryMeta[s.category];
              return (
                <li key={s.id}>
                  <button
                    onClick={() => setActive(s)}
                    className="group relative block w-full overflow-hidden rounded-2xl border border-border bg-card p-4 text-left shadow-sm transition-all hover:border-foreground/20 hover:shadow-md"
                  >
                    <span className={`absolute inset-y-0 left-0 w-1 ${u.bar}`} aria-hidden />

                    {/* Chip row */}
                    <div className="flex flex-wrap items-center gap-1.5 pl-2">
                      <Chip className={u.chip}>
                        <span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${u.dot}`} />
                        {u.label}
                      </Chip>
                      <Chip className={c.chip}>
                        <c.Icon className="mr-1 h-3 w-3" />
                        {s.category}
                      </Chip>
                      <Chip className="bg-sky-50 text-sky-700">
                        <Clock className="mr-1 h-3 w-3" />
                        {s.status}
                      </Chip>
                      <span className="ml-auto text-[11px] text-muted-foreground">
                        {s.reportedAt}
                      </span>
                    </div>

                    {/* Body */}
                    <div className="mt-2 pl-2">
                      <p className="font-display text-base font-bold leading-snug">
                        {s.name}
                      </p>
                      <p className="mt-0.5 text-sm text-foreground/80">{s.problem}</p>
                      <p className="mt-2 text-xs italic text-muted-foreground">
                        Why: {s.why}
                      </p>

                      <div className="mt-3 flex items-center justify-between gap-2 text-xs text-muted-foreground">
                        <span className="flex min-w-0 items-center gap-1">
                          <MapPin className="h-3.5 w-3.5 shrink-0" />
                          <span className="truncate">{s.location}</span>
                        </span>
                        <span className="font-mono text-[10px]">{s.code}</span>
                      </div>

                      <div className="mt-3 flex items-center gap-2">
                        <Button
                          size="sm"
                          className="h-8 rounded-md px-3 text-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            openResolve(s);
                          }}
                        >
                          <Wrench className="mr-1 h-3.5 w-3.5" />
                          Resolve
                        </Button>
                        <span className="ml-auto inline-flex items-center text-xs font-medium text-muted-foreground group-hover:text-foreground">
                          Details
                          <ChevronRight className="ml-0.5 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                        </span>
                      </div>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}

        {/* Recently resolved */}
        {sensors.some((s) => s.resolvedAt) && (
          <section className="mt-8">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Recently resolved
            </h3>
            <ul className="space-y-2">
              {sensors
                .filter((s) => s.resolvedAt)
                .slice(-4)
                .reverse()
                .map((s) => (
                  <li
                    key={s.id}
                    className="flex items-center gap-3 rounded-xl border border-border bg-card px-3 py-2.5"
                  >
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{s.name}</p>
                      <p className="truncate text-[11px] text-muted-foreground">
                        {s.code} · {s.resolvedAt}
                      </p>
                    </div>
                  </li>
                ))}
            </ul>
          </section>
        )}

        {/* Trust strip — mirrors the dashboard footer */}
        <footer className="mt-10 border-t border-border pt-4 text-[11px] text-muted-foreground">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="flex items-center gap-1">
              <Lock className="h-3 w-3" /> LoRaWAN AES-128 encrypted
            </span>
            <span aria-hidden>·</span>
            <span className="flex items-center gap-1">
              <Shield className="h-3 w-3" /> Role-based access
            </span>
          </div>
          <p className="mt-2">120 sensors across 6 districts</p>
        </footer>
      </main>

      {/* Detail dialog */}
      <Dialog open={!!active} onOpenChange={(o) => !o && setActive(null)}>
        <DialogContent className="max-w-md gap-0 p-0 sm:rounded-2xl">
          {active && (
            <>
              <div className="relative border-b border-border p-5">
                <span
                  className={`absolute inset-y-0 left-0 w-1 ${urgencyMeta[active.urgency].bar}`}
                  aria-hidden
                />
                <div className="flex items-start justify-between gap-3 pl-2">
                  <div className="min-w-0">
                    <div className="mb-2 flex flex-wrap items-center gap-1.5">
                      <Chip className={urgencyMeta[active.urgency].chip}>
                        {urgencyMeta[active.urgency].label}
                      </Chip>
                      <Chip className={categoryMeta[active.category].chip}>
                        {active.category}
                      </Chip>
                      <span className="font-mono text-[10px] text-muted-foreground">
                        {active.code}
                      </span>
                    </div>
                    <DialogHeader className="space-y-1 text-left">
                      <DialogTitle className="font-display text-xl">
                        {active.name}
                      </DialogTitle>
                      <DialogDescription className="flex items-center gap-1 text-xs">
                        <MapPin className="h-3 w-3" /> {active.location}
                      </DialogDescription>
                    </DialogHeader>
                  </div>
                  <button
                    onClick={() => setActive(null)}
                    className="rounded-md p-1 text-muted-foreground hover:bg-accent"
                    aria-label="Close"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="space-y-4 p-5">
                <Section label="Problem">
                  <p className="text-sm leading-relaxed">{active.problem}</p>
                </Section>
                <Section label="Why">
                  <p className="text-sm italic leading-relaxed text-muted-foreground">
                    {active.why}
                  </p>
                </Section>
                <Section label="Recommended action">
                  <p className="flex items-start gap-2 text-sm leading-relaxed">
                    <Wrench className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    {active.recommendedAction}
                  </p>
                </Section>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <InfoTile label="District" value={active.district} />
                  <InfoTile label="Reported" value={active.reportedAt} Icon={Clock} />
                </div>
              </div>

              <DialogFooter className="border-t border-border p-4">
                <Button
                  size="lg"
                  className="w-full gap-2 font-semibold"
                  onClick={() => openResolve(active)}
                >
                  <Wrench className="h-4 w-4" />
                  Resolve issue
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Resolve dialog */}
      <Dialog
        open={!!resolving}
        onOpenChange={(o) => {
          if (!o) {
            setResolving(null);
            setComment("");
          }
        }}
      >
        <DialogContent className="max-w-md sm:rounded-2xl">
          <DialogHeader>
            <DialogTitle className="font-display text-xl">Log resolution</DialogTitle>
            <DialogDescription>
              {resolving && (
                <span className="font-mono text-xs">
                  {resolving.code} · {resolving.location}
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <label
              htmlFor="comment"
              className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Fix comment
            </label>
            <Textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="e.g. Swapped battery pack, verified seal, sensor back online at 12:42."
              rows={5}
              autoFocus
            />
          </div>
          <DialogFooter className="gap-2 sm:gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setResolving(null);
                setComment("");
              }}
            >
              Cancel
            </Button>
            <Button onClick={submitResolution} className="gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Mark resolved
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirmation prompt — shows the comment that was added */}
      <Dialog
        open={!!lastResolved}
        onOpenChange={(o) => !o && setLastResolved(null)}
      >
        <DialogContent className="max-w-md sm:rounded-2xl">
          <div className="mx-auto -mt-2 mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
            <CheckCircle2 className="h-7 w-7 text-emerald-600" />
          </div>
          <DialogHeader className="text-center sm:text-center">
            <DialogTitle className="font-display text-xl">Sensor resolved</DialogTitle>
            <DialogDescription>
              {lastResolved && (
                <>
                  <span className="block font-medium text-foreground">
                    {lastResolved.name}
                  </span>
                  <span className="font-mono text-xs">
                    {lastResolved.code} · {lastResolved.resolvedAt}
                  </span>
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          {lastResolved?.resolutionComment && (
            <div className="rounded-xl border border-border bg-muted/40 p-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Your comment
              </p>
              <p className="text-sm italic leading-relaxed">
                “{lastResolved.resolutionComment}”
              </p>
            </div>
          )}
          <DialogFooter>
            <Button className="w-full" onClick={() => setLastResolved(null)}>
              Back to list
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Chip({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${className}`}
    >
      {children}
    </span>
  );
}

function SummaryTile({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`mt-1 font-display text-3xl font-bold leading-none ${accent}`}>
        {value}
      </p>
    </div>
  );
}

function Section({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      {children}
    </div>
  );
}

function InfoTile({
  label,
  value,
  Icon,
}: {
  label: string;
  value: string;
  Icon?: typeof Clock;
}) {
  return (
    <div className="rounded-xl border border-border bg-muted/40 p-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 flex items-center gap-1 text-sm font-medium">
        {Icon && <Icon className="h-3.5 w-3.5 text-muted-foreground" />}
        {value}
      </p>
    </div>
  );
}

// Suppress unused-import warning for icons referenced only via metadata maps.
void AlertTriangle;
