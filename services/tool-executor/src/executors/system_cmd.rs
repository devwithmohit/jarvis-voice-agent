use std::process::{Command, Stdio};
use std::time::Duration;
use tokio::time::timeout;
use anyhow::{Result, Context};
use tracing::{info, debug, warn};
use std::sync::Arc;
use crate::security::SecurityValidator;

pub struct SystemExecutor {
    validator: Arc<SecurityValidator>,
}

impl SystemExecutor {
    pub fn new(validator: Arc<SecurityValidator>) -> Self {
        Self { validator }
    }

    pub async fn execute_command(&self, command: &str) -> Result<CommandResult> {
        info!("Executing command: {}", command);

        // Validate command
        self.validator
            .validate_command(command)
            .context("Command validation failed")?;

        // Parse command
        let parts: Vec<&str> = command.split_whitespace().collect();
        if parts.is_empty() {
            return Err(anyhow::anyhow!("Empty command"));
        }

        let (cmd, args) = parts.split_first().unwrap();
        debug!("Command: {}, Args: {:?}", cmd, args);

        // Execute with timeout
        let timeout_duration = Duration::from_secs(self.validator.get_command_timeout());

        let execution = async {
            let output = Command::new(cmd)
                .args(args)
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .output()
                .context("Failed to execute command")?;

            let stdout = String::from_utf8_lossy(&output.stdout).to_string();
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();
            let exit_code = output.status.code().unwrap_or(-1);
            let success = output.status.success();

            debug!("Command exit code: {}", exit_code);
            debug!("Command stdout length: {} bytes", stdout.len());
            debug!("Command stderr length: {} bytes", stderr.len());

            Ok::<CommandResult, anyhow::Error>(CommandResult {
                stdout,
                stderr,
                exit_code,
                success,
            })
        };

        let result = timeout(timeout_duration, execution)
            .await
            .context("Command execution timeout")??;

        if result.success {
            info!("Command executed successfully");
        } else {
            warn!("Command failed with exit code: {}", result.exit_code);
        }

        Ok(result)
    }

    pub fn get_working_directory(&self) -> Result<String> {
        std::env::current_dir()
            .context("Failed to get current directory")?
            .to_str()
            .ok_or_else(|| anyhow::anyhow!("Invalid UTF-8 in path"))
            .map(String::from)
    }

    pub fn get_environment_variable(&self, name: &str) -> Option<String> {
        std::env::var(name).ok()
    }
}

#[derive(Debug, Clone)]
pub struct CommandResult {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
    pub success: bool,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_simple_command() {
        // Test requires proper security config setup
        // Omitted for brevity
    }
}
