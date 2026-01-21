use std::sync::Arc;
use tonic::{Request, Response, Status};
use tracing::{info, error, warn};
use crate::security::SecurityValidator;
use crate::executors::{FileExecutor, SystemExecutor};
use crate::generated::{
    tool_executor_server::ToolExecutor,
    FileReadRequest, FileReadResponse,
    FileWriteRequest, FileWriteResponse,
    FileListRequest, FileListResponse, FileEntry,
    FileExistsRequest, FileExistsResponse,
    FileInfoRequest, FileInfoResponse,
    CommandRequest, CommandResponse,
    DirectoryResponse, EmptyRequest,
    EnvVarRequest, EnvVarResponse,
};

pub struct ToolExecutorService {
    file_executor: FileExecutor,
    system_executor: SystemExecutor,
}

impl ToolExecutorService {
    pub fn new(validator: Arc<SecurityValidator>) -> Self {
        info!("Initializing ToolExecutorService");

        let file_executor = FileExecutor::new(Arc::clone(&validator));
        let system_executor = SystemExecutor::new(validator);

        Self {
            file_executor,
            system_executor,
        }
    }
}

#[tonic::async_trait]
impl ToolExecutor for ToolExecutorService {
    async fn read_file(
        &self,
        request: Request<FileReadRequest>,
    ) -> Result<Response<FileReadResponse>, Status> {
        let path = &request.get_ref().path;
        info!("ReadFile request: {}", path);

        match self.file_executor.read_file(path) {
            Ok(content) => {
                info!("File read successful: {} bytes", content.len());
                Ok(Response::new(FileReadResponse {
                    success: true,
                    content,
                    error: String::new(),
                }))
            }
            Err(e) => {
                error!("File read error: {}", e);
                Ok(Response::new(FileReadResponse {
                    success: false,
                    content: String::new(),
                    error: e.to_string(),
                }))
            }
        }
    }

    async fn write_file(
        &self,
        request: Request<FileWriteRequest>,
    ) -> Result<Response<FileWriteResponse>, Status> {
        let req = request.get_ref();
        info!("WriteFile request: {}", req.path);

        match self.file_executor.write_file(&req.path, &req.content) {
            Ok(_) => {
                info!("File write successful");
                Ok(Response::new(FileWriteResponse {
                    success: true,
                    error: String::new(),
                }))
            }
            Err(e) => {
                error!("File write error: {}", e);
                Ok(Response::new(FileWriteResponse {
                    success: false,
                    error: e.to_string(),
                }))
            }
        }
    }

    async fn list_directory(
        &self,
        request: Request<FileListRequest>,
    ) -> Result<Response<FileListResponse>, Status> {
        let path = &request.get_ref().path;
        info!("ListDirectory request: {}", path);

        match self.file_executor.list_directory(path) {
            Ok(entries) => {
                let file_entries: Vec<FileEntry> = entries
                    .iter()
                    .map(|name| FileEntry {
                        name: name.clone(),
                        is_dir: false,
                        size: 0,
                    })
                    .collect();

                info!("Directory list successful: {} entries", file_entries.len());
                Ok(Response::new(FileListResponse {
                    success: true,
                    entries: file_entries,
                    error: String::new(),
                }))
            }
            Err(e) => {
                error!("Directory list error: {}", e);
                Ok(Response::new(FileListResponse {
                    success: false,
                    entries: vec![],
                    error: e.to_string(),
                }))
            }
        }
    }

    async fn file_exists(
        &self,
        request: Request<FileExistsRequest>,
    ) -> Result<Response<FileExistsResponse>, Status> {
        let path = &request.get_ref().path;

        match self.file_executor.file_exists(path) {
            Ok(exists) => {
                Ok(Response::new(FileExistsResponse {
                    success: true,
                    exists,
                    error: String::new(),
                }))
            }
            Err(e) => {
                Ok(Response::new(FileExistsResponse {
                    success: false,
                    exists: false,
                    error: e.to_string(),
                }))
            }
        }
    }

    async fn get_file_info(
        &self,
        request: Request<FileInfoRequest>,
    ) -> Result<Response<FileInfoResponse>, Status> {
        let path = &request.get_ref().path;

        match self.file_executor.get_file_info(path) {
            Ok(info) => {
                Ok(Response::new(FileInfoResponse {
                    success: true,
                    size: info.size,
                    is_dir: info.is_dir,
                    is_file: info.is_file,
                    readonly: info.readonly,
                    error: String::new(),
                }))
            }
            Err(e) => {
                Ok(Response::new(FileInfoResponse {
                    success: false,
                    size: 0,
                    is_dir: false,
                    is_file: false,
                    readonly: false,
                    error: e.to_string(),
                }))
            }
        }
    }

    async fn execute_command(
        &self,
        request: Request<CommandRequest>,
    ) -> Result<Response<CommandResponse>, Status> {
        let req = request.get_ref();
        let command = if req.args.is_empty() {
            req.command.clone()
        } else {
            format!("{} {}", req.command, req.args.join(" "))
        };

        info!("ExecuteCommand request: {}", command);

        match self.system_executor.execute_command(&command).await {
            Ok(result) => {
                info!("Command execution successful: exit_code={}", result.exit_code);
                Ok(Response::new(CommandResponse {
                    success: result.success,
                    stdout: result.stdout,
                    stderr: result.stderr,
                    exit_code: result.exit_code,
                    error: String::new(),
                }))
            }
            Err(e) => {
                error!("Command execution error: {}", e);
                Ok(Response::new(CommandResponse {
                    success: false,
                    stdout: String::new(),
                    stderr: String::new(),
                    exit_code: -1,
                    error: e.to_string(),
                }))
            }
        }
    }

    async fn get_working_directory(
        &self,
        _request: Request<EmptyRequest>,
    ) -> Result<Response<DirectoryResponse>, Status> {
        match self.system_executor.get_working_directory() {
            Ok(path) => {
                Ok(Response::new(DirectoryResponse {
                    success: true,
                    path,
                    error: String::new(),
                }))
            }
            Err(e) => {
                Ok(Response::new(DirectoryResponse {
                    success: false,
                    path: String::new(),
                    error: e.to_string(),
                }))
            }
        }
    }

    async fn get_environment_variable(
        &self,
        request: Request<EnvVarRequest>,
    ) -> Result<Response<EnvVarResponse>, Status> {
        let name = &request.get_ref().name;

        match self.system_executor.get_environment_variable(name) {
            Ok(value) => {
                Ok(Response::new(EnvVarResponse {
                    success: true,
                    value,
                    error: String::new(),
                }))
            }
            Err(e) => {
                Ok(Response::new(EnvVarResponse {
                    success: false,
                    value: String::new(),
                    error: e.to_string(),
                }))
            }
        }
    }
}
