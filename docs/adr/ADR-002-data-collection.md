# ADR-002: Data Collection Architecture

**Status**: Accepted  
**Date**: 2026-04-02  
**Deciders**: Architecture Team  
**Supersedes**: ADR-001 (Measurement Strategy - refines scope)

---

## Context

Tracera requires a comprehensive data collection architecture to gather, store, and analyze Python tooling performance metrics across diverse environments. The system must handle:

- High-frequency metric sampling from multiple concurrent tool executions
- Privacy-preserving data handling for user codebases
- Efficient storage of time-series performance data
- Real-time and batch analysis pipelines

The collection architecture must balance completeness (capturing all relevant metrics) with minimal overhead to avoid distorting the very measurements it captures.

---

## Decision Drivers

| Driver | Priority | Description |
|--------|----------|-------------|
| **Accuracy** | P0 | Measurement overhead must not exceed 2% of baseline execution time |
| **Privacy** | P0 | User source code must never leave the local environment |
| **Completeness** | P1 | Capture time, memory, CPU, I/O, and network metrics |
| **Scalability** | P1 | Support 1000+ concurrent benchmark runs |
| **Reliability** | P1 | Zero data loss for completed benchmark runs |
| **Latency** | P2 | Analysis results available within 5 seconds of run completion |

---

## Considered Options

### Option A: In-Process Collection (REJECTED)

Embed measurement code directly within each tool's execution context via monkey-patching or import hooks.

```
┌─────────────────────────────────────────────────────────────┐
│                    In-Process Collector                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │
│  │   ruff      │    │    uv       │    │     mypy        │   │
│  │  (patched)  │    │  (patched)  │    │   (patched)     │   │
│  └──────┬──────┘    └──────┬──────┘    └────────┬────────┘   │
│         │                  │                    │            │
│         └──────────────────┼────────────────────┘            │
│                            ▼                                 │
│              ┌─────────────────────────┐                      │
│              │   Instrumentation Layer │                      │
│              │  (monkey-patched hooks) │                      │
│              └───────────┬─────────────┘                      │
│                          ▼                                   │
│              ┌─────────────────────────┐                      │
│              │   Metrics Buffer        │                      │
│              └───────────┬─────────────┘                      │
│                          ▼                                   │
│              ┌─────────────────────────┐                      │
│              │   Local SQLite Store    │                      │
│              └─────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

**Pros**:
- Minimal context switching overhead
- Direct access to internal tool state
- Fine-grained metric granularity

**Cons**:
- Requires per-tool patching
- Breaks when tool internals change
- Modifies tool behavior (observer effect)
- Complex maintenance burden

### Option B: External Process Monitoring (REJECTED)

Use dedicated monitoring processes that attach to tool processes via OS APIs (ptrace, dtrace, ETW).

```
┌─────────────────────────────────────────────────────────────┐
│                 External Process Monitor                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  ruff    │    │    uv    │    │   mypy   │  Tool         │
│   │ (PID:1)  │    │ (PID:2)  │    │ (PID:3)  │  Processes    │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘             │
│        │               │               │                     │
│        └───────────────┼───────────────┘                     │
│                        ▼                                     │
│   ┌─────────────────────────────────────────┐              │
│   │       OS Kernel (ptrace/procfs)         │              │
│   │  • /proc/[pid]/status                   │              │
│   │  • ptrace(PTRACE_SYSCALL)               │              │
│   │  • dtrace probes                        │              │
│   └─────────────────┬───────────────────────┘              │
│                     ▼                                        │
│   ┌─────────────────────────────────────────┐              │
│   │     External Monitor Daemon           │              │
│   │  • Sample every 10ms                    │              │
│   │  • Aggregate metrics                    │              │
│   │  • Stream to collector                  │              │
│   └─────────────────┬───────────────────────┘              │
│                     ▼                                        │
│   ┌─────────────────────────────────────────┐              │
│   │         Local Collector               │              │
│   └─────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

**Pros**:
- No tool modification required
- Captures true OS-level metrics
- Works with any binary

