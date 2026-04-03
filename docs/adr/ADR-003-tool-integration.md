# ADR-003: Tool Integration Strategy

**Status**: Accepted  
**Date**: 2026-04-02  
**Deciders**: Architecture Team  
**Supersedes**: —

---

## Context

Tracera must integrate with a diverse ecosystem of Python development tools including linters (ruff, flake8), type checkers (mypy, pyright), package managers (uv, pip), formatters (black, ruff format), and test runners (pytest). Each tool has unique:

- CLI interfaces and argument conventions
- Output formats (JSON, TOML, custom text)
- Version cadences and breaking changes
- Configuration systems (pyproject.toml, setup.cfg, .ini files)
- Performance characteristics

A unified integration strategy is required to add new tools without core code changes, handle version compatibility, and provide seamless updates.

---

## Decision Drivers

| Driver | Priority | Description |
|--------|----------|-------------|
| **Extensibility** | P0 | Add new tools without recompiling Tracera |
| **Version Agility** | P0 | Support multiple tool versions simultaneously |
| **Isolation** | P0 | Tool crashes must not affect Tracera stability |
| **Configuration** | P1 | Unified config layer over tool-specific formats |
| **Discovery** | P1 | Auto-detect available tools in environment |
| **Update Safety** | P1 | Rollback capability for problematic tool versions |

---

## Considered Options

### Option A: Hardcoded Adapters (REJECTED)

Implement each tool integration as a dedicated Rust module with compiled-in logic.

```rust
// Hardcoded approach - each tool is a module
pub mod ruff;
pub mod uv;
pub mod mypy;
// ... etc

pub enum Tool {
    Ruff(RuffAdapter),
    Uv(UvAdapter),
    Mypy(MypyAdapter),
}

impl Tool {
    pub async fn run(&self, target: &Path) -> Result<ToolOutput> {
        match self {
            Tool::Ruff(adapter) => adapter.run(target).await,
            Tool::Uv(adapter) => adapter.run(target).await,
            // ... etc
        }
    }
}
```

**Pros**:
- Type-safe at compile time
- Optimal performance (no runtime overhead)
- IDE-friendly autocomplete

**Cons**:
- Requires recompilation to add tools
- Binary size grows with each tool
- Version updates require code changes
- Testing burden increases linearly

### Option B: External Process Wrappers (REJECTED)

Execute tools as external processes, parse output via regex/JSON.

```rust
pub struct ExternalTool {
    binary_path: PathBuf,
    version: String,
}

impl ExternalTool {
    pub async fn run(&self, target: &Path) -> Result<ToolOutput> {
        let output = Command::new(&self.binary_path)
            .arg("--output-format=json")
            .arg(target)
            .output()
            .await?;
        
        self.parse_output(&output.stdout)
    }
}
```

**Pros**:
- Simple implementation
- Works with any executable
- Natural process isolation

**Cons**:
- Fragile parsing (regex breaks on format changes)
- No standardized error handling
- High per-invocation overhead
- Difficult to extend without code changes

### Option C: Plugin Architecture with Manifests (ACCEPTED)

Define tools via declarative YAML/TOML manifests with embedded or referenced adapter scripts.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Plugin Architecture                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │                        Tool Registry                                    │   │
│  │                                                                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │   │
│  │  │    ruff      │  │     uv       │  │    mypy      │  │  pyright  │ │   │
│  │  │  (builtin)   │  │  (builtin)   │  │  (builtin)   │  │ (builtin) │ │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │   │
│  │         │                 │                 │                │       │   │
│  │         └─────────────────┴─────────────────┘                │       │   │
│  │                           │                                    │       │   │
│  │         ┌─────────────────┴──────────────────┐               │       │   │
│  │         │                                    │               │       │   │
│  │         ▼                                    ▼               ▼       │   │
│  │  ┌─────────────┐                    ┌─────────────┐  ┌─────────────┐│   │
│  │  │  bandit     │                    │  custom-1   │  │  custom-2   ││   │
│  │  │  (plugin)   │                    │  (plugin)   │  │  (plugin)   ││   │
│  │  └─────────────┘                    └─────────────┘  └─────────────┘│   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │                     Plugin Loader & Sandbox                               ││
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────────┐  ││
│  │  │ Manifest Parser │  │ Adapter Executor │  │   Version Manager      │  ││
│  │  │   (TOML/YAML)   │  │ (WASM/embedded)  │  │   (semver resolution)  │  ││
│  │  └─────────────────┘  └──────────────────┘  └────────────────────────┘  ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │                      Unified Tool Interface                               ││
│  │                                                                         ││
│  │   ┌────────────────────────────────────────────────────────────────┐   ││
│  │   │  trait ToolAdapter {                                            │   ││
│  │   │      fn name(&self) -> &str;                                    │   ││
│  │   │      fn version(&self) -> Version;                             │   ││
│  │   │      async fn run(&self, ctx: &RunContext) -> Result<RunResult>;│   ││
│  │   │      fn supported_targets(&self) -> Vec<TargetType>;           │   ││
│  │   │      fn configuration_schema(&self) -> Schema;                   │   ││
│  │   │  }                                                              │   ││
│  │   └────────────────────────────────────────────────────────────────┘   ││
│  │                                                                         ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │                      Execution Engine                                     ││
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────────┐││
│  │  │  Process Spawner│  │ Output Parser    │  │  Result Normalizer       │││
│  │  │  (isolated)     │  │ (structured)     │  │  (unified format)        │││
│  │  └─────────────────┘  └──────────────────┘  └────────────────────────┘││
│  └────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Decision Outcome

