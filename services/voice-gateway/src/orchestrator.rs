use tokio::sync::mpsc;
use anyhow::Result;
use tracing::{info, debug, error};

use crate::wake_word::WakeWordDetector;
use crate::audio::{AudioStream, AudioProcessor};

pub struct VoiceOrchestrator {
    detector: WakeWordDetector,
    audio_stream: AudioStream,
    processor: AudioProcessor,
    is_listening: bool,
}

impl VoiceOrchestrator {
    pub fn new(keyword_path: &str) -> Result<Self> {
        let detector = WakeWordDetector::new(keyword_path, 0.5)?;
        let audio_stream = AudioStream::new()?;
        let frame_length = detector.frame_length();
        let processor = AudioProcessor::new(frame_length);

        Ok(Self {
            detector,
            audio_stream,
            processor,
            is_listening: false,
        })
    }

    /// Main voice loop: wake-word → transcription → response
    pub async fn start(&mut self) -> Result<()> {
        let (audio_tx, mut audio_rx) = mpsc::channel(1000);

        // Start audio capture
        let _stream = self.audio_stream.start_capture(audio_tx)?;

        info!("🎙️  Listening for wake word...");
        info!("Sample rate: {}Hz", self.audio_stream.sample_rate());
        info!("Channels: {}", self.audio_stream.channels());

        while let Some(audio_chunk) = audio_rx.recv().await {
            // Add samples to processor
            self.processor.add_samples(&audio_chunk);

            // Process frames
            while let Some(frame) = self.processor.next_frame() {
                if !self.is_listening {
                    // Check for wake word
                    if self.detector.process_frame(&frame)? {
                        info!("🔊 Wake word detected!");
                        self.is_listening = true;
                        self.processor.clear();

                        // TODO: Start STT streaming
                        info!("Starting speech transcription...");

                        // TODO: Connect to STT service via gRPC
                        // let stt_client = STTServiceClient::connect("http://stt-service:50052").await?;
                        // Stream audio to STT...

                        // For now, simulate listening for 3 seconds
                        tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;

                        info!("Transcription complete");
                        self.is_listening = false;

                        info!("🎙️  Listening for wake word...");
                    }
                } else {
                    // Currently transcribing
                    debug!("Transcribing audio frame...");

                    // TODO: Send frame to STT service
                    // stt_client.stream_audio(frame).await?;
                }
            }
        }

        Ok(())
    }

    pub fn is_listening(&self) -> bool {
        self.is_listening
    }
}