**Cons**:
- Platform-specific implementation (Linux/macOS/Windows)
- High overhead from frequent syscalls
- Requires elevated privileges (ptrace)
- Complex signal handling for process lifecycle

### Option C: Hybrid Sidecar Architecture (ACCEPTED)

Combine lightweight in-process instrumentation with external process monitoring for system-level metrics.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                        Hybrid Data Collection Architecture                      │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                         Benchmark Runner                                 │  │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐  │  │
│  │  │  Warmup Phase   │→│ Measurement Loop │→│   Result Aggregation    │  │  │
│  │  └─────────────────┘  └──────────────────┘  └─────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│                                    ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                     Tool Execution Sandbox                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐   │   │  │
│  │  │  │  ruff   │  │   uv    │  │  mypy   │  │  pyright        │   │   │  │
│  │  │  │(wrapped)│  │(wrapped)│  │(wrapped)│  │ (wrapped)       │   │   │  │
│  │  │  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘   │   │  │
│  │  │       └─────────────┴───────────┴────────────────┘             │   │  │
│  │  │                         │                                      │   │  │
│  │  │              ┌────────────┴────────────┐                       │   │  │
│  │  │              │  Lightweight Wrapper   │  (timing, exit code)  │   │  │
│  │  │              │  (shell/entry point)   │                       │   │  │
│  │  │              └─────────────────────────┘                       │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  │                                   │                                    │  │
│  │              ┌────────────────────┼────────────────────┐               │  │
│  │              │                    │                    │               │  │
│  │              ▼                    ▼                    ▼               │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │  │
│  │  │ Resource Monitor│  │  System Profiler  │  │  Output Parser    │      │  │
│  │  │  (psutil-based) │  │ (perf/dtrace/ETW) │  │ (structured logs)│      │  │
│  │  │                 │  │                 │  │                   │      │  │
│  │  │ • Memory RSS    │  │ • CPU cycles    │  │ • Parse JSON/XML  │      │  │
│  │  │ • CPU percent   │  │ • Cache misses  │  │ • Extract metrics │      │  │
│  │  │ • File handles  │  │ • Branch mispr  │  │ • Error counts    │      │  │
│  │  │ • Thread count  │  │ • IPC           │  │                   │      │  │
│  │  └────────┬────────┘  └────────┬────────┘  └─────────┬───────────┘      │  │
│  │           │                    │                    │                  │  │
│  │           └────────────────────┼────────────────────┘                  │  │
│  │                                ▼                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │  │              Metrics Aggregation Buffer                          │   │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │  │
│  │  │  │ Time Series │  │  Histograms │  │   Percentile Sketches   │  │   │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │   │  │
│  │  └─────────────────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│                                    ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                       Data Pipeline Layer                                  │  │
│  │                                                                          │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    Privacy Filter                                    │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │  │  │
│  │  │  │ Path Sanitizer │  │ Code Redactor│  │  Stack Trace Anonymizer│ │  │  │
│  │  │  └──────────────┘  └──────────────┘  └────────────────────────┘ │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                    │                                     │  │
│  │                                    ▼                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    Local Storage                                     │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │  │  │
│  │  │  │ Time-Series  │  │ Benchmark    │  │    Analysis Cache      │ │  │  │
│  │  │  │ DB (SQLite)  │  │ Registry     │  │    (query results)     │ │  │  │
│  │  │  └──────────────┘  └──────────────┘  └────────────────────────┘ │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                    │                                     │  │
│  │                    ┌───────────────┴───────────────┐                     │  │
│  │                    │                               │                     │  │
│  │                    ▼                               ▼                     │  │
│  │  ┌──────────────────────────┐  ┌──────────────────────────┐             │  │
│  │  │   Real-time Analysis   │  │   Batch Analysis          │             │  │
│  │  │   Stream Processor     │  │   Scheduled Jobs            │             │  │
│  │  │                        │  │                           │             │  │
│  │  │ • Anomaly detection    │  │ • Trend analysis          │             │  │
│  │  │ • Regression alerts    │  │ • Baseline updates        │             │  │
│  │  │ • Live dashboard       │  │ • Report generation       │             │  │
│  │  └──────────────────────────┘  └──────────────────────────┘             │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Decision Outcome

