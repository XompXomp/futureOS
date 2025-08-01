import Dexie, { Table } from 'dexie';

export interface PatientProfile {
  uid: string;
  name: string;
  age: number;
  bloodType: string;
  allergies: string[];
  treatment: Array<{
    name: string;
    medicationList: string[];
    dailyChecklist: string[];
    appointment: string;
    recommendations: string[];
    sleepHours?: number;
    sleepQuality?: string;
    [key: string]: any; // for treatment-specific metrics
  }>;
}

export interface Conversation {
  cid: string;
  tags: string[];
  conversation: Array<{
    sender: 'user' | 'ai';
    text: string;
  }>;
}

export interface Memory {
  id: string; // always 'memory' for singleton
  memory: any; // array of objects with datetime and text
}

export interface Links {
  id: string; // always 'links' for singleton
  links: Record<string, any>;
}

export interface General {
  id: string; // always 'general' for singleton
  general: any;
}

export interface Updates {
  id: string; // always 'updates' for singleton
  updates: any;
}

class AppDB extends Dexie {
  patientProfile!: Table<PatientProfile, string>; // uid as primary key
  conversation!: Table<Conversation, string>; // cid as primary key
  memory!: Table<Memory, string>; // id as primary key
  links!: Table<Links, string>; // id as primary key
  general!: Table<General, string>; // id as primary key
  updates!: Table<Updates, string>; // id as primary key

  constructor() {
    super('AppDB');
    this.version(1).stores({
      patientProfile: 'uid',
      conversation: 'cid',
    });
    this.version(2).stores({
      memory: 'id',
    });
    this.version(3).stores({
      links: 'id',
      general: 'id',
    });
    this.version(4).stores({
      updates: 'id',
    });
  }
}

export const db = new AppDB();

// Memory DB functions
export async function getMemory() {
  return db.memory.get('memory');
}

export async function updateMemory(memory: Memory | any) {
  // Ensure memory has the correct structure
  const memoryObject = {
    id: 'memory',
    memory: Array.isArray(memory) ? memory : (memory?.memory || [])
  };
  return db.memory.put(memoryObject);
}

export async function addMemoryItem(item: object) {
  const memory = await getMemory();
  if (!memory) return;
  memory.memory.push(item);
  await updateMemory(memory);
}

// Links DB functions
export async function getLinks() {
  return db.links.get('links');
}

export async function updateLinks(links: Links) {
  return db.links.put(links);
}

// General DB functions
export async function getGeneral() {
  return db.general.get('general');
}

export async function updateGeneral(general: General) {
  return db.general.put(general);
}

// Updates DB functions
export async function getUpdates() {
  return db.updates.get('updates');
}

export async function updateUpdates(updates: Updates | any) {
  // Get existing updates first
  const existingUpdates = await db.updates.get('updates');
  const existingUpdatesArray = existingUpdates?.updates || [];
  
  // Prepare new updates to add
  const newUpdates = Array.isArray(updates) ? updates : (updates?.updates || []);
  
  // Combine existing and new updates
  const combinedUpdates = [...existingUpdatesArray, ...newUpdates];
  
  // Ensure updates has the correct structure
  const updatesObject = {
    id: 'updates',
    updates: combinedUpdates
  };
  return db.updates.put(updatesObject);
}

