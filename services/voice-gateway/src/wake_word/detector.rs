use anyhow::{Result, anyhow};
use tracing::{info, debug};

/// Wake-word detection using simple energy-based detection
/// TODO: Replace with actual wake-word library (Porcupine, openWakeWord, etc.)
pub struct WakeWordDetector {
    keyword_path: String,
    sensitivity: f32,
    frame_length: usize,
    sample_rate: u32,
    energy_threshold: f32,
}

impl WakeWordDetector {
    pub fn new(keyword_path: &str, sensitivity: f32) -> Result<Self> {
        info!("Initializing wake-word detector");
        info!("Keyword path: {}", keyword_path);
        info!("Sensitivity: {}", sensitivity);

        // For now, use simple energy-based detection
        // In production, integrate Picovoice Porcupine or openWakeWord

        Ok(Self {
            keyword_path: keyword_path.to_string(),
            sensitivity,
            frame_length: 512,  // Frame size in samples
            sample_rate: 16000,
            energy_threshold: 0.02 * sensitivity,
        })
    }

    /// Process audio frame and detect wake word
    /// Returns true if wake word detected
    pub fn process_frame(&mut self, audio_frame: &[i16]) -> Result<bool> {
        if audio_frame.len() != self.frame_length {
            return Err(anyhow!(
                "Invalid frame length: expected {}, got {}",
                self.frame_length,
                audio_frame.len()
            ));
        }

        // Simple energy-based detection
        // TODO: Replace with actual wake-word model inference
        let energy = self.calculate_energy(audio_frame);

        if energy > self.energy_threshold {
            debug!("High energy detected: {:.4}", energy);

            // For demo purposes, consider high energy as wake word
            // In production, use actual wake-word model
            if energy > self.energy_threshold * 2.0 {
                info!("Wake word detected (energy-based)");
                return Ok(true);
            }
        }

        Ok(false)
    }

    /// Calculate audio energy (RMS)
    fn calculate_energy(&self, audio_frame: &[i16]) -> f32 {
        let sum_squares: f64 = audio_frame
            .iter()
            .map(|&sample| {
                let normalized = sample as f64 / 32768.0;
                normalized * normalized
            })
            .sum();

        (sum_squares / audio_frame.len() as f64).sqrt() as f32
    }

    pub fn frame_length(&self) -> usize {
        self.frame_length
    }

    pub fn sample_rate(&self) -> u32 {
        self.sample_rate
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detector_creation() {
        let detector = WakeWordDetector::new("./test.ppn", 0.5);
        assert!(detector.is_ok());
    }

    #[test]
    fn test_energy_calculation() {
        let mut detector = WakeWordDetector::new("./test.ppn", 0.5).unwrap();

        // Silent audio
        let silent_frame = vec![0i16; 512];
        let result = detector.process_frame(&silent_frame);
        assert!(result.is_ok());
        assert!(!result.unwrap());

        // Loud audio
        let loud_frame = vec![10000i16; 512];
        let result = detector.process_frame(&loud_frame);
        assert!(result.is_ok());
    }
}