**Chosen**: Option C - Hybrid Sidecar Architecture

### Core Components

#### 1. Benchmark Runner (`BenchmarkRunner`)

```rust
pub struct BenchmarkRunner {
    config: BenchmarkConfig,
    resource_monitor: ResourceMonitor,
    system_profiler: Option<SystemProfiler>,
    privacy_filter: PrivacyFilter,
    storage: Arc<dyn MetricStorage>,
}

pub struct BenchmarkConfig {
    /// Target tool configuration
    pub tool: ToolSpec,
    /// Target codebase or synthetic benchmark
    pub target: BenchmarkTarget,
    /// Number of warmup runs (not measured)
    pub warmup_count: u32,
    /// Number of measurement runs
    pub measurement_count: u32,
    /// Minimum total measurement time
    pub min_runtime_seconds: f64,
    /// Cache clearing command between runs
    pub prepare: Option<String>,
    /// Whether to collect system-level metrics (perf/dtrace)
    pub enable_system_profiler: bool,
    /// Privacy level for data collection
    pub privacy_level: PrivacyLevel,
}

pub enum PrivacyLevel {
    /// Full anonymization - no paths, no content
    Strict,
    /// Project-relative paths only
    Standard,
    /// Full paths with user consent
    Debug,
}

impl BenchmarkRunner {
    pub async fn run(&self) -> Result<BenchmarkReport> {
        // Phase 1: Warmup
        for i in 0..self.config.warmup_count {
            self.execute_warmup(i).await?;
        }

        // Phase 2: Measurement with resource monitoring
        let mut measurements = Vec::new();
        let monitor = self.resource_monitor.start().await?;
        
        for i in 0..self.config.measurement_count {
            if let Some(ref prepare) = self.config.prepare {
                self.run_prepare_command(prepare).await?;
            }
            
            let measurement = self.execute_measurement(i).await?;
            measurements.push(measurement);
        }
        
        let resource_summary = monitor.stop().await?;
        
        // Phase 3: System profiling (optional)
        let system_metrics = if self.config.enable_system_profiler {
            self.system_profiler.as_ref()
                .map(|p| p.collect_summary())
                .transpose()?
        } else {
            None
        };
        
        // Phase 4: Privacy filtering
        let filtered_measurements = self.privacy_filter
            .sanitize(measurements)
            .await?;
        
        // Phase 5: Storage and analysis
        let report = self.generate_report(
            filtered_measurements,
            resource_summary,
            system_metrics,
        ).await?;
        
        self.storage.store(&report).await?;
        
        Ok(report)
    }
}
```

#### 2. Resource Monitor (`ResourceMonitor`)