**Chosen**: Option C - Plugin Architecture with Manifests

### Core Design

#### 1. Tool Manifest Schema

```yaml
# tools/ruff/manifest.yaml
name: ruff
description: An extremely fast Python linter and code formatter
author: Astral
license: MIT
category: [linter, formatter]

# Version compatibility matrix
versions:
  - range: ">=0.6.0"
    manifest_version: "1.0"
    binary: ruff
    
  - range: ">=0.5.0, <0.6.0"
    manifest_version: "1.0"
    binary: ruff
    deprecated: true
    deprecation_message: "Upgrade to ruff 0.6+ for better performance"

# Tool discovery
discovery:
  methods:
    - type: path
      env_var: "RUFF_PATH"
    - type: which
      command: "ruff"
    - type: python_package
      package: "ruff"
      module: "ruff"

# Configuration schema
configuration:
  file_formats:
    - pyproject.toml:
        section: "tool.ruff"
    - ruff.toml
  
  schema:
    target_version:
      type: string
      enum: ["py37", "py38", "py39", "py310", "py311", "py312", "py313"]
      default: "py311"
    
    line_length:
      type: integer
      minimum: 1
      maximum: 320
      default: 88
    
    select:
      type: array
      items:
        type: string
      description: "Rule codes to enable"
    
    ignore:
      type: array
      items:
        type: string
      description: "Rule codes to disable"

# Command definitions
commands:
  lint:
    description: "Run linter on Python files"
    default: true
    args:
      - "check"
      - "--output-format=json"
      - "--no-cache"  # Tracera handles caching
      - "{target}"
    
    output:
      format: json
      schema: "./schemas/lint-output.json"
      error_on: "$.code != null"
    
    metrics:
      - name: files_checked
        path: "$.filenames | length"
      - name: errors_found
        path: "$.messages | map(select(.code)) | length"
      - name: fixes_available
        path: "$.messages | map(select(.fix)) | length"

  format:
    description: "Format Python files"
    args:
      - "format"
      - "--check"  # Dry run for benchmarking
      - "--diff"
      - "{target}"
    
    output:
      format: text
      success_code: 0

# Performance hints
performance:
  supports_incremental: true
  cache_directory: ".ruff_cache"
  parallelizable: true
  memory_heavy: false
  
  # Resource limits for sandboxing
  resource_limits:
    max_memory_mb: 2048
    max_cpu_time_seconds: 300
    max_file_handles: 1024
```

#### 2. Tool Registry (`ToolRegistry`)

