import React, { useEffect, useState, useRef, RefObject } from 'react';
import './App.css';
import { getPatientProfile, getConversation, updatePatientProfile, updateConversation, PatientProfile, Conversation, getMemory, updateMemory, getLinks, updateLinks, getGeneral, updateGeneral, updateUpdates, getUpdates } from './db';
import OpusRecorder from 'opus-recorder';
// @ts-ignore
import msgpack from 'msgpack-lite';

// Type declaration for msgpack-lite if types are not available
declare module 'msgpack-lite' {
  export function decode(data: Uint8Array): any;
  export function encode(data: any): Uint8Array;
}

const LLAMA_ENDPOINT = 'http://localhost:5100/api/agent'; // Local backend endpoint
const LLAMA_STREAM_ENDPOINT = 'http://localhost:5100/api/agent/stream'; // New streaming endpoint
const UNMUTE_STT_ENDPOINT = 'ws://172.22.225.138:11004/api/asr-streaming'; // Direct STT endpoint

// === STT ADD-ON: Proxy endpoint for STT ===
const STT_PROXY_URL = 'ws://localhost:8080'; // STT proxy endpoint

function base64DecodeOpus(base64String: string): Uint8Array {
  const binaryString = window.atob(base64String);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

const audioQueueRef: { current: Blob[] } = { current: [] };
let lastAudioUrl: string | null = null;
let isPlaying = false;

function playNextAudio(audioPlayerRef: RefObject<HTMLAudioElement | null>) {
  if (isPlaying || audioQueueRef.current.length === 0 || !audioPlayerRef.current) return;
  const audioBlob = audioQueueRef.current.shift();
  if (!audioBlob) return;
  const audioEl = audioPlayerRef.current;
  if (lastAudioUrl) {
    URL.revokeObjectURL(lastAudioUrl);
    lastAudioUrl = null;
  }
  lastAudioUrl = URL.createObjectURL(audioBlob);
  audioEl.src = lastAudioUrl;
  isPlaying = true;
  audioEl.onended = () => {
    isPlaying = false;
    playNextAudio(audioPlayerRef);
  };
  audioEl.onpause = () => {
    isPlaying = false;
  };
  audioEl.oncanplaythrough = () => {
    audioEl.play().catch((e: any) => {
      console.error('Audio playback error:', e);
    });
    audioEl.oncanplaythrough = null; // Remove handler after first use
  };
}

// Streaming audio playback setup
let audioContext: AudioContext | null = null;
let audioWorkletNode: any = null;
let decoderWorker: Worker | null = null;

function setupStreamingAudio() {
  console.log('[DEBUG] setupStreamingAudio called');
  if (!audioContext) {
    audioContext = new window.AudioContext();
    (window as any).audioContext = audioContext; // Expose for debugging
    console.log('[DEBUG] audioContext created and assigned to window:', audioContext);
  }
  if (!audioWorkletNode) {
    audioContext.audioWorklet
      .addModule('/audio-output-processor.js')
      .then(() => {
        audioWorkletNode = new window.AudioWorkletNode(audioContext!, 'audio-output-processor');
        audioWorkletNode.connect(audioContext!.destination);
        console.log('[DEBUG] AudioWorkletNode created and connected:', audioWorkletNode);
      });
  }
  if (!decoderWorker) {
    decoderWorker = new Worker('/decoderWorker.min.js');
    decoderWorker.onmessage = (event: MessageEvent) => {
      if (!audioWorkletNode) {
        console.log('[DEBUG] PCM frame received but AudioWorkletNode not ready');
        return;
      }
      if (event.data && event.data[0]) {
        console.log('[DEBUG] PCM frame received from decoder:', event.data[0]);
        audioWorkletNode.port.postMessage({ frame: event.data[0], type: 'audio', micDuration: 0 });
      } else {
        console.log('[DEBUG] Decoder worker message with no frame:', event.data);
      }
    };
    decoderWorker.postMessage({
      command: 'init',
      bufferLength: 960, // 20ms at 48kHz
      decoderSampleRate: 24000,
      outputBufferSampleRate: 48000,
      resampleQuality: 0,
    });
  }
}

// Track received chunk types for streaming state management
const receivedChunkTypesRef = { current: new Set<string>() };

// Streaming chunk handler for new API
function handleStreamingChunk(chunk: any, setConversation: any, updateConversation: any, setProfile: any, updatePatientProfile: any, setLinks: any, setGeneral: any, setUpdates: any, setStreamingText: any, setIsStreaming: any, setStreamingError: any, setStreamingStatus: any, setLoading: any) {
  console.log('[DEBUG] Streaming chunk received:', chunk);
  console.log('[DEBUG] Chunk type:', chunk.type);
  console.log('[DEBUG] Chunk data:', chunk.data);
  console.log('[DEBUG] Chunk data type:', typeof chunk.data);
  console.log('[DEBUG] Chunk data keys:', chunk.data ? Object.keys(chunk.data) : 'null');
  
  // Track this chunk type
  receivedChunkTypesRef.current.add(chunk.type);
  console.log('[DEBUG] Received chunk types so far:', Array.from(receivedChunkTypesRef.current));
  
  switch (chunk.type) {
    case 'streaming_started':
      console.log('Agent processing started:', chunk.data.message);
      setStreamingStatus(chunk.data.message);
      setIsStreaming(true);
      setStreamingText('');
      setStreamingError(null);
      // Reset chunk type tracking for new streaming session
      receivedChunkTypesRef.current.clear();
      console.log('[DEBUG] Reset chunk type tracking for new streaming session');
      break;
      
    case 'unmute_connecting':
      console.log('Connecting to voice assistant...');
      setStreamingStatus('Connecting to voice assistant...');
      // Reset chunk type tracking for new Unmute connection
      receivedChunkTypesRef.current.clear();
      console.log('[DEBUG] Reset chunk type tracking for new Unmute connection');
      break;
      
    case 'unmute_connected':
      console.log('Connected to voice assistant');
      setStreamingStatus('Connected to voice assistant');
      break;
      
    case 'unmute_streaming_started':
      console.log('Voice assistant is responding...');
      setStreamingStatus('Voice assistant is responding...');
      break;
      
    case 'text_chunk':
      // Handle real-time text chunks from Unmute
      const textChunk = chunk.data.text;
      console.log('Text chunk:', textChunk);
      
      // Add to streaming text buffer
      setStreamingText((prev: string) => prev + textChunk);
      
      // Update conversation in real-time
      setConversation((prev: Conversation | null) => {
        if (!prev) return prev;
        const lastMsg = prev.conversation[prev.conversation.length - 1];
        if (lastMsg && lastMsg.sender === 'ai') {
          // Update last assistant message
          const updated = {
            ...prev,
            cid: prev.cid || 'conv-001',
            conversation: [
              ...prev.conversation.slice(0, -1),
              { ...lastMsg, text: lastMsg.text + textChunk }
            ]
          };
          updateConversation(updated);
          return updated;
        } else {
          // Start new assistant message
          const updated = {
            ...prev,
            cid: prev.cid || 'conv-001',
            conversation: [...prev.conversation, { sender: 'ai' as 'ai', text: textChunk }]
          };
          updateConversation(updated);
          return updated;
        }
      });
      break;
      
    case 'audio_chunk':
      // Handle real-time audio chunks from Unmute
      const audioChunk = chunk.data.audio;
      console.log('Audio chunk received:', audioChunk.length, 'bytes');
      
      // Decode base64 audio and stream to player
      const audioData = base64DecodeOpus(audioChunk);
      setupStreamingAudio();
      if (decoderWorker) {
        decoderWorker.postMessage({ command: 'decode', pages: audioData }, [audioData.buffer]);
      }
      break;
      
    case 'text_complete':
      console.log('Text response complete');
      setStreamingStatus('Text response complete');
      break;
      
    case 'audio_complete':
      console.log('Audio response complete');
      setStreamingStatus('Audio response complete');
      break;
      
    case 'unmute_complete':
      console.log('Voice assistant response complete');
      setStreamingStatus('Voice assistant response complete');
      
      // Check if final_result has also been received before clearing streaming state
      const hasFinalResult = receivedChunkTypesRef.current.has('final_result');
      console.log('[DEBUG] unmute_complete received. Has final_result:', hasFinalResult);
      
      if (hasFinalResult) {
        console.log('[DEBUG] Both unmute_complete and final_result received, clearing streaming state');
        // Clear streaming state
        setIsStreaming(false);
        setStreamingText('');
        setStreamingStatus('');
        setLoading(false);
        
        // Clean up streaming connection
        if ((window as any).cleanupStreaming) {
          (window as any).cleanupStreaming();
          (window as any).cleanupStreaming = null;
        }
        
        // Reset chunk type tracking
        receivedChunkTypesRef.current.clear();
      } else {
        console.log('[DEBUG] unmute_complete received but final_result not yet received, keeping streaming state active');
      }
      break;
      
    // case 'workflow_complete':
    //   // Handle workflow completion from agent
    //   console.log('Agent workflow complete');
    //   const workflowResult = chunk.data;
    //   console.log('[DEBUG] workflow_complete - workflowResult:', workflowResult);
    //   console.log('[DEBUG] workflow_complete - workflowResult.result:', workflowResult.result);
    //   console.log('[DEBUG] workflow_complete - workflowResult.result?.patientProfile:', workflowResult.result?.patientProfile);
      
    //   if (workflowResult.result && workflowResult.result.patientProfile) {
    //     console.log('[DEBUG] Updating profile from workflow_complete:', workflowResult.result.patientProfile);
    //     setProfile(workflowResult.result.patientProfile);
    //     updatePatientProfile(workflowResult.result.patientProfile);
    //   }
    //   if (workflowResult.result && workflowResult.result.memory) {
    //     updateMemory(workflowResult.result.memory);
    //   }
    //   if (workflowResult.result && workflowResult.result.links) {
    //     setLinks(workflowResult.result.links);
    //   }
    //   if (workflowResult.result && workflowResult.result.general) {
    //     setGeneral(workflowResult.result.general);
    //   }
    //   if (workflowResult.result && workflowResult.result.updates) {
    //     console.log('[DEBUG] Updating updates from workflow_complete:', workflowResult.result.updates);
    //     // Append new updates to existing ones
    //     setUpdates((prevUpdates: any) => {
    //       const existingUpdates = prevUpdates || [];
    //       const newUpdates = workflowResult.result.updates;
    //       return [...existingUpdates, ...newUpdates];
    //     });
    //     updateUpdates(workflowResult.result.updates);
    //   }
      
    //   // Don't clear streaming state here - let the audio response to continue streaming
    //   // This allows the audio response to continue streaming
    //   break;
      
    case 'final_result':
      // Handle final result from agent workflow
      console.log('Agent processing complete');
      const result = chunk.data;
      console.log('[DEBUG] final_result - result:', result);
      console.log('[DEBUG] final_result - result.updatedPatientProfile:', result.updatedPatientProfile);
      
      if (result.updatedPatientProfile) {
        console.log('[DEBUG] Updating profile from final_result:', result.updatedPatientProfile);
        setProfile(result.updatedPatientProfile);
        updatePatientProfile(result.updatedPatientProfile);
      }
      if (result.updatedMemory) {
        updateMemory(result.updatedMemory);
      }
      if (result.links) {
        setLinks(result.links);
      }
      if (result.general) {
        setGeneral(result.general);
      }
      if (result.Updates) {
        console.log('[DEBUG] Updating updates from final_result:', result.Updates);
        // Append new updates to existing ones
        setUpdates((prevUpdates: any) => {
          const existingUpdates = prevUpdates || [];
          const newUpdates = result.Updates;
          return [...existingUpdates, ...newUpdates];
        });
        updateUpdates(result.Updates);
      }
      if (result.function){
        console.log('[DEBUG] Updating function from final_result:', result.function);
        (window as any).processUICommand(result.function);
      }
      
      // Check if unmute_complete has also been received before clearing streaming state
      const hasUnmuteComplete = receivedChunkTypesRef.current.has('unmute_complete');
      console.log('[DEBUG] final_result received. Has unmute_complete:', hasUnmuteComplete);
      
      if (hasUnmuteComplete) {
        console.log('[DEBUG] Both final_result and unmute_complete received, clearing streaming state');
        // Clear streaming state
        setIsStreaming(false);
        setStreamingText('');
        setStreamingStatus('');
        setLoading(false);
        
        // Clean up streaming connection
        if ((window as any).cleanupStreaming) {
          (window as any).cleanupStreaming();
          (window as any).cleanupStreaming = null;
        }
        
        // Reset chunk type tracking
        receivedChunkTypesRef.current.clear();
      } else {
        console.log('[DEBUG] final_result received but unmute_complete not yet received, keeping streaming state active');
      }
      break;
      
    case 'error':
    case 'unmute_error':
    case 'unmute_timeout':
    case 'workflow_error':
      console.error('Error:', chunk.data.error || chunk.data.message);
      setStreamingError(chunk.data.error || chunk.data.message);
      setIsStreaming(false);
      setStreamingText('');
      setStreamingStatus('');
      setLoading(false);
      
      // Clean up streaming connection
      if ((window as any).cleanupStreaming) {
        (window as any).cleanupStreaming();
        (window as any).cleanupStreaming = null;
      }
      break;
      
    case 'keepalive':
      // Handle keepalive messages
      console.log('Keepalive received');
      break;
      
    default:
      console.log('Unknown streaming chunk type:', chunk.type);
  }
}

const App: React.FC = () => {
  const [input, setInput] = useState('');
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  // --- Add state for links, general, and updates ---
  const [links, setLinks] = useState<Record<string, any> | null>(null);
  const [general, setGeneral] = useState<any | null>(null);
  const [updates, setUpdates] = useState<any | null>(null);
  const [audioMode, setAudioMode] = useState(false);
  
  // --- Add streaming state variables ---
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingError, setStreamingError] = useState<string | null>(null);
  const [streamingStatus, setStreamingStatus] = useState<string>('');
  
  // --- Add UI state variables ---
  const [darkMode, setDarkMode] = useState(false);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const audioChunksRef = useRef<Uint8Array[]>([]);
  const recorderRef = useRef<any>(null);
  // Track if a new user message was just added
  const justAddedUserMessageRef = { current: false };
  // (Reverted) No transcription buffer
  // Buffer for streaming transcription (audio only)
  const transcriptionBufferRef = useRef<string>("");
  const flushTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isRecordingRef = useRef(false);
  const profileRef = useRef<PatientProfile | null>(null);
  
  // === STT ADD-ON: STT-related state and refs ===
  const [speechDetected, setSpeechDetected] = useState(false);  // Track when speech is detected
  const sttWsRef = useRef<WebSocket | null>(null);  // Direct STT WebSocket
  // Track sentence buffer and timing
  const currentSentenceBufferRef = useRef<string>("");
  const sentenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const conversationRef = useRef<Conversation | null>(null);
  
  // Keep conversation ref in sync with state
  useEffect(() => {
    conversationRef.current = conversation;
  }, [conversation]);
  useEffect(() => {
    profileRef.current = profile;
    console.log('[DEBUG] profileRef.current updated:', profileRef.current);
  }, [profile]);

  // === STT ADD-ON: Cleanup STT connection on component unmount ===
  useEffect(() => {
    return () => {
      // Cleanup STT WebSocket connection when component unmounts
      closeSTTConnection();
    };
  }, []);

  useEffect(() => {
    console.log('[DEBUG] General state changed:', general);
  }, [general]);

  useEffect(() => {
    // Initialize database with sample data first
    import('./db').then(({ initializeSampleData }) => {
      initializeSampleData().then(() => {
        console.log('[DEBUG] Database initialized with sample data');
        
        // Now load the data
        getPatientProfile().then(result => {
          console.log('[DEBUG] setProfile called with (initial load):', result ?? null);
          setProfile(result ?? null);
        });
        getConversation().then(result => setConversation(result ?? null));
        getLinks().then(result => {
          console.log('[DEBUG] setLinks called with (initial load):', result?.links ?? null);
          setLinks(result?.links ?? null);
        });
        getGeneral().then(result => {
          console.log('[DEBUG] setGeneral called with (initial load):', result?.general ?? null);
          setGeneral(result?.general ?? null);
        });
        getUpdates().then(result => {
          console.log('[DEBUG] setUpdates called with (initial load):', result?.updates ?? null);
          setUpdates(result?.updates ?? null);
        });
      }).catch(error => {
        console.error('[DEBUG] Database initialization error:', error);
      });
    });
  }, []);

  // Loading timeout reference for streaming
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // === STT ADD-ON: STT WebSocket connection management ===
  // Remove the automatic WebSocket connection - we'll create it on demand
  
  // Function to create and setup STT WebSocket connection
  const createSTTConnection = () => {
    if (sttWsRef.current && sttWsRef.current.readyState === WebSocket.OPEN) {
      console.log('[DEBUG] STT WebSocket already connected');
      return;
    }
    
    console.log('[DEBUG] Creating new STT WebSocket connection');
    const sttWs = new window.WebSocket(STT_PROXY_URL);
    sttWsRef.current = sttWs;
    
    sttWs.onopen = () => {
      console.log('[DEBUG] STT WebSocket connected');
      // Try sending authentication token as a message
      try {
        const authMessage = {
          type: "Auth",
          token: "public_token"
        };
        const encoded = msgpack.encode(authMessage);
        sttWs.send(encoded);
        console.log('[DEBUG] Sent authentication message');
      } catch (e) {
        console.log('[DEBUG] Could not send auth message:', e);
      }
    };
    
    sttWs.onmessage = (event) => {
      try {
        // STT uses MessagePack format
        let data;
        if (event.data instanceof Blob) {
          // Handle binary MessagePack data
          event.data.arrayBuffer().then(buffer => {
            try {
              const uint8Array = new Uint8Array(buffer);
              data = msgpack.decode(uint8Array);
              console.log('[DEBUG] STT MessagePack decoded:', data);
              handleSTTMessage(data);
            } catch (e) {
              console.error('[DEBUG] Failed to decode MessagePack:', e);
            }
          });
        } else {
          // Handle text messages (if any)
          console.log('[DEBUG] STT text message:', event.data);
        }
      } catch (e: any) {
        console.error('STT WebSocket message handling error:', e);
      }
    };
    
    sttWs.onerror = (error) => {
      console.error('[DEBUG] STT WebSocket error:', error);
    };
    
    sttWs.onclose = () => {
      console.log('[DEBUG] STT WebSocket closed');
      sttWsRef.current = null;
    };
  };
  
  // Function to close STT WebSocket connection
  const closeSTTConnection = () => {
    if (sttWsRef.current && sttWsRef.current.readyState === WebSocket.OPEN) {
      console.log('[DEBUG] Closing STT WebSocket connection');
      sttWsRef.current.close();
      sttWsRef.current = null;
    }
  };

  // === STT ADD-ON: Handle STT messages - detect sentence completion and send to LLM ===
  const handleSTTMessage = (data: any) => {
    console.log('[DEBUG] Processing STT message:', data);
    console.log('[DEBUG] Message type:', data.type);
    console.log('[DEBUG] Full message data:', JSON.stringify(data, null, 2));
    
    if (data.type === 'Word' && data.text) {
      // Clear any existing sentence timeout
      if (sentenceTimeoutRef.current) {
        clearTimeout(sentenceTimeoutRef.current);
        sentenceTimeoutRef.current = null;
      }
      
      // Add word to sentence buffer
      currentSentenceBufferRef.current += (currentSentenceBufferRef.current ? ' ' : '') + data.text;
      
      // Don't add to conversation display yet - wait for sentence completion
      
      // Set timeout to detect sentence completion and send to LLM
      sentenceTimeoutRef.current = setTimeout(() => {
        const completedSentence = currentSentenceBufferRef.current.trim();
        if (completedSentence && profileRef.current && conversationRef.current) {
          console.log('[DEBUG] Sentence completed, sending to LLM:', completedSentence);
          
          // Close STT WebSocket connection before sending to workflow
          closeSTTConnection();
          
          // Add completed sentence to conversation display
          setConversation(prev => {
            if (!prev) return prev;
            const updated = {
              ...prev,
              conversation: [...prev.conversation, { sender: 'user' as 'user', text: completedSentence }]
            };
            updateConversation(updated);
            return updated;
          });
          
          // Send to LLM using existing handleSendPrompt function
          handleSendPrompt(completedSentence);
          
          // Clear buffer
          currentSentenceBufferRef.current = "";
        } else if (completedSentence) {
          console.log('[DEBUG] Sentence completed but profile/conversation not ready, retrying in 1 second');
          // Retry in 1 second if profile/conversation not ready
          setTimeout(() => {
            if (profileRef.current && conversationRef.current) {
              // Close STT WebSocket connection before sending to workflow
              closeSTTConnection();
              
              // Add completed sentence to conversation display
              setConversation(prev => {
                if (!prev) return prev;
                const updated = {
                  ...prev,
                  conversation: [...prev.conversation, { sender: 'user' as 'user', text: completedSentence }]
                };
                updateConversation(updated);
                return updated;
              });
              
              handleSendPrompt(completedSentence);
              currentSentenceBufferRef.current = "";
            }
          }, 1000);
        }
      }, 2000); // 2 seconds timeout
      
      console.log('[DEBUG] STT Word added to conversation:', data.text);
      setSpeechDetected(true);
      
    } else if (data.type === 'Marker') {
      // Ignore markers (like Unmute backend does)
      console.log('[DEBUG] STT Marker received - ignoring');
      
    } else if (data.type === 'EndWord') {
      console.log('[DEBUG] STT Word ended at time:', data.stop_time);
      
    } else if (data.type === 'Step') {
      // Just log step data for debugging
      console.log('[DEBUG] STT Step received:', data.step_idx, 'pause prediction:', data.prs);
      
      // Check if speech has stopped (for UI feedback only)
      if (data.prs && data.prs.length > 0) {
        const pausePrediction = data.prs[0];
        if (pausePrediction > 0.95) {
          setSpeechDetected(false);
        }
      }
      
    } else if (data.type === 'Ready') {
      console.log('[DEBUG] STT Ready message received');
    } else if (data.type === 'Error') {
      console.error('[DEBUG] STT Error:', data.message);
    } else {
      console.log('[DEBUG] Unknown message type:', data.type);
    }
  };

  // Send text input as a message
  const handleSendPrompt = async (prompt: string, options: { updates?: any, links?: any[], general?: any } = {}) => {
    // console.log('handleSendPrompt called', {
    //   hasProfile: !!profile,
    //   hasConversation: !!conversation,
    //   prompt
    // });
    // if (!profile || !conversation) {
    //   console.log('Not sending: missing profile or conversation', {
    //     hasProfile: !!profile,
    //     hasConversation: !!conversation
    //   });
    //   return;
    // }
    // setLoading(true);
    // const updatedConv = { 
    //   ...conversation, 
    //   cid: conversation.cid || 'conv-001', // Ensure cid exists
    //   conversation: [...conversation.conversation, { sender: 'user' as 'user', text: prompt }] 
    // };
    // setConversation(updatedConv);
    // await updateConversation(updatedConv);
    
    // Set a timeout to prevent loading state from getting stuck
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }
    loadingTimeoutRef.current = setTimeout(() => {
      console.log('[DEBUG] Loading timeout reached, setting loading to false');
      setLoading(false);
    }, 30000); // 30 second timeout
    
    // Send to Llama via new streaming API
    await sendPromptToLlamaStream(prompt, options);
    setInput('');
    // Don't set loading to false here - let the streaming response completion handle it
  };



  // === STT ADD-ON: Audio recording logic using Web Audio API for raw PCM ===
  const handleAudioRecord = async () => {
    if (recording) {
      // Stop Web Audio API recording
      if (recorderRef.current) {
        const processor = recorderRef.current as any;
        if (processor.disconnect) {
          processor.disconnect();
        }
      }
      setRecording(false);
      setSpeechDetected(false);
      
      // Close STT WebSocket connection when manually stopping recording
      closeSTTConnection();
      return;
    }
    try {
      // Create STT WebSocket connection when recording starts
      createSTTConnection();
      
      // Use Web Audio API to get raw PCM data
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioContext = new AudioContext({ sampleRate: 24000 });
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(1024, 1, 1);
      
      processor.onaudioprocess = (event) => {
        if (sttWsRef.current && sttWsRef.current.readyState === 1) {
          // Get raw PCM data
          const inputData = event.inputBuffer.getChannelData(0);
          const pcmData = Array.from(inputData); // Convert to regular array
          
          // Send PCM data to STT
          const message = {
            type: 'Audio',
            pcm: pcmData
          };
          const encoded = msgpack.encode(message);
          sttWsRef.current.send(encoded);
          console.log('Sent PCM data to STT, length:', pcmData.length);
        }
      };
      
      source.connect(processor);
      processor.connect(audioContext.destination);
      recorderRef.current = processor;
      setRecording(true);
      setSpeechDetected(true);
      
      const onEnded = () => {
        if (processor) {
          processor.disconnect();
          source.disconnect();
          stream.getTracks().forEach(track => track.stop());
        }
        setRecording(false);
        setSpeechDetected(false);
        
        // Close STT WebSocket connection when recording stops
        closeSTTConnection();
      };
      
      // Stop recording after 10 seconds or when user clicks again
      setTimeout(() => {
        if (recording) {
          onEnded();
        }
      }, 10000);
      
    } catch (error) {
      console.error('Audio recording error:', error);
      alert('Audio recording error');
    }
  };

  useEffect(() => {
    if (!audioPlayerRef.current) return;
    const audioEl = audioPlayerRef.current;
    const onEnded = () => {
      if (audioPlayerRef.current) playNextAudio(audioPlayerRef);
    };
    audioEl.addEventListener('ended', onEnded);
    return () => {
      audioEl.removeEventListener('ended', onEnded);
    };
  }, []);

  // Function to send prompt to Llama
  // Function to process UI commands from Llama
  const processUICommand = (command: string) => {
    console.log('[DEBUG] Processing UI command:', command);
    
    if (command.startsWith('setMode(') && command.endsWith(')')) {
      const mode = command.slice(8, -1); // Extract value between parentheses
      if (mode === 'dark') {
        if (darkMode) {
          console.log('[DEBUG] Dark mode already set, skipping');
        } else {
          setDarkMode(true);
          console.log('[DEBUG] Set dark mode: true');
        }
      } else if (mode === 'light') {
        if (!darkMode) {
          console.log('[DEBUG] Light mode already set, skipping');
        } else {
          setDarkMode(false);
          console.log('[DEBUG] Set dark mode: false');
        }
      }
    }
    
    if (command.startsWith('addFitness(') && command.endsWith(')')) {
      console.log('[DEBUG] Adding fitness treatment');
      addFitnessTreatment();
    }
    
    if (command.startsWith('removeFitness(') && command.endsWith(')')) {
      console.log('[DEBUG] Removing fitness treatment');
      removeFitnessTreatment();
    }
    
    if (command.startsWith('addSleep(') && command.endsWith(')')) {
      console.log('[DEBUG] Adding sleep treatment');
      addSleepTreatment();
    }
    
    if (command.startsWith('removeSleep(') && command.endsWith(')')) {
      console.log('[DEBUG] Removing sleep treatment');
      removeSleepTreatment();
    }
  };

  // Function to add fitness treatment
  const addFitnessTreatment = async () => {
    if (!profile) {
      console.log('[DEBUG] Cannot add fitness treatment: no profile available');
      return;
    }
    
    // Check if fitness treatment already exists
    const fitnessExists = profile.treatment.some(treatment => treatment.name === 'Fitness');
    if (fitnessExists) {
      console.log('[DEBUG] Fitness treatment already exists, skipping add');
      return;
    }
    
    const fitnessTreatment = {
      name: 'Fitness',
      medicationList: [],
      dailyChecklist: ['Track calories', 'Track protein', 'Exercise 30 minutes'],
      appointment: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week from now
      recommendations: ['Stay hydrated', 'Eat balanced meals', 'Get adequate rest'],
      dailyCals: 2000,
      dailyProtein: 150
    };

    const updatedProfile = {
      ...profile,
      treatment: [...profile.treatment, fitnessTreatment]
    };

    setProfile(updatedProfile);
    updatePatientProfile(updatedProfile);
    console.log('[DEBUG] Added fitness treatment:', fitnessTreatment);
  };

  // Function to remove fitness treatment
  const removeFitnessTreatment = async () => {
    if (!profile) {
      console.log('[DEBUG] Cannot remove fitness treatment: no profile available');
      return;
    }
    
    // Check if fitness treatment exists
    const fitnessExists = profile.treatment.some(treatment => treatment.name === 'Fitness');
    if (!fitnessExists) {
      console.log('[DEBUG] Fitness treatment does not exist, skipping remove');
      return;
    }
    
    const updatedProfile = {
      ...profile,
      treatment: profile.treatment.filter(treatment => treatment.name !== 'Fitness')
    };

    setProfile(updatedProfile);
    updatePatientProfile(updatedProfile);
    console.log('[DEBUG] Removed fitness treatment');
  };

  // Function to add sleep treatment
  const addSleepTreatment = async () => {
    if (!profile) {
      console.log('[DEBUG] Cannot add sleep treatment: no profile available');
      return;
    }
    
    // Check if sleep treatment already exists
    const sleepExists = profile.treatment.some(treatment => treatment.name === 'Sleep');
    if (sleepExists) {
      console.log('[DEBUG] Sleep treatment already exists, skipping add');
      return;
    }
    
    const sleepTreatment = {
      name: 'Sleep',
      medicationList: ['Ibuprofen'],
      dailyChecklist: ['Take medication', 'Walk 30 minutes'],
      appointment: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week from now
      recommendations: ['Stay hydrated', 'Regular exercise'],
      sleepHours: 8,
      sleepQuality: 'Excellent'
    };

    const updatedProfile = {
      ...profile,
      treatment: [...profile.treatment, sleepTreatment]
    };

    setProfile(updatedProfile);
    updatePatientProfile(updatedProfile);
    console.log('[DEBUG] Added sleep treatment:', sleepTreatment);
  };

  // Function to remove sleep treatment
  const removeSleepTreatment = async () => {
    if (!profile) {
      console.log('[DEBUG] Cannot remove sleep treatment: no profile available');
      return;
    }
    
    // Check if sleep treatment exists
    const sleepExists = profile.treatment.some(treatment => treatment.name === 'Sleep');
    if (!sleepExists) {
      console.log('[DEBUG] Sleep treatment does not exist, skipping remove');
      return;
    }
    
    const updatedProfile = {
      ...profile,
      treatment: profile.treatment.filter(treatment => treatment.name !== 'Sleep')
    };

    setProfile(updatedProfile);
    updatePatientProfile(updatedProfile);
    console.log('[DEBUG] Removed sleep treatment');
  };

  // Make function globally accessible for testing
  (window as any).processUICommand = processUICommand;

  async function sendPromptToLlama(prompt: string, options: { updates?: any, links?: any[], general?: any } = {}) {
    console.log('[DEBUG] sendPromptToLlama called, profileRef.current:', profileRef.current, 'profile:', profile);
    if (!profileRef.current) {
      console.warn('[DEBUG] sendPromptToLlama: patientProfile is null');
      return;
    }
    const memory = await getMemory();
    console.log('[DEBUG] Sending to Llama:', { prompt, patientProfile: profileRef.current, memory });
    // --- Build request payload with required fields ---
    const requestBody: any = {
      prompt,
      patientProfile: profileRef.current,
      memory: memory || { id: 'memory', memory: [] }
    };
    if (options.updates) requestBody.updates = options.updates;
    // Note: conversation, links, general are accessed via local backend bridge
    fetch(LLAMA_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })
      .then(res => res.json())
      .then(data => {
        console.log('[DEBUG] Llama response:', data);
        if (data.updatedPatientProfile || data.patientProfile) {
          const newProfile = data.updatedPatientProfile || data.patientProfile;
          console.log('[DEBUG] setProfile called with (Llama/Unmute response):', newProfile);
          setProfile(newProfile);
          updatePatientProfile(newProfile);
        }
        if (data.updatedMemory || data.memory) {
          const newMemory = data.updatedMemory || data.memory;
          updateMemory(newMemory);
        }
        if (data.updates) {
          // handle updates if needed
          console.log('[DEBUG] Received updates from Llama:', data.updates);
        }
        if (data.links) {
          setLinks(data.links);
          console.log('[DEBUG] Received links from Llama:', data.links);
        }
        if (data.general) {
          setGeneral(data.general);
          console.log('[DEBUG] Received general from Llama:', data.general);
        }
        if (data.extraInfo) {
          console.log('[DEBUG] Received extraInfo from Llama:', data.extraInfo);
          // Note: No longer forwarding to Unmute WebSocket since we removed it
        }
      })
      .catch(err => console.error('[DEBUG] Llama error:', err));
  }

  // New streaming API function
  async function sendPromptToLlamaStream(prompt: string, options: { updates?: any, links?: any[], general?: any } = {}) {
    console.log('[DEBUG] sendPromptToLlamaStream called');
    if (!profileRef.current) {
      console.warn('[DEBUG] sendPromptToLlamaStream: patientProfile is null');
      return;
    }
    
    const memory = await getMemory();
    const requestBody: any = {
      prompt,
      patientProfile: profileRef.current,
      memory: memory || { id: 'memory', memory: [] }
    };
    if (options.updates) requestBody.updates = options.updates;

    try {
      // Use fetch with streaming response instead of EventSource
      const response = await fetch(LLAMA_STREAM_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Store cleanup function
      const cleanupTimeout = () => {
        reader.cancel();
      };
      (window as any).cleanupStreaming = cleanupTimeout;

      // Read streaming response
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('[DEBUG] Streaming complete');
          cleanupTimeout();
          break;
        }

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = line.slice(6); // Remove 'data: ' prefix
              if (data.trim()) {
                const parsedChunk = JSON.parse(data);
                handleStreamingChunk(
                  parsedChunk, 
                  setConversation, 
                  updateConversation, 
                  setProfile, 
                  updatePatientProfile, 
                  setLinks, 
                  setGeneral, 
                  setUpdates, 
                  setStreamingText, 
                  setIsStreaming, 
                  setStreamingError, 
                  setStreamingStatus, 
                  setLoading
                );
              }
            } catch (error) {
              console.error('[DEBUG] Error parsing streaming chunk:', error);
            }
          }
        }
      }

    } catch (error) {
      console.error('[DEBUG] Error setting up streaming:', error);
      setStreamingError('Failed to start streaming');
      setIsStreaming(false);
      setLoading(false);
    }
  }

  return (
    <div style={{
      maxWidth: 2000,
      margin: '0 auto',
      padding: 16,
      backgroundColor: darkMode ? '#1a1a1a' : '#ffffff',
      color: darkMode ? '#ffffff' : '#000000',
      minHeight: '100vh'
    }}>
      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
        {/* Left side - Chatbot */}
        <div style={{ flex: 1, maxWidth: 700 }}>
          <h2>AI Health Chatbot</h2>
          <div style={{
            minHeight: 300,
            background: darkMode ? '#2d2d2d' : '#f7f7f7',
            padding: 12,
            borderRadius: 8,
            marginBottom: 12
          }}>
            {conversation?.conversation.map((msg, idx) => (
              <div key={idx} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '8px 0' }}>
                <span style={{
                  display: 'inline-block',
                  background: msg.sender === 'user' ? '#3182ce' : (darkMode ? '#404040' : '#fff'),
                  color: msg.sender === 'user' ? '#fff' : (darkMode ? '#ffffff' : '#222'),
                  borderRadius: 16,
                  padding: '8px 14px',
                  maxWidth: '75%',
                }}>{msg.text}</span>
              </div>
            ))}
          </div>
          {/* Streaming status display */}
          {(isStreaming || streamingStatus || streamingError) && (
            <div style={{
              background: darkMode ? '#2d2d2d' : '#f0f8ff',
              padding: 8,
              borderRadius: 4,
              marginBottom: 8,
              border: darkMode ? '1px solid #404040' : '1px solid #ddd',
              fontSize: 12
            }}>
              {streamingError && (
                <div style={{ color: '#e53e3e', marginBottom: 4 }}>
                  ❌ Error: {streamingError}
                </div>
              )}
              {streamingStatus && (
                <div style={{ color: darkMode ? '#90cdf4' : '#3182ce', marginBottom: 4 }}>
                  🔄 {streamingStatus}
                </div>
              )}
              {isStreaming && (
                <div style={{ color: darkMode ? '#9ae6b4' : '#38a169' }}>
                  ⚡ Streaming in progress...
                </div>
              )}
            </div>
          )}
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={handleAudioRecord}
              disabled={loading || !profile}
              style={{ 
                background: recording ? '#e53e3e' : speechDetected ? '#f6ad55' : '#3182ce', 
                color: '#fff', 
                border: 'none', 
                borderRadius: '50%', 
                width: 40, 
                height: 40, 
                fontSize: 18 
              }}
              aria-label={recording ? 'Stop recording' : 'Record audio'}
            >
              {recording ? '■' : speechDetected ? '🎤' : '🎤'}
            </button>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && input.trim() && !loading) handleSendPrompt(input.trim()); }}
              disabled={loading}
              placeholder="Type your message..."
              style={{
                flex: 1,
                padding: '8px 12px',
                borderRadius: 16,
                border: '1px solid #ccc',
                backgroundColor: darkMode ? '#404040' : '#ffffff',
                color: darkMode ? '#ffffff' : '#000000'
              }}
            />
            <button onClick={() => input.trim() && !loading && handleSendPrompt(input.trim())} disabled={loading || !input.trim()} style={{ background: '#3182ce', color: '#fff', border: 'none', borderRadius: '50%', width: 40, height: 40, fontSize: 18 }}>
              ➤
            </button>
          </div>
        </div>
        {/* Right side - Patient Profile and other info */}
        <div style={{
          width: 750,
          flexShrink: 0,
          display: 'flex',
          gap: 12
        }}>
          <div style={{
            flex: 0.5
          }}>
            {/* Links, General */}
            <div style={{
              background: darkMode ? '#2d2d2d' : '#eef',
              padding: 12,
              borderRadius: 8,
              marginBottom: 12,
              border: darkMode ? '1px solid #404040' : 'none'
            }}>
              <h4>Links</h4>
              {links ? (
                <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', margin: 0, color: darkMode ? '#ffffff' : '#000000' }}>{JSON.stringify(links, null, 2)}</pre>
              ) : (
                <p style={{ fontSize: 12, color: darkMode ? '#999' : '#666', margin: 0, fontStyle: 'italic' }}>No links available</p>
              )}
            </div>
            <div style={{
              background: darkMode ? '#2d2d2d' : '#efe',
              padding: 12,
              borderRadius: 8,
              marginBottom: 12,
              border: darkMode ? '1px solid #404040' : 'none'
            }}>
              <h4>General</h4>
              {general ? (
                <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', margin: 0, color: darkMode ? '#ffffff' : '#000000' }}>{JSON.stringify(general, null, 2)}</pre>
              ) : (
                <p style={{ fontSize: 12, color: darkMode ? '#999' : '#666', margin: 0, fontStyle: 'italic' }}>No general information available</p>
              )}
            </div>
          </div>
          {/* Updates */}
          <div style={{
            flex: 0.7
          }}>
            <div style={{
              background: darkMode ? '#2d2d2d' : '#ffe',
              padding: 12,
              borderRadius: 8,
              marginBottom: 12,
              border: darkMode ? '1px solid #404040' : 'none'
            }}>
              <h4>Updates</h4>
              {updates ? (
                <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', margin: 0, color: darkMode ? '#ffffff' : '#000000' }}>{JSON.stringify(updates, null, 2)}</pre>
              ) : (
                <p style={{ fontSize: 12, color: darkMode ? '#999' : '#666', margin: 0, fontStyle: 'italic' }}>No updates available</p>
              )}
            </div>
          </div>
          {/* Patient Profile */}
          <div style={{
            flex: 1
          }}>
            {profile && (
              <div style={{
                background: darkMode ? '#2d2d2d' : '#eef',
                padding: 12,
                borderRadius: 8,
                marginBottom: 12,
                border: darkMode ? '1px solid #404040' : 'none'
              }}>
                <h4>Patient Profile</h4>
                <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', margin: 0, color: darkMode ? '#ffffff' : '#000000' }}>
                  {JSON.stringify(profile, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;