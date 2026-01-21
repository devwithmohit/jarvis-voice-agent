use std::fs;
use std::path::Path;
use anyhow::{Result, Context};
use tracing::{info, debug, error};
use std::sync::Arc;
use crate::security::SecurityValidator;

pub struct FileExecutor {
    validator: Arc<SecurityValidator>,
}

impl FileExecutor {
    pub fn new(validator: Arc<SecurityValidator>) -> Self {
        Self { validator }
    }

    pub fn read_file(&self, path: &str) -> Result<String> {
        info!("Reading file: {}", path);

        // Validate path
        self.validator
            .validate_file_read(path)
            .context("File read validation failed")?;

        // Check if file exists
        if !Path::new(path).exists() {
            return Err(anyhow::anyhow!("File does not exist: {}", path));
        }

        // Check file size
        let metadata = fs::metadata(path)
            .context("Failed to get file metadata")?;

        let max_size = self.validator.get_max_file_size();
        if metadata.len() > max_size {
            return Err(anyhow::anyhow!(
                "File size ({} bytes) exceeds maximum allowed ({} bytes)",
                metadata.len(),
                max_size
            ));
        }

        debug!("File size: {} bytes", metadata.len());

        // Read file
        let content = fs::read_to_string(path)
            .context("Failed to read file")?;

        info!("Successfully read {} bytes from {}", content.len(), path);
        Ok(content)
    }

    pub fn write_file(&self, path: &str, content: &str) -> Result<()> {
        info!("Writing file: {} ({} bytes)", path, content.len());

        // Validate path
        self.validator
            .validate_file_write(path)
            .context("File write validation failed")?;

        // Check content size
        let max_size = self.validator.get_max_file_size();
        if content.len() > max_size as usize {
            return Err(anyhow::anyhow!(
                "Content size ({} bytes) exceeds maximum allowed ({} bytes)",
                content.len(),
                max_size
            ));
        }

        // Ensure parent directory exists
        if let Some(parent) = Path::new(path).parent() {
            if !parent.exists() {
                debug!("Creating parent directory: {:?}", parent);
                fs::create_dir_all(parent)
                    .context("Failed to create parent directory")?;
            }
        }

        // Write file
        fs::write(path, content)
            .context("Failed to write file")?;

        info!("Successfully wrote {} bytes to {}", content.len(), path);
        Ok(())
    }

    pub fn list_directory(&self, path: &str) -> Result<Vec<String>> {
        info!("Listing directory: {}", path);

        // Validate path
        self.validator
            .validate_file_read(path)
            .context("Directory read validation failed")?;

        // Check if directory exists
        let path_obj = Path::new(path);
        if !path_obj.exists() {
            return Err(anyhow::anyhow!("Directory does not exist: {}", path));
        }

        if !path_obj.is_dir() {
            return Err(anyhow::anyhow!("Path is not a directory: {}", path));
        }

        // Read directory
        let entries: Vec<String> = fs::read_dir(path)
            .context("Failed to read directory")?
            .filter_map(|entry| {
                entry.ok().and_then(|e| {
                    e.file_name().to_str().map(String::from)
                })
            })
            .collect();

        info!("Found {} entries in {}", entries.len(), path);
        debug!("Entries: {:?}", entries);

        Ok(entries)
    }

    pub fn file_exists(&self, path: &str) -> Result<bool> {
        debug!("Checking if file exists: {}", path);

        // Validate path
        self.validator
            .validate_file_read(path)
            .context("File exists check validation failed")?;

        Ok(Path::new(path).exists())
    }

    pub fn get_file_info(&self, path: &str) -> Result<FileInfo> {
        info!("Getting file info: {}", path);

        // Validate path
        self.validator
            .validate_file_read(path)
            .context("File info validation failed")?;

        let metadata = fs::metadata(path)
            .context("Failed to get file metadata")?;

        Ok(FileInfo {
            size_bytes: metadata.len(),
            is_directory: metadata.is_dir(),
            is_file: metadata.is_file(),
            readonly: metadata.permissions().readonly(),
        })
    }
}

#[derive(Debug)]
pub struct FileInfo {
    pub size_bytes: u64,
    pub is_directory: bool,
    pub is_file: bool,
    pub readonly: bool,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;

    // Tests would require setting up test fixtures
    // Omitted for brevity
}
