use tonic::{transport::Server, Request, Response, Status};
use tracing::info;

// TODO: Implement gRPC server for voice gateway control
// This would include RPCs for:
// - Start/stop listening
// - Adjust wake-word sensitivity
// - Get status
// - Configure audio settings

pub struct VoiceGatewayServer {
    // Add fields as needed
}

impl VoiceGatewayServer {
    pub fn new() -> Self {
        Self {}
    }

    pub async fn serve(addr: &str) -> Result<(), Box<dyn std::error::Error>> {
        info!("Starting voice gateway gRPC server on {}", addr);

        // TODO: Implement gRPC service
        // let service = VoiceGatewayServicer::new();
        // Server::builder()
        //     .add_service(voice_gateway_server(service))
        //     .serve(addr.parse()?)
        //     .await?;

        Ok(())
    }
}

impl Default for VoiceGatewayServer {
    fn default() -> Self {
        Self::new()
    }
}
