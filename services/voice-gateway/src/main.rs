use anyhow::Result;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{info, warn, error};

pub mod wake_word;
pub mod audio;
pub mod grpc;
pub mod orchestrator;

use orchestrator::VoiceOrchestrator;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    info!("Starting Voice Gateway...");

    // Initialize orchestrator
    let orchestrator = Arc::new(Mutex::new(
        VoiceOrchestrator::new("./keywords/jarvis.ppn")?
    ));

    info!("Voice Gateway initialized successfully");

    // Start voice processing loop
    let orchestrator_clone = Arc::clone(&orchestrator);
    tokio::spawn(async move {
        let mut orch = orchestrator_clone.lock().await;
        if let Err(e) = orch.start().await {
            error!("Voice orchestrator error: {}", e);
        }
    });

    // Start gRPC server
    // TODO: Implement gRPC server for voice gateway control
    info!("Voice Gateway ready on port 50054");

    // Keep running
    tokio::signal::ctrl_c().await?;
    info!("Shutting down Voice Gateway...");

    Ok(())
}