```rust
use psutil::process::Process;
use tokio::time::{interval, Duration};

pub struct ResourceMonitor {
    sample_interval_ms: u64,
    process_tracker: ProcessTracker,
}

pub struct ProcessTracker {
    root_pid: u32,
    child_pids: Arc<RwLock<Vec<u32>>>,
}

impl ResourceMonitor {
    pub async fn start(&self) -> Result<RunningMonitor> {
        let (tx, rx) = mpsc::channel(1000);
        let tracker = self.process_tracker.clone();
        let interval_ms = self.sample_interval_ms;
        
        let handle = tokio::spawn(async move {
            let mut ticker = interval(Duration::from_millis(interval_ms));
            
            loop {
                ticker.tick().await;
                
                // Sample all tracked processes
                let pids = tracker.get_all_pids().await;
                let mut sample = ResourceSample {
                    timestamp: Instant::now(),
                    processes: Vec::new(),
                };
                
                for pid in pids {
                    if let Ok(proc) = Process::new(pid) {
                        let mem = proc.memory_info()?;
                        let cpu = proc.cpu_percent()?;
                        
                        sample.processes.push(ProcessMetrics {
                            pid,
                            memory_rss_mb: mem.rss() as f64 / 1024.0 / 1024.0,
                            memory_vms_mb: mem.vms() as f64 / 1024.0 / 1024.0,
                            cpu_percent: cpu,
                            num_threads: proc.num_threads()? as u32,
                            open_files: proc.open_files()?.len() as u32,
                        });
                    }
                }
                
                if tx.send(sample).await.is_err() {
                    break; // Receiver dropped
                }
            }
            
            Ok::<(), Error>(())
        });
        
        Ok(RunningMonitor {
            receiver: rx,
            handle,
            samples: Vec::new(),
        })
    }
}

pub struct RunningMonitor {
    receiver: mpsc::Receiver<ResourceSample>,
    handle: JoinHandle<Result<()>>,
    samples: Vec<ResourceSample>,
}

impl RunningMonitor {
    pub async fn sample(&mut self) -> Result<Option<ResourceSample>> {
        match timeout(Duration::from_millis(5), self.receiver.recv()).await {
            Ok(Some(sample)) => {
                self.samples.push(sample.clone());
                Ok(Some(sample))
            }
            _ => Ok(None), // No sample available (non-blocking)
        }
    }
    
    pub async fn stop(mut self) -> Result<ResourceSummary> {
        drop(self.receiver); // Signal shutdown
        self.handle.await??;
        
        // Aggregate samples
        let total_samples = self.samples.len();
        let memory_peak = self.samples.iter()
            .map(|s| s.total_memory_rss())
            .fold(0.0, f64::max);
        
        let memory_avg = self.samples.iter()
            .map(|s| s.total_memory_rss())
            .sum::<f64>() / total_samples as f64;
        
        let cpu_avg = self.samples.iter()
            .map(|s| s.total_cpu_percent())
            .sum::<f64>() / total_samples as f64;
        
        Ok(ResourceSummary {
            total_samples,
            memory_peak_mb: memory_peak,
            memory_avg_mb: memory_avg,
            cpu_percent_avg: cpu_avg,
            duration: self.total_duration(),
        })
    }
}
```

#### 3. System Profiler (`SystemProfiler`)

```rust
#[cfg(target_os = "linux")]
pub struct LinuxProfiler {
    perf_available: bool,
    events: Vec<PerfEvent>,
}

#[cfg(target_os = "macos")]
pub struct MacOSProfiler {
    dtrace_available: bool,
    script_path: PathBuf,
}

pub enum SystemProfiler {
    #[cfg(target_os = "linux")]
    Linux(LinuxProfiler),
    #[cfg(target_os = "macos")]
    MacOS(MacOSProfiler),
    #[cfg(target_os = "windows")]
    Windows(WindowsProfiler),
    Null, // Profiling disabled
}

impl SystemProfiler {
    pub async fn collect_summary(&self) -> Result<SystemMetrics> {
        match self {
            #[cfg(target_os = "linux")]
            Self::Linux(profiler) => profiler.collect().await,
            #[cfg(target_os = "macos")]
            Self::MacOS(profiler) => profiler.collect().await,
            _ => Ok(SystemMetrics::default()),
        }
    }
}

#[cfg(target_os = "linux")]
impl LinuxProfiler {
    pub async fn collect(&self) -> Result<SystemMetrics> {
        if !self.perf_available {
            return Ok(SystemMetrics::default());
        }
        
        // Parse perf stat output
        let output = Command::new("perf")
            .args(&[
                "stat",
                "-e", "cycles,instructions,cache-references,cache-misses,branches,branch-misses",
                "--",
                "sleep", "0.1"
            ])
            .stderr(Stdio::piped())
            .output()
            .await?;
        
        let stderr = String::from_utf8_lossy(&output.stderr);
        
        Ok(SystemMetrics {
            cpu_cycles: Self::parse_perf_value(&stderr, "cycles"),
            instructions: Self::parse_perf_value(&stderr, "instructions"),
            cache_references: Self::parse_perf_value(&stderr, "cache-references"),
            cache_misses: Self::parse_perf_value(&stderr, "cache-misses"),
            branch_instructions: Self::parse_perf_value(&stderr, "branches"),
            branch_misses: Self::parse_perf_value(&stderr, "branch-misses"),
        })
    }
}
```

