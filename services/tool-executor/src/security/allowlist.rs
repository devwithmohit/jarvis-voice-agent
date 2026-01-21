use serde::{Deserialize, Serialize};
use std::fs;
use anyhow::Result;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SecurityConfig {
    pub file_operations: FileOperationsConfig,
    pub system_commands: SystemCommandsConfig,
    pub environment: EnvironmentConfig,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct FileOperationsConfig {
    pub allowed_extensions: AllowedExtensions,
    pub blocked_paths: Vec<String>,
    pub allowed_directories: Vec<String>,
    pub max_file_size_mb: u64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct AllowedExtensions {
    pub read: Vec<String>,
    pub write: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SystemCommandsConfig {
    pub enabled: bool,
    pub allowlist: Vec<String>,
    pub blocked_patterns: Vec<String>,
    pub timeout_seconds: u64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct EnvironmentConfig {
    pub sandbox_user: String,
    pub max_execution_time_ms: u64,
    pub max_output_bytes: usize,
}

pub fn load_config(path: &str) -> Result<SecurityConfig> {
    let content = fs::read_to_string(path)?;
    let config: SecurityConfig = serde_yaml::from_str(&content)?;
    Ok(config)
}
