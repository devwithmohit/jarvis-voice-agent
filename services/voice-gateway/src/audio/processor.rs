use bytes::Bytes;
use tracing::debug;

/// Audio processor for format conversion and buffering
pub struct AudioProcessor {
    buffer: Vec<i16>,
    frame_size: usize,
}

impl AudioProcessor {
    pub fn new(frame_size: usize) -> Self {
        Self {
            buffer: Vec::new(),
            frame_size,
        }
    }

    /// Add audio samples to buffer
    pub fn add_samples(&mut self, samples: &[i16]) {
        self.buffer.extend_from_slice(samples);
    }

    /// Get next frame if available
    pub fn next_frame(&mut self) -> Option<Vec<i16>> {
        if self.buffer.len() >= self.frame_size {
            let frame = self.buffer.drain(..self.frame_size).collect();
            Some(frame)
        } else {
            None
        }
    }

    /// Convert i16 samples to bytes
    pub fn samples_to_bytes(samples: &[i16]) -> Bytes {
        let mut bytes = Vec::with_capacity(samples.len() * 2);
        for &sample in samples {
            bytes.extend_from_slice(&sample.to_le_bytes());
        }
        Bytes::from(bytes)
    }

    /// Convert bytes to i16 samples
    pub fn bytes_to_samples(bytes: &[u8]) -> Vec<i16> {
        bytes
            .chunks_exact(2)
            .map(|chunk| i16::from_le_bytes([chunk[0], chunk[1]]))
            .collect()
    }

    /// Clear buffer
    pub fn clear(&mut self) {
        self.buffer.clear();
        debug!("Audio buffer cleared");
    }

    /// Get buffer size
    pub fn buffer_size(&self) -> usize {
        self.buffer.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_processor() {
        let mut processor = AudioProcessor::new(512);

        // Add samples
        let samples = vec![100i16; 1024];
        processor.add_samples(&samples);

        assert_eq!(processor.buffer_size(), 1024);

        // Get frames
        let frame1 = processor.next_frame();
        assert!(frame1.is_some());
        assert_eq!(frame1.unwrap().len(), 512);

        let frame2 = processor.next_frame();
        assert!(frame2.is_some());
        assert_eq!(frame2.unwrap().len(), 512);

        let frame3 = processor.next_frame();
        assert!(frame3.is_none());
    }

    #[test]
    fn test_conversion() {
        let samples = vec![100i16, 200, 300, 400];
        let bytes = AudioProcessor::samples_to_bytes(&samples);
        let converted = AudioProcessor::bytes_to_samples(&bytes);

        assert_eq!(samples, converted);
    }
}