#### 4. Privacy Filter (`PrivacyFilter`)

```rust
pub struct PrivacyFilter {
    level: PrivacyLevel,
    project_root: Option<PathBuf>,
    redaction_patterns: Vec<Regex>,
}

impl PrivacyFilter {
    pub fn new(level: PrivacyLevel, project_root: Option<PathBuf>) -> Self {
        let redaction_patterns = vec![
            Regex::new(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}").unwrap(), // Emails
            Regex::new(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}").unwrap(), // UUIDs
            Regex::new(r"sk-[a-zA-Z0-9]{48}").unwrap(), // API keys (OpenAI format)
        ];
        
        Self {
            level,
            project_root,
            redaction_patterns,
        }
    }
    
    pub async fn sanitize(&self, measurements: Vec<Measurement>) -> Result<Vec<SanitizedMeasurement>> {
        measurements.into_iter()
            .map(|m| self.sanitize_measurement(m))
            .collect()
    }
    
    fn sanitize_measurement(&self, m: Measurement) -> Result<SanitizedMeasurement> {
        let sanitized_paths = m.file_paths
            .into_iter()
            .map(|p| self.sanitize_path(p))
            .collect();
        
        let sanitized_output = self.redact_sensitive_content(m.output);
        let sanitized_errors = self.redact_sensitive_content(m.errors);
        
        Ok(SanitizedMeasurement {
            tool_name: m.tool_name,
            version: m.version,
            duration_ms: m.duration_ms,
            memory_peak_mb: m.memory_peak_mb,
            file_paths: sanitized_paths,
            output: sanitized_output,
            errors: sanitized_errors,
            metric_fingerprint: self.compute_fingerprint(&m),
        })
    }
    
    fn sanitize_path(&self, path: PathBuf) -> SanitizedPath {
        match self.level {
            PrivacyLevel::Strict => {
                // Replace with hash of relative path
                let hash = blake3::hash(path.to_string_lossy().as_bytes());
                SanitizedPath::Anonymized(format!("file_{:.16}", hash.to_hex()))
            }
            PrivacyLevel::Standard => {
                // Project-relative path
                if let Some(ref root) = self.project_root {
                    if let Ok(rel) = path.strip_prefix(root) {
                        return SanitizedPath::Relative(rel.to_path_buf());
                    }
                }
                SanitizedPath::FileName(path.file_name()
                    .map(|n| n.to_string_lossy().to_string())
                    .unwrap_or_else(|| "unknown".to_string()))
            }
            PrivacyLevel::Debug => {
                SanitizedPath::Full(path)
            }
        }
    }
    
    fn redact_sensitive_content(&self, content: String) -> String {
        let mut result = content;
        for pattern in &self.redaction_patterns {
            result = pattern.replace_all(&result, "[REDACTED]").to_string();
        }
        result
    }
    
    fn compute_fingerprint(&self, m: &Measurement) -> String {
        // Deterministic fingerprint for duplicate detection
        let data = format!("{}:{}:{}", m.tool_name, m.version, m.duration_ms);
        blake3::hash(data.as_bytes()).to_hex().to_string()
    }
}
```

#### 5. Storage Layer (`MetricStorage`)