// Sample data initialization
export async function initializeSampleData() {
  // Import shared data if available
  const sharedData = (window as any).sharedData;
  
  const existingProfile = await db.patientProfile.toCollection().first();
  if (!existingProfile) {
    const profileData = sharedData?.sharedPatientProfile || {
      uid: 'user-001',
      name: 'Jane Smith',
      age: 29,
      bloodType: 'A-',
      allergies: ['Peanuts'],
      treatment: [
        {
          name: 'Sleep',
          medicationList: ['Ibuprofen'],
          dailyChecklist: ['Take medication', 'Walk 30 minutes'],
          appointment: '2024-08-15T09:00:00',
          recommendations: ['Stay hydrated', 'Regular exercise'],
          sleepHours: 8,
          sleepQuality: 'Excellent',
        }
      ],
    };
    await db.patientProfile.add(profileData);
  }
  const existingConversation = await db.conversation.toCollection().first();
  if (!existingConversation) {
    await db.conversation.add({
      cid: 'conv-001',
      tags: ['greeting'],
      conversation: [
        { sender: 'user', text: 'Hello' },
        { sender: 'ai', text: 'Hello, how can I help you today?' },
      ],
    });
  }
  // Always update memory with latest data from shared-data.js
  const memoryData = sharedData?.sharedMemory || {
    id: 'memory',
    memory: [
      {
        datetime: '01_07_25_09_00',
        text: "Patient said they can't sleep"
      },
      {
        datetime: '02_07_25_22_15',
        text: 'Wakes up multiple times'
      }
    ],
  };
  await db.memory.put(memoryData);
  // Only initialize links if they don't exist (don't overwrite server updates)
  const existingLinks = await db.links.get('links');
  if (!existingLinks) {
    const linksData = sharedData?.sharedLinks || {
      id: 'links',
      links: {
        Sleep: {
          'disturbed sleep': 0.6,
          'tired in morning': 0.3
        }
      },
    };
    await db.links.put(linksData);
  }
  // Only initialize general if it doesn't exist (don't overwrite server updates)
  const existingGeneral = await db.general.get('general');
  if (!existingGeneral) {
    const generalData = sharedData?.sharedGeneral || {
      id: 'general',
      general: {
        EmotionalCues: ["anxious", "tired"],
        Tone: "reflective",
        Engagement: "high",
        Hesitation: "minimal",
        NuancedFindings: ["User shows progress in managing stress"],
        trend_analysis: ""
      },
    };
    await db.general.put(generalData);
  }
  // Always update updates with latest data from shared-data.js
  const updatesData = sharedData?.sharedUpdates || {
    id: 'updates',
    updates: [
      {
        datetime: '01_07_25_09_00',
        text: 'Initial consultation - Patient reports sleep disturbances'
      },
      {
        datetime: '01_07_25_14_30',
        text: 'Sleep hours changed from 7 to 9 hours'
      },
      {
        datetime: '01_07_25_15_45',
        text: 'Sleep quality changed from Poor to Excellent'
      },
      {
        datetime: '02_07_25_10_15',
        text: 'Melatonin added to prescriptions'
      },
      {
        datetime: '02_07_25_11_20',
        text: 'Appointment scheduled for 2025-08-15T09:00:00'
      },
      {
        datetime: '02_07_25_16_30',
        text: 'Daily checklist updated: Added "Take melatonin 30 min before bed"'
      },
      {
        datetime: '03_07_25_08_45',
        text: 'Patient reported improved sleep quality - reduced wake-ups from 5 to 2 times per night'
      },
      {
        datetime: '03_07_25_12_00',
        text: 'New recommendation added: "Avoid caffeine after 2 PM"'
      },
      {
        datetime: '03_07_25_14_20',
        text: 'Sleep tracking enabled - monitoring sleep patterns'
      },
      {
        datetime: '04_07_25_09_30',
        text: 'Follow-up appointment scheduled for 2025-08-22T10:00:00'
      },
      {
        datetime: '04_07_25_16_45',
        text: 'Sleep hygiene recommendations updated: Added "Keep bedroom temperature at 65-67°F"'
      },
      {
        datetime: '05_07_25_10_00',
        text: 'Melatonin dosage adjusted from 3mg to 5mg'
      },
      {
        datetime: '05_07_25_13_30',
        text: 'New medication added: Magnesium supplement for muscle relaxation'
      },
      {
        datetime: '05_07_25_15_20',
        text: 'Patient achieved 8 hours of continuous sleep for first time in 3 months'
      },
      {
        datetime: '06_07_25_08_15',
        text: 'Sleep quality rating improved from Good to Excellent'
      },
      {
        datetime: '06_07_25_12_30',
        text: 'Daily exercise routine added to treatment plan: 30 min walk before dinner'
      },
    ],
  };
  await db.updates.put(updatesData);
}

export async function getPatientProfile() {
  return db.patientProfile.toCollection().first();
}

export async function getConversation() {
  return db.conversation.toCollection().first();
}

export async function updatePatientProfile(profile: PatientProfile) {
  return db.patientProfile.put(profile);
}

export async function updateConversation(conversation: Conversation) {
  return db.conversation.put(conversation);
}