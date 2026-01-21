use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Device, Stream, StreamConfig, SampleFormat};
use tokio::sync::mpsc;
use anyhow::{Result, anyhow};
use tracing::{info, error};

pub struct AudioStream {
    device: Device,
    config: StreamConfig,
}

impl AudioStream {
    pub fn new() -> Result<Self> {
        let host = cpal::default_host();
        info!("Audio host: {}", host.id().name());

        let device = host
            .default_input_device()
            .ok_or_else(|| anyhow!("No input device available"))?;

        info!("Input device: {}", device.name()?);

        let config = device.default_input_config()?;
        info!("Default input config: {:?}", config);

        Ok(Self {
            device,
            config: config.into(),
        })
    }

    /// Start capturing audio and send to channel
    pub fn start_capture(&self, tx: mpsc::Sender<Vec<i16>>) -> Result<Stream> {
        let config = self.config.clone();
        let tx = tx.clone();

        info!("Starting audio capture...");

        let stream = self.device.build_input_stream(
            &config,
            move |data: &[i16], _: &cpal::InputCallbackInfo| {
                let tx = tx.clone();
                let audio_data = data.to_vec();

                // Send audio data to processing channel
                tokio::spawn(async move {
                    if let Err(e) = tx.send(audio_data).await {
                        error!("Failed to send audio data: {}", e);
                    }
                });
            },
            |err| {
                error!("Audio stream error: {}", err);
            },
            None,
        )?;

        stream.play()?;
        info!("Audio capture started");

        Ok(stream)
    }

    pub fn sample_rate(&self) -> u32 {
        self.config.sample_rate.0
    }

    pub fn channels(&self) -> u16 {
        self.config.channels
    }
}

impl Default for AudioStream {
    fn default() -> Self {
        Self::new().expect("Failed to create audio stream")
    }
}