```rust
#[async_trait]
pub trait MetricStorage: Send + Sync {
    async fn store(&self, report: &BenchmarkReport) -> Result<()>;
    async fn query(&self, filter: QueryFilter) -> Result<Vec<BenchmarkReport>>;
    async fn aggregate(&self, spec: AggregationSpec) -> Result<AggregationResult>;
}

pub struct SQLiteStorage {
    pool: SqlitePool,
}

impl SQLiteStorage {
    pub async fn new(path: &Path) -> Result<Self> {
        let pool = SqlitePool::connect_with(
            SqliteConnectOptions::new()
                .filename(path)
                .create_if_missing(true)
                .journal_mode(SqliteJournalMode::Wal)
                .synchronous(SqliteSynchronous::Normal)
        ).await?;
        
        // Initialize schema
        sqlx::query(include_str!("../sql/schema.sql"))
            .execute(&pool)
            .await?;
        
        Ok(Self { pool })
    }
}

#[async_trait]
impl MetricStorage for SQLiteStorage {
    async fn store(&self, report: &BenchmarkReport) -> Result<()> {
        let mut tx = self.pool.begin().await?;
        
        // Store benchmark metadata
        let benchmark_id = sqlx::query(
            r#"
            INSERT INTO benchmarks (tool_name, tool_version, target_id, started_at, completed_at)
            VALUES (?1, ?2, ?3, ?4, ?5)
            RETURNING id
            "#
        )
        .bind(&report.tool_name)
        .bind(&report.tool_version)
        .bind(&report.target_id)
        .bind(report.started_at)
        .bind(report.completed_at)
        .fetch_one(&mut *tx)
        .await?
        .get::<i64, _>("id");
        
        // Store time-series samples
        for sample in &report.time_series {
            sqlx::query(
                r#"
                INSERT INTO time_series (benchmark_id, timestamp_ms, memory_mb, cpu_percent)
                VALUES (?1, ?2, ?3, ?4)
                "#
            )
            .bind(benchmark_id)
            .bind(sample.timestamp_ms)
            .bind(sample.memory_mb)
            .bind(sample.cpu_percent)
            .execute(&mut *tx)
            .await?;
        }
        
        // Store aggregated statistics
        sqlx::query(
            r#"
            INSERT INTO statistics (
                benchmark_id, duration_ms_mean, duration_ms_p50, duration_ms_p95, duration_ms_p99,
                memory_mb_peak, memory_mb_avg, cpu_percent_avg
            )
            VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
            "#
        )
        .bind(benchmark_id)
        .bind(report.stats.duration_ms.mean)
        .bind(report.stats.duration_ms.p50)
        .bind(report.stats.duration_ms.p95)
        .bind(report.stats.duration_ms.p99)
        .bind(report.stats.memory_mb.peak)
        .bind(report.stats.memory_mb.average)
        .bind(report.stats.cpu_percent.average)
        .execute(&mut *tx)
        .await?;
        
        tx.commit().await?;
        Ok(())
    }
}
```

#### 6. Analysis Pipeline

```rust
pub struct AnalysisPipeline {
    real_time_processor: RealTimeProcessor,
    batch_processor: BatchProcessor,
    storage: Arc<dyn MetricStorage>,
}

pub struct RealTimeProcessor {
    anomaly_detector: AnomalyDetector,
    regression_checker: RegressionChecker,
    alert_handlers: Vec<Box<dyn AlertHandler>>,
}

impl RealTimeProcessor {
    pub async fn process(&self, report: &BenchmarkReport) -> Result<()> {
        // Anomaly detection
        if let Some(anomaly) = self.anomaly_detector.check(report).await? {
            self.send_alert(Alert::Anomaly {
                benchmark_id: report.id.clone(),
                severity: anomaly.severity,
                description: anomaly.description,
            }).await?;
        }
        
        // Regression detection against baseline
        if let Some(regression) = self.regression_checker.check(report).await? {
            self.send_alert(Alert::Regression {
                benchmark_id: report.id.clone(),
                metric: regression.metric,
                baseline_value: regression.baseline,
                current_value: regression.current,
                delta_percent: regression.delta_percent,
            }).await?;
        }
        
        Ok(())
    }
}

pub struct BatchProcessor {
    trend_analyzer: TrendAnalyzer,
    baseline_updater: BaselineUpdater,
    report_generator: ReportGenerator,
}

impl BatchProcessor {
    pub async fn run_daily(&self) -> Result<()> {
        // Trend analysis
        let trends = self.trend_analyzer.analyze(
            Utc::now() - Duration::days(30),
            Utc::now()
        ).await?;
        
        // Update rolling baselines
        self.baseline_updater.update(trends).await?;
        
        // Generate summary reports
        let report = self.report_generator.generate(trends).await?;
        self.report_generator.publish(report).await?;
        
        Ok(())
    }
}
```

