use anyhow::Result;
use std::sync::Arc;
use tonic::transport::Server;
use tracing::{info, error};
use tracing_subscriber;

pub mod security;
pub mod executors;
pub mod grpc;

// Generated proto code
pub mod generated {
    tonic::include_proto!("tool");
}

use security::SecurityValidator;
use grpc::server::ToolExecutorService;
use generated::tool_executor_server::ToolExecutorServer;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    info!("Starting Tool Executor service...");

    // Load security configuration
    let config = security::load_config("config/security.yaml")?;
    let validator = Arc::new(SecurityValidator::from_config(config)?);

    info!("Security configuration loaded");
    info!("Allowed file extensions (read): {:?}", validator.get_allowed_read_extensions());
    info!("System commands enabled: {}", validator.is_commands_enabled());

    // Create gRPC service
    let service = ToolExecutorService::new(validator);

    // Start server
    let addr = "0.0.0.0:50055".parse()?;
    info!("Tool Executor gRPC server starting on {}", addr);

    Server::builder()
        .add_service(ToolExecutorServer::new(service))
        .serve(addr)
        .await?;

    info!("Tool Executor service stopped");

    Ok(())
}
