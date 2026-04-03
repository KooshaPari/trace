# ADR-001: Performance Measurement Strategy

**Date**: 2026-04-02  
**Status**: Accepted  
**Deciders**: Agent  

## Context

Tracera analyzes Python tooling performance. A consistent, accurate measurement methodology is required to provide reliable benchmarks across different tools.

## Decision Drivers

- **Accuracy**: Meaningful, reproducible results
- **Fairness**: Comparable conditions for all tools
- **Overhead**: Measurement should not distort results
- **Coverage**: Multiple dimensions (time, memory, CPU)
- **Reporting**: Clear, actionable output

## Options Considered

### Measurement Tools

| Tool | Type | Overhead | Accuracy | Best For |
|------|------|----------|----------|----------|
| **hyperfine** | External | Very low | High | Command benchmarks |
| **criterion** | In-process | Low | Very high | Rust micro-benchmarks |
| **time** (shell) | External | Minimal | Medium | Quick checks |
| **perf** (Linux) | Kernel | Minimal | Very high | Deep profiling |
| **psutil** | Sampling | Medium | Medium | Memory tracking |

## Decision

**Multi-layer measurement architecture**:

1. **Primary**: hyperfine for command-level benchmarks
2. **Secondary**: psutil for resource monitoring
3. **Deep**: perf integration for profiling
4. **CI**: Criterion-style statistical rigor

### Architecture

```rust
pub struct BenchmarkRunner {
    config: BenchmarkConfig,
    hyperfine: HyperfineIntegration,
    resource_monitor: ResourceMonitor,
}

pub struct BenchmarkConfig {
    /// Number of warmup runs
    pub warmup_count: u32,
    /// Number of measurement runs
    pub measurement_count: u32,
    /// Minimum runtime per command
    pub min_runtime_seconds: f64,
    /// Preparation command (cache clearing, etc.)
    pub prepare: Option<String>,
    /// Cleanup command
    pub cleanup: Option<String>,
    /// Export format
    pub export: ExportFormat,
}

pub struct BenchmarkResult {
    pub tool: String,
    pub command: String,
    pub mean: Duration,
    pub stddev: Duration,
    pub min: Duration,
    pub max: Duration,
    pub runs: Vec<Duration>,
    pub memory_peak_mb: f64,
    pub memory_avg_mb: f64,
    pub cpu_percent: f64,
}

impl BenchmarkRunner {
    pub async fn benchmark(&self, tool: &Tool, target: &Path) -> Result<BenchmarkResult> {
        // 1. Warmup runs (not measured)
        for _ in 0..self.config.warmup_count {
            self.run_once(tool, target).await?;
        }
        
        // 2. Measurement runs with resource monitoring
        let mut runs = Vec::new();
        let mut memory_samples = Vec::new();
        let mut cpu_samples = Vec::new();
        
        let monitor = self.resource_monitor.start(tool.pid()?).await?;
        
        for _ in 0..self.config.measurement_count {
            if let Some(ref prepare) = self.config.prepare {
                Command::new("sh").arg("-c").arg(prepare).status().await?;
            }
            
            let start = Instant::now();
            self.run_once(tool, target).await?;
            let elapsed = start.elapsed();
            runs.push(elapsed);
            
            if let Some(ref cleanup) = self.config.cleanup {
                Command::new("sh").arg("-c").arg(cleanup).status().await?;
            }
        }
        
        let resource_summary = monitor.stop().await?;
        
        // 3. Statistical analysis
        let mean = runs.iter().sum::<Duration>() / runs.len() as u32;
        let variance = runs.iter()
            .map(|d| {
                let diff = d.as_secs_f64() - mean.as_secs_f64();
                diff * diff
            })
            .sum::<f64>() / runs.len() as f64;
        let stddev = Duration::from_secs_f64(variance.sqrt());
        
        Ok(BenchmarkResult {
            tool: tool.name().to_string(),
            command: tool.command_for(target),
            mean,
            stddev,
            min: *runs.iter().min().unwrap(),
            max: *runs.iter().max().unwrap(),
            runs,
            memory_peak_mb: resource_summary.memory_peak_mb,
            memory_avg_mb: resource_summary.memory_avg_mb,
            cpu_percent: resource_summary.cpu_percent,
        })
    }
}
```

### hyperfine Integration