```rust
pub struct ToolRegistry {
    /// Built-in tools (compiled into binary)
    builtin_tools: HashMap<String, Arc<dyn ToolAdapter>>,
    
    /// Discovered plugin tools
    plugin_tools: RwLock<HashMap<String, PluginTool>>,
    
    /// Version resolution cache
    version_cache: Arc<dyn VersionCache>,
    
    /// Manifest loader
    manifest_loader: ManifestLoader,
}

impl ToolRegistry {
    pub async fn new(config: RegistryConfig) -> Result<Self> {
        let mut builtin_tools = HashMap::new();
        
        // Register built-in adapters
        builtin_tools.insert("ruff".to_string(), Arc::new(RuffAdapter::new()) as Arc<dyn ToolAdapter>);
        builtin_tools.insert("uv".to_string(), Arc::new(UvAdapter::new()) as Arc<dyn ToolAdapter>);
        builtin_tools.insert("mypy".to_string(), Arc::new(MypyAdapter::new()) as Arc<dyn ToolAdapter>);
        builtin_tools.insert("pyright".to_string(), Arc::new(PyrightAdapter::new()) as Arc<dyn ToolAdapter>);
        
        Ok(Self {
            builtin_tools,
            plugin_tools: RwLock::new(HashMap::new()),
            version_cache: Arc::new(InMemoryVersionCache::new()),
            manifest_loader: ManifestLoader::new(&config.plugin_paths),
        })
    }
    
    /// Discover and load all available tools
    pub async fn discover(&self) -> Result<Vec<ToolInfo>> {
        let mut tools = Vec::new();
        
        // Add built-in tools
        for (name, adapter) in &self.builtin_tools {
            if let Ok(version) = adapter.detect_version().await {
                tools.push(ToolInfo {
                    name: name.clone(),
                    version,
                    source: ToolSource::Builtin,
                    available: true,
                });
            }
        }
        
        // Scan plugin directories
        let plugin_manifests = self.manifest_loader.scan().await?;
        
        for manifest in plugin_manifests {
            match self.load_plugin(&manifest).await {
                Ok(plugin) => {
                    let mut plugins = self.plugin_tools.write().await;
                    plugins.insert(manifest.name.clone(), plugin);
                    
                    tools.push(ToolInfo {
                        name: manifest.name,
                        version: manifest.version,
                        source: ToolSource::Plugin(manifest.path),
                        available: true,
                    });
                }
                Err(e) => {
                    warn!("Failed to load plugin {}: {}", manifest.name, e);
                }
            }
        }
        
        Ok(tools)
    }
    
    /// Get tool by name with version resolution
    pub async fn get(&self, name: &str, version_req: Option<&str>) -> Result<Arc<dyn ToolAdapter>> {
        // Check built-in first
        if let Some(tool) = self.builtin_tools.get(name) {
            if let Some(req) = version_req {
                let version = tool.version().await?;
                if !VersionReq::parse(req)?.matches(&version) {
                    bail!("Built-in {} version {} doesn't satisfy requirement {}", 
                          name, version, req);
                }
            }
            return Ok(tool.clone());
        }
        
        // Check plugins
        let plugins = self.plugin_tools.read().await;
        if let Some(plugin) = plugins.get(name) {
            if let Some(req) = version_req {
                if !VersionReq::parse(req)?.matches(&plugin.manifest.version) {
                    bail!("Plugin {} version {} doesn't satisfy requirement {}",
                          name, plugin.manifest.version, req);
                }
            }
            return Ok(plugin.adapter.clone());
        }
        
        bail!("Tool '{}' not found in registry", name)
    }
}
```

#### 3. Plugin System (`PluginTool`)

```rust
pub struct PluginTool {
    manifest: ToolManifest,
    adapter: Arc<dyn ToolAdapter>,
    wasm_instance: Option<WasmInstance>,
}

pub struct ToolManifest {
    pub name: String,
    pub version: Version,
    pub description: String,
    pub author: String,
    pub categories: Vec<ToolCategory>,
    pub commands: HashMap<String, CommandDef>,
    pub configuration: ConfigSchema,
    pub discovery: DiscoveryConfig,
    pub performance: PerformanceHints,
}

/// Adapter implementation for plugin-based tools
pub struct PluginAdapter {
    manifest: ToolManifest,
    wasm_engine: Option<WasmEngine>,
    binary_path: PathBuf,
}

#[async_trait]
impl ToolAdapter for PluginAdapter {
    fn name(&self) -> &str {
        &self.manifest.name
    }
    
    async fn version(&self) -> Result<Version> {
        // Check version from binary or cache
        let output = Command::new(&self.binary_path)
            .arg("--version")
            .output()
            .await?;
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        self.parse_version(&stdout)
    }
    
    async fn run(&self, ctx: &RunContext) -> Result<RunResult> {
        let command_def = self.manifest.commands
            .get(&ctx.command)
            .ok_or_else(|| anyhow!("Unknown command: {}", ctx.command))?;
        
        // Build command arguments
        let args = self.build_args(command_def, ctx)?;
        
        // Execute with sandboxing
        let mut cmd = Command::new(&self.binary_path);
        cmd.args(&args)
            .current_dir(&ctx.working_dir)
            .env_clear()
            .envs(&ctx.env_vars);
        
        // Apply resource limits
        if let Some(limits) = &self.manifest.performance.resource_limits {
            #[cfg(target_os = "linux")]
            {
                cmd = self.apply_linux_limits(cmd, limits);
            }
        }
        
        let output = cmd.output().await?;
        
        // Parse structured output
        let parsed = self.parse_output(command_def, &output).await?;
        
        Ok(RunResult {
            exit_code: output.status.code().unwrap_or(-1),
            stdout: output.stdout,
            stderr: output.stderr,
            parsed,
            metrics: self.extract_metrics(command_def, &parsed),
        })
    }
    
    fn configuration_schema(&self) -> &ConfigSchema {
        &self.manifest.configuration
    }
    
    fn supported_targets(&self) -> Vec<TargetType> {
        // Infer from command definitions
        self.manifest.commands.values()
            .flat_map(|cmd| cmd.target_types.clone())
            .collect::<HashSet<_>>()
            .into_iter()
            .collect()
    }
}
```

