use regex::Regex;
use std::path::{Path, PathBuf};
use anyhow::{Result, anyhow};
use tracing::{debug, warn};
use crate::security::SecurityConfig;

pub struct SecurityValidator {
    pub config: SecurityConfig,
    blocked_path_regexes: Vec<Regex>,
    allowed_dir_regexes: Vec<Regex>,
}

impl SecurityValidator {
    pub fn from_config(config: SecurityConfig) -> Result<Self> {
        // Compile blocked path patterns
        let blocked_path_regexes = config
            .file_operations
            .blocked_paths
            .iter()
            .map(|pattern| {
                let regex_pattern = Self::glob_to_regex(pattern);
                Regex::new(&regex_pattern)
            })
            .collect::<Result<Vec<_>, _>>()?;

        // Compile allowed directory patterns
        let allowed_dir_regexes = config
            .file_operations
            .allowed_directories
            .iter()
            .map(|pattern| {
                let expanded = shellexpand::tilde(pattern);
                let regex_pattern = Self::glob_to_regex(&expanded);
                Regex::new(&regex_pattern)
            })
            .collect::<Result<Vec<_>, _>>()?;

        Ok(Self {
            config,
            blocked_path_regexes,
            allowed_dir_regexes,
        })
    }

    fn glob_to_regex(pattern: &str) -> String {
        pattern
            .replace("\\", "\\\\")
            .replace(".", "\\.")
            .replace("*", ".*")
            .replace("?", ".")
    }

    pub fn validate_file_read(&self, path: &str) -> Result<()> {
        debug!("Validating file read: {}", path);
        self.validate_file_access(path, &self.config.file_operations.allowed_extensions.read)
    }

    pub fn validate_file_write(&self, path: &str) -> Result<()> {
        debug!("Validating file write: {}", path);
        self.validate_file_access(path, &self.config.file_operations.allowed_extensions.write)
    }

    fn validate_file_access(&self, path: &str, allowed_exts: &[String]) -> Result<()> {
        // Expand tilde and normalize path
        let expanded = shellexpand::tilde(path);
        let path_normalized = expanded.to_string();

        // Check blocked paths first
        for regex in &self.blocked_path_regexes {
            if regex.is_match(&path_normalized) {
                warn!("Path is blocked: {}", path);
                return Err(anyhow!("Access denied: path is in blocked list"));
            }
        }

        // Check allowed directories
        let in_allowed_dir = self.allowed_dir_regexes
            .iter()
            .any(|regex| regex.is_match(&path_normalized));

        if !in_allowed_dir {
            warn!("Path not in allowed directory: {}", path);
            return Err(anyhow!("Access denied: path not in allowed directories"));
        }

        // Check file extension
        let path_obj = Path::new(&path_normalized);
        if let Some(ext) = path_obj.extension() {
            let ext_str = format!(".{}", ext.to_string_lossy());
            if !allowed_exts.contains(&ext_str) {
                warn!("File extension not allowed: {}", ext_str);
                return Err(anyhow!("Access denied: file extension '{}' not allowed", ext_str));
            }
        } else {
            // Files without extension not allowed
            return Err(anyhow!("Access denied: files must have an extension"));
        }

        debug!("Path validation passed: {}", path);
        Ok(())
    }

    pub fn validate_command(&self, command: &str) -> Result<()> {
        if !self.config.system_commands.enabled {
            return Err(anyhow!("System commands are disabled"));
        }

        debug!("Validating command: {}", command);

        // Extract command name (first word)
        let cmd_name = command
            .split_whitespace()
            .next()
            .ok_or_else(|| anyhow!("Empty command"))?;

        // Check allowlist
        if !self.config.system_commands.allowlist.contains(&cmd_name.to_string()) {
            warn!("Command not in allowlist: {}", cmd_name);
            return Err(anyhow!("Command '{}' not allowed", cmd_name));
        }

        // Check blocked patterns
        for pattern in &self.config.system_commands.blocked_patterns {
            if command.contains(pattern) {
                warn!("Command contains blocked pattern '{}': {}", pattern, command);
                return Err(anyhow!("Command contains blocked pattern: {}", pattern));
            }
        }

        debug!("Command validation passed: {}", command);
        Ok(())
    }

    pub fn get_max_file_size(&self) -> u64 {
        self.config.file_operations.max_file_size_mb * 1024 * 1024
    }

    pub fn get_command_timeout(&self) -> u64 {
        self.config.system_commands.timeout_seconds
    }

    pub fn get_allowed_read_extensions(&self) -> &[String] {
        &self.config.file_operations.allowed_extensions.read
    }

    pub fn is_commands_enabled(&self) -> bool {
        self.config.system_commands.enabled
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_config() -> SecurityConfig {
        SecurityConfig {
            file_operations: crate::security::FileOperationsConfig {
                allowed_extensions: crate::security::AllowedExtensions {
                    read: vec![".txt".to_string()],
                    write: vec![".txt".to_string()],
                },
                blocked_paths: vec!["/etc/*".to_string()],
                allowed_directories: vec!["/tmp/*".to_string()],
                max_file_size_mb: 10,
            },
            system_commands: crate::security::SystemCommandsConfig {
                enabled: true,
                allowlist: vec!["ls".to_string(), "pwd".to_string()],
                blocked_patterns: vec!["rm -rf".to_string()],
                timeout_seconds: 10,
            },
            environment: crate::security::EnvironmentConfig {
                sandbox_user: "test".to_string(),
                max_execution_time_ms: 5000,
                max_output_bytes: 1048576,
            },
        }
    }

    #[test]
    fn test_blocked_path() {
        let config = create_test_config();
        let validator = SecurityValidator::from_config(config).unwrap();

        let result = validator.validate_file_read("/etc/passwd");
        assert!(result.is_err());
    }

    #[test]
    fn test_allowed_path() {
        let config = create_test_config();
        let validator = SecurityValidator::from_config(config).unwrap();

        let result = validator.validate_file_read("/tmp/test.txt");
        assert!(result.is_ok());
    }

    #[test]
    fn test_command_allowlist() {
        let config = create_test_config();
        let validator = SecurityValidator::from_config(config).unwrap();

        assert!(validator.validate_command("ls -la").is_ok());
        assert!(validator.validate_command("whoami").is_err());
    }

    #[test]
    fn test_blocked_pattern() {
        let config = create_test_config();
        let validator = SecurityValidator::from_config(config).unwrap();

        let result = validator.validate_command("rm -rf /");
        assert!(result.is_err());
    }
}