---

## Privacy Considerations

### Data Classification

| Category | Collected | Storage | Notes |
|----------|-----------|---------|-------|
| **Tool name** | ✓ | Local | ruff, uv, mypy, etc. |
| **Tool version** | ✓ | Local | Semantic version |
| **Timing metrics** | ✓ | Local | Wall time, CPU time |
| **Memory metrics** | ✓ | Local | RSS, VMS, peak |
| **Error counts** | ✓ | Local | Number of errors/warnings |
| **File paths** | Optional | Local | Sanitized per privacy level |
| **Source code** | ✗ | — | **Never collected** |
| **Full error messages** | Optional | Local | Redacted in strict mode |

### Privacy Levels

```rust
/// PrivacyLevel determines how aggressively data is sanitized.
pub enum PrivacyLevel {
    /// Strict: No identifying information
    /// - File paths → hashed (file_a1b2c3d4)
    /// - Error messages → count only (42 errors)
    /// - Output content → not stored
    Strict,
    
    /// Standard: Project-relative information
    /// - File paths → project-relative (src/main.py)
    /// - Error messages → redacted sensitive content
    /// - Output content → metrics only
    Standard,
    
    /// Debug: Full information (user opt-in)
    /// - File paths → full paths
    /// - Error messages → full content
    /// - Output content → stored for analysis
    Debug,
}
```

---

## Storage Strategy

### Database Schema

```sql
-- Benchmark runs table
CREATE TABLE benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    tool_version TEXT NOT NULL,
    target_id TEXT NOT NULL,  -- Synthetic benchmark or project hash
    privacy_level TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    status TEXT NOT NULL,  -- 'completed', 'failed', 'timeout'
    fingerprint TEXT UNIQUE,  -- For deduplication
    
    -- Aggregated metrics
    duration_ms_mean REAL,
    duration_ms_p50 REAL,
    duration_ms_p95 REAL,
    duration_ms_p99 REAL,
    duration_ms_stddev REAL,
    memory_mb_peak REAL,
    memory_mb_avg REAL,
    cpu_percent_avg REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Time-series samples (one row per measurement interval)
CREATE TABLE time_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benchmark_id INTEGER NOT NULL,
    timestamp_ms INTEGER NOT NULL,  -- Relative to benchmark start
    memory_mb REAL NOT NULL,
    cpu_percent REAL NOT NULL,
    num_threads INTEGER,
    open_files INTEGER,
    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id) ON DELETE CASCADE
);

-- File path references (sanitized)
CREATE TABLE file_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benchmark_id INTEGER NOT NULL,
    sanitized_path TEXT NOT NULL,  -- May be hash or relative path
    file_type TEXT,  -- 'python', 'markdown', 'toml', etc.
    line_count INTEGER,
    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id) ON DELETE CASCADE
);

-- Error/warning tallies (not full messages)
CREATE TABLE diagnostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benchmark_id INTEGER NOT NULL,
    severity TEXT NOT NULL,  -- 'error', 'warning', 'note'
    category TEXT,  -- 'syntax', 'type', 'lint', etc.
    count INTEGER NOT NULL,
    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id) ON DELETE CASCADE
);

-- Baselines for regression detection
CREATE TABLE baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    tool_version TEXT NOT NULL,
    target_type TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value_mean REAL NOT NULL,
    value_stddev REAL NOT NULL,
    sample_count INTEGER NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_name, tool_version, target_type, metric_name)
);

-- Indexes for common queries
CREATE INDEX idx_benchmarks_tool ON benchmarks(tool_name, tool_version);
CREATE INDEX idx_benchmarks_target ON benchmarks(target_id);
CREATE INDEX idx_benchmarks_time ON benchmarks(created_at);
CREATE INDEX idx_time_series_benchmark ON time_series(benchmark_id);
```