#### 4. Version Management

```rust
pub struct VersionManager {
    cache: Arc<dyn VersionCache>,
    resolvers: Vec<Box<dyn VersionResolver>>,
}

pub trait VersionResolver: Send + Sync {
    fn name(&self) -> &str;
    async fn resolve(&self, tool: &str, version_req: &str) -> Result<Option<Version>>;
    async fn install(&self, tool: &str, version: &Version) -> Result<PathBuf>;
}

/// uv-based Python package resolver
pub struct UvVersionResolver {
    uv_path: PathBuf,
    cache_dir: PathBuf,
}

#[async_trait]
impl VersionResolver for UvVersionResolver {
    fn name(&self) -> &str {
        "uv"
    }
    
    async fn resolve(&self, tool: &str, version_req: &str) -> Result<Option<Version>> {
        // Use uv to find matching version
        let output = Command::new(&self.uv_path)
            .args(&["tool", "run", "--from", &format!("{}=={}", tool, version_req), tool, "--version"])
            .output()
            .await?;
        
        if !output.status.success() {
            return Ok(None);
        }
        
        // Parse version from output
        let stdout = String::from_utf8_lossy(&output.stdout);
        Ok(Some(self.parse_version(&stdout)?))
    }
    
    async fn install(&self, tool: &str, version: &Version) -> Result<PathBuf> {
        let tool_dir = self.cache_dir.join(format!("{}-{}", tool, version));
        
        if !tool_dir.exists() {
            // Install with uv
            let status = Command::new(&self.uv_path)
                .args(&[
                    "tool", "install",
                    "--tool-dir", &tool_dir.to_string_lossy(),
                    &format!("{}=={}", tool, version)
                ])
                .status()
                .await?;
            
            if !status.success() {
                bail!("Failed to install {}=={}", tool, version);
            }
        }
        
        Ok(tool_dir.join("bin").join(tool))
    }
}

/// PyPI JSON API resolver (for version discovery)
pub struct PyPiVersionResolver {
    client: reqwest::Client,
}

#[async_trait]
impl VersionResolver for PyPiVersionResolver {
    fn name(&self) -> &str {
        "pypi"
    }
    
    async fn resolve(&self, tool: &str, version_req: &str) -> Result<Option<Version>> {
        let url = format!("https://pypi.org/pypi/{}/json", tool);
        let resp = self.client.get(&url).send().await?;
        
        if !resp.status().is_success() {
            return Ok(None);
        }
        
        let data: PyPiResponse = resp.json().await?;
        let req = VersionReq::parse(version_req)?;
        
        // Find best matching version
        let matching = data.releases.keys()
            .filter_map(|v| Version::parse(v).ok())
            .filter(|v| req.matches(v))
            .max();
        
        Ok(matching)
    }
    
    async fn install(&self, _tool: &str, _version: &Version) -> Result<PathBuf> {
        // PyPI doesn't handle installation - delegate to uv/pip
        bail!("PyPI resolver is discovery-only")
    }
}
```

#### 5. Update Mechanisms

