class AudioOutputProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.frames = [];
    this.offsetInFirstBuffer = 0;
    this.port.onmessage = (event) => {
      if (event.data.type === 'audio' && event.data.frame) {
        this.frames.push(event.data.frame);
      } else if (event.data.type === 'reset') {
        this.frames = [];
        this.offsetInFirstBuffer = 0;
      }
    };
  }

  process(inputs, outputs) {
    const output = outputs[0][0];
    let out_idx = 0;
    while (out_idx < output.length && this.frames.length) {
      const first = this.frames[0];
      const to_copy = Math.min(first.length - this.offsetInFirstBuffer, output.length - out_idx);
      const subArray = first.subarray(this.offsetInFirstBuffer, this.offsetInFirstBuffer + to_copy);
      output.set(subArray, out_idx);
      this.offsetInFirstBuffer += to_copy;
      out_idx += to_copy;
      if (this.offsetInFirstBuffer === first.length) {
        this.frames.shift();
        this.offsetInFirstBuffer = 0;
      }
    }
    // Fill the rest with silence if we run out of audio
    if (out_idx < output.length) {
      output.fill(0, out_idx);
    }
    return true;
  }
}

registerProcessor('audio-output-processor', AudioOutputProcessor); 