```rust
pub struct HyperfineIntegration;

impl HyperfineIntegration {
    pub fn command(&self, config: &BenchmarkConfig, commands: &[String]) -> Command {
        let mut cmd = Command::new("hyperfine");
        
        cmd.arg("--warmup").arg(config.warmup_count.to_string())
           .arg("--runs").arg(config.measurement_count.to_string())
           .arg("--min-runs").arg("10")
           .arg("--style").arg("none")
           .arg("--export-json").arg("/tmp/tracera-hyperfine.json");
        
        if let Some(ref prepare) = config.prepare {
            cmd.arg("--prepare").arg(prepare);
        }
        
        if let Some(ref cleanup) = config.cleanup {
            cmd.arg("--cleanup").arg(cleanup);
        }
        
        for command in commands {
            cmd.arg(command);
        }
        
        cmd
    }
    
    pub fn parse_results(&self, json_path: &Path) -> Result<Vec<HyperfineResult>> {
        let content = fs::read_to_string(json_path)?;
        let data: serde_json::Value = serde_json::from_str(&content)?;
        
        let mut results = Vec::new();
        for result in data["results"].as_array().unwrap_or(&vec![]) {
            results.push(HyperfineResult {
                command: result["command"].as_str().unwrap_or("").to_string(),
                mean: result["mean"].as_f64().unwrap_or(0.0),
                stddev: result["stddev"].as_f64().unwrap_or(0.0),
                min: result["min"].as_f64().unwrap_or(0.0),
                max: result["max"].as_f64().unwrap_or(0.0),
            });
        }
        
        Ok(results)
    }
}
```

### Resource Monitoring

```rust
pub struct ResourceMonitor {
    pid: Pid,
    sample_interval: Duration,
}

impl ResourceMonitor {
    pub async fn start(pid: Pid) -> Result<RunningMonitor> {
        Ok(RunningMonitor {
            pid,
            start_time: Instant::now(),
            samples: Vec::new(),
        })
    }
}

pub struct RunningMonitor {
    pid: Pid,
    start_time: Instant,
    samples: Vec<ResourceSample>,
}

impl RunningMonitor {
    pub async fn sample(&mut self) -> Result<()> {
        let process = Process::new(self.pid)?;
        
        let sample = ResourceSample {
            timestamp: Instant::now(),
            memory_mb: process.memory_info()?.rss() as f64 / 1024.0 / 1024.0,
            cpu_percent: process.cpu_percent()?,
        };
        
        self.samples.push(sample);
        Ok(())
    }
    
    pub async fn stop(self) -> Result<ResourceSummary> {
        let memory_peak = self.samples.iter()
            .map(|s| s.memory_mb)
            .fold(0.0, f64::max);
        
        let memory_avg = self.samples.iter()
            .map(|s| s.memory_mb)
            .sum::<f64>() / self.samples.len() as f64;
        
        let cpu_avg = self.samples.iter()
            .map(|s| s.cpu_percent)
            .sum::<f64>() / self.samples.len() as f64;
        
        Ok(ResourceSummary {
            memory_peak_mb: memory_peak,
            memory_avg_mb: memory_avg,
            cpu_percent: cpu_avg,
            duration: self.start_time.elapsed(),
        })
    }
}
```

## Measurement Best Practices

### 1. Cache Clearing

For fair comparison, clear caches between runs:

```bash
# Linux: clear disk cache
echo 3 > /proc/sys/vm/drop_caches

# macOS: clear unified buffer cache
purge
```

### 2. Statistical Rigor

- Minimum 10 runs
- Discard outliers (>2 stddev)
- Report confidence intervals
- Warmup runs to stabilize cache

### 3. Controlled Environment

```rust
pub struct EnvironmentControl {
    /// CPU isolation (taskset on Linux)
    cpu_affinity: Option<Vec<usize>>,
    /// Disable CPU frequency scaling
    disable_turbo: bool,
    /// Nice level
    nice_level: i32,
}

impl EnvironmentControl {
    pub fn apply(&self) -> Result<()> {
        if self.disable_turbo {
            // Disable Intel Turbo Boost / AMD Precision Boost
            fs::write(
                "/sys/devices/system/cpu/intel_pstate/no_turbo",
                "1"
            )?;
        }
        
        // Set process priority
        unsafe {
            libc::nice(self.nice_level);
        }
        
        Ok(())
    }
}
```

## Consequences

### Positive
- **Accurate**: hyperfine + statistical analysis
- **Comprehensive**: Time, memory, CPU
- **Reproducible**: Controlled environment
- **Extensible**: Plugin architecture for new tools

### Negative
- **Setup**: Requires hyperfine installation
- **Time**: Thorough benchmarking takes time
- **Platform**: Some features Linux-only

## References

- hyperfine: https://github.com/sharkdp/hyperfine
- criterion.rs: https://github.com/bheisler/criterion.rs
- psutil: https://github.com/giampaolo/psutil
- Tracera SOTA Research: `docs/research/PYTHON_TOOLING_SOTA.md`

---

*This ADR will be updated as implementation progresses*