```rust
pub struct UpdateManager {
    registry: Arc<ToolRegistry>,
    check_interval: Duration,
    notification_handlers: Vec<Box<dyn UpdateNotificationHandler>>,
}

impl UpdateManager {
    /// Check for available updates across all registered tools
    pub async fn check_for_updates(&self) -> Result<Vec<UpdateInfo>> {
        let tools = self.registry.discover().await?;
        let mut updates = Vec::new();
        
        for tool in tools {
            if let Some(latest) = self.fetch_latest_version(&tool.name).await? {
                if latest > tool.version {
                    updates.push(UpdateInfo {
                        tool: tool.name,
                        current: tool.version,
                        latest,
                        changelog_url: self.get_changelog_url(&tool.name, &latest),
                        breaking_changes: self.check_breaking_changes(&tool.name, &tool.version, &latest).await,
                    });
                }
            }
        }
        
        Ok(updates)
    }
    
    /// Apply update with rollback capability
    pub async fn apply_update(&self, tool: &str, version: &Version) -> Result<UpdateResult> {
        // 1. Create backup of current version
        let current = self.registry.get(tool, None).await?;
        let backup = self.create_backup(tool, &current.version().await?).await?;
        
        // 2. Download and install new version
        let install_result = self.install_version(tool, version).await;
        
        // 3. Run smoke tests
        match install_result {
            Ok(_) => {
                if let Err(e) = self.run_smoke_tests(tool).await {
                    // Rollback on test failure
                    self.restore_backup(backup).await?;
                    return Ok(UpdateResult::RolledBack {
                        version: version.clone(),
                        reason: format!("Smoke test failed: {}", e),
                    });
                }
                
                Ok(UpdateResult::Success {
                    version: version.clone(),
                    previous: current.version().await?,
                })
            }
            Err(e) => {
                self.restore_backup(backup).await?;
                Ok(UpdateResult::Failed {
                    version: version.clone(),
                    error: e.to_string(),
                })
            }
        }
    }
    
    /// Auto-update channel management
    pub async fn set_channel(&self, tool: &str, channel: UpdateChannel) -> Result<()> {
        let config = match channel {
            UpdateChannel::Stable => ToolChannelConfig {
                version_constraint: ">=1.0.0, <2.0.0".to_string(),
                prerelease: false,
            },
            UpdateChannel::Beta => ToolChannelConfig {
                version_constraint: ">=0.9.0".to_string(),
                prerelease: true,
            },
            UpdateChannel::Nightly => ToolChannelConfig {
                version_constraint: "*".to_string(),
                prerelease: true,
                source: Some("git+https://github.com/astral-sh/ruff".to_string()),
            },
            UpdateChannel::Pinned { version } => ToolChannelConfig {
                version_constraint: format!("={}", version),
                prerelease: false,
            },
        };
        
        self.registry.set_channel(tool, config).await
    }
}

pub enum UpdateChannel {
    Stable,
    Beta,
    Nightly,
    Pinned { version: Version },
}

pub enum UpdateResult {
    Success { version: Version, previous: Version },
    RolledBack { version: Version, reason: String },
    Failed { version: Version, error: String },
}
```

#### 6. Configuration Unification

```rust
/// Unified configuration layer that maps to tool-specific formats
pub struct UnifiedConfig {
    /// Tool-agnostic settings
    pub global: GlobalConfig,
    
    /// Per-tool overrides
    pub tools: HashMap<String, ToolConfig>,
}

pub struct ToolConfig {
    /// Whether tool is enabled
    pub enabled: bool,
    
    /// Version constraint
    pub version: Option<String>,
    
    /// Target Python version
    pub target_version: Option<String>,
    
    /// Line length (for formatters)
    pub line_length: Option<u32>,
    
    /// Rules to enable
    pub select: Option<Vec<String>>,
    
    /// Rules to disable
    pub ignore: Option<Vec<String>>,
    
    /// Tool-specific raw config (passed through)
    pub raw: Option<serde_json::Value>,
}

impl UnifiedConfig {
    /// Generate pyproject.toml section for a tool
    pub fn to_pyproject(&self, tool: &str) -> Result<String> {
        let config = self.tools.get(tool)
            .ok_or_else(|| anyhow!("Tool {} not configured", tool))?;
        
        let tool_name = match tool {
            "ruff" => "tool.ruff",
            "mypy" => "tool.mypy",
            _ => &format!("tool.{}", tool),
        };
        
        let mut toml = format!("[{}]\n", tool_name);
        
        if let Some(ref target) = config.target_version {
            toml.push_str(&format!("target-version = \"{}\"\n", 
                target.replace("py", "")));
        }
        
        if let Some(length) = config.line_length {
            toml.push_str(&format!("line-length = {}\n", length));
        }
        
        if let Some(ref select) = config.select {
            toml.push_str(&format!("select = [{}]\n", 
                select.iter().map(|s| format!("'{}'", s)).collect::<Vec<_>>().join(", ")));
        }
        
        if let Some(ref ignore) = config.ignore {
            toml.push_str(&format!("ignore = [{}]\n",
                ignore.iter().map(|s| format!("'{}'", s)).collect::<Vec<_>>().join(", ")));
        }
        
        // Pass through raw config
        if let Some(ref raw) = config.raw {
            toml.push_str(&self.value_to_toml(raw, 0)?);
        }
        
        Ok(toml)
    }
    
    /// Generate tool-native config file
    pub fn to_native_config(&self, tool: &str) -> Result<NativeConfig> {
        match tool {
            "ruff" => self.generate_ruff_config(),
            "mypy" => self.generate_mypy_config(),
            "uv" => self.generate_uv_config(),
            _ => bail!("Native config not implemented for {}", tool),
        }
    }
}
```