### Retention Policy

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| Raw time-series | 30 days | Space-efficient aggregation after analysis |
| Aggregated stats | 1 year | Long-term trend analysis |
| Baselines | Indefinite | Required for regression detection |
| Failed runs | 7 days | Debugging window |

---

## Analysis Pipeline

### Real-time Stream

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Benchmark       │────▶│  Ingestion       │────▶│  Anomaly        │
│ Completed       │     │  Buffer          │     │  Detection      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                         │
                              ┌──────────────────────────┼──────────┐
                              │                          │          │
                              ▼                          ▼          ▼
                    ┌─────────────────┐       ┌─────────────────┐ ┌──────────────┐
                    │ Regression      │       │ Alert Router    │ │ Dashboard    │
                    │ Detection       │       │                 │ │ Update       │
                    └────────┬────────┘       └────────┬────────┘ └──────────────┘
                             │                         │
                             ▼                         ▼
                    ┌─────────────────┐       ┌─────────────────┐
                    │ Baseline Update │       │ Notification    │
                    │ (async)         │       │ (email/ slack)  │
                    └─────────────────┘       └─────────────────┘
```

### Batch Processing

```rust
pub struct DailyBatchJob;

#[async_trait]
impl Job for DailyBatchJob {
    async fn run(&self, ctx: &JobContext) -> Result<JobResult> {
        // 1. Aggregate last 24h of benchmarks
        let daily = ctx.storage.aggregate(AggregationSpec {
            time_range: TimeRange::last_n_days(1),
            group_by: vec!["tool_name", "tool_version"],
            metrics: vec!["duration_ms", "memory_mb"],
        }).await?;
        
        // 2. Detect trends
        let trends = TrendAnalyzer::new()
            .with_window(30.days())
            .detect(&daily)
            .await?;
        
        // 3. Update rolling baselines
        for trend in trends {
            if trend.confidence > 0.95 {
                ctx.baselines.update(&trend).await?;
            }
        }
        
        // 4. Generate reports
        let report = ReportGenerator::new()
            .template(Template::DailySummary)
            .generate(&daily, &trends)
            .await?;
        
        ctx.reports.publish(report).await?;
        
        Ok(JobResult::success())
    }
}
```

---

## Consequences

### Positive

- **Accurate measurements**: Hybrid approach captures both wall time and system metrics
- **Privacy-first**: Default strict mode ensures no sensitive data leakage
- **Extensible storage**: Plugin architecture allows PostgreSQL/ cloud backends
- **Real-time insights**: Stream processing enables immediate feedback
- **Platform coverage**: Abstracted profilers work on Linux, macOS, Windows

### Negative

- **Complexity**: Three separate monitoring systems increase code surface
- **Overhead**: Even lightweight monitoring adds ~1-2% overhead
- **Storage growth**: Time-series data grows rapidly without retention policies
- **Platform limits**: Some metrics (perf counters) are Linux-only

### Mitigations

- Aggressive data retention (30-day raw, 1-year aggregated)
- Configurable sampling intervals (default: 10ms)
- Optional system profiling (disabled by default)
- Compression for time-series data (LZ4)

---

## Related ADRs

- ADR-001: Performance Measurement Strategy
- ADR-003: Tool Integration Strategy
- ADR-004: Storage Backend Selection

## References

- [hyperfine](https://github.com/sharkdp/hyperfine) - Command-line benchmarking tool
- [psutil](https://github.com/giampaolo/psutil) - Cross-platform process monitoring
- [Linux perf](https://perf.wiki.kernel.org/) - Performance counters
- [DTrace](http://dtrace.org/) - Dynamic tracing (macOS/Solaris)
- [SQLite WAL Mode](https://sqlite.org/wal.html) - Write-ahead logging for concurrent access