---

## Plugin Development Kit

### Creating a Custom Plugin

```yaml
# ~/.tracera/plugins/bandit/manifest.yaml
name: bandit
description: Security linter for Python
category: [security, linter]
author: Custom
version: "1.0.0"
manifest_version: "1.0"

discovery:
  methods:
    - type: which
      command: "bandit"
    - type: python_package
      package: "bandit"

commands:
  lint:
    args:
      - "bandit"
      - "-f", "json"
      - "-r"
      - "{target}"
    
    output:
      format: json
      schema: |
        {
          "type": "object",
          "properties": {
            "results": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "test_id": {"type": "string"},
                  "test_name": {"type": "string"},
                  "issue_severity": {"type": "string"},
                  "issue_confidence": {"type": "string"},
                  "line_number": {"type": "integer"}
                }
              }
            }
          }
        }
    
    metrics:
      - name: vulnerabilities
        path: "$.results | length"
      - name: high_severity
        path: "$.results | map(select(.issue_severity == 'HIGH')) | length"
      - name: medium_severity
        path: "$.results | map(select(.issue_severity == 'MEDIUM')) | length"

configuration:
  file_formats:
    - pyproject.toml:
        section: "tool.bandit"
  
  schema:
    skips:
      type: array
      items: string
      description: "Tests to skip"
    
    severity_level:
      type: string
      enum: ["low", "medium", "high"]
      default: "low"
```

### WASM-Based Adapters (Advanced)

For complex parsing logic or performance-critical adapters:

```rust
/// WASM-based plugin for sandboxed execution
pub struct WasmAdapter {
    engine: WasmEngine,
    module: WasmModule,
    instance: WasmInstance,
}

impl WasmAdapter {
    pub fn load(wasm_bytes: &[u8]) -> Result<Self> {
        let engine = WasmEngine::new();
        let module = engine.compile(wasm_bytes)?;
        let instance = module.instantiate()?;
        
        Ok(Self { engine, module, instance })
    }
}

#[async_trait]
impl ToolAdapter for WasmAdapter {
    async fn run(&self, ctx: &RunContext) -> Result<RunResult> {
        // Call WASM function with sandboxed execution
        let input = serde_json::to_vec(&ctx)?;
        
        let output = self.instance
            .call("run", &input)
            .await?;
        
        let result: RunResult = serde_json::from_slice(&output)?;
        Ok(result)
    }
}
```

---

## Consequences

### Positive

- **Extensibility**: New tools added via YAML manifests without recompilation
- **Version flexibility**: Multiple tool versions coexist via resolver system
- **Isolation**: Plugin sandboxing prevents tool crashes from affecting Tracera
- **Unified interface**: Single API across all tools regardless of implementation
- **Community plugins**: Third-party tools integrate via standard manifest format
- **Auto-discovery**: Tools found automatically via PATH, pip, conda

### Negative

- **Complexity**: Plugin system adds architectural overhead
- **Performance**: YAML parsing and dynamic dispatch slower than native code
- **Security**: Loading external manifests requires validation/sandboxing
- **Debugging**: Issues span Tracera + plugin + tool (three layers)

### Mitigations

- Built-in adapters for core tools (ruff, uv, mypy, pyright) for performance
- JSON Schema validation for all manifests
- WASM sandboxing for untrusted community plugins
- Comprehensive plugin development documentation

---

## Related ADRs

- ADR-001: Performance Measurement Strategy
- ADR-002: Data Collection Architecture
- ADR-004: Storage Backend Selection

## References

- [PyPI JSON API](https://docs.pypi.org/api/json/)
- [Semantic Versioning](https://semver.org/)
- [WASM Component Model](https://component-model.bytecodealliance.org/)
- [uv tool interface](https://docs.astral.sh/uv/concepts/tools/)
