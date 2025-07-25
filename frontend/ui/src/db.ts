import Dexie, { Table } from 'dexie';

export interface PatientProfile {
  uid: string;
  name: string;
  age: number;
  bloodType: string;
  allergies: string[];
  treatment: {
    medicationList: string[];
    dailyChecklist: string[];
    appointment: string;
    recommendations: string[];
    sleepHours: number;
    sleepQuality: string;
  };
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
  episodes: object[];
  procedural: object | null;
  semantic: object[];
}

export interface Links {
  id: string; // always 'links' for singleton
  links: any[];
}

export interface General {
  id: string; // always 'general' for singleton
  general: any;
}

class AppDB extends Dexie {
  patientProfile!: Table<PatientProfile, string>; // uid as primary key
  conversation!: Table<Conversation, string>; // cid as primary key
  memory!: Table<Memory, string>; // id as primary key
  links!: Table<Links, string>; // id as primary key
  general!: Table<General, string>; // id as primary key

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
  }
}

export const db = new AppDB();

// Memory DB functions
export async function getMemory() {
  return db.memory.get('memory');
}

export async function updateMemory(memory: Memory) {
  return db.memory.put(memory);
}

export async function addEpisode(episode: object) {
  const memory = await getMemory();
  if (!memory) return;
  memory.episodes.push(episode);
  await updateMemory(memory);
}

export async function addSemantic(semantic: object) {
  const memory = await getMemory();
  if (!memory) return;
  memory.semantic.push(semantic);
  await updateMemory(memory);
}

export async function updateProcedural(procedural: object) {
  const memory = await getMemory();
  if (!memory) return;
  memory.procedural = procedural;
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

// Sample data initialization
export async function initializeSampleData() {
  const existingProfile = await db.patientProfile.toCollection().first();
  if (!existingProfile) {
    await db.patientProfile.add({
      uid: 'user-001',
      name: 'Jane Smith',
      age: 29,
      bloodType: 'A-',
      allergies: ['Peanuts'],
      treatment: {
        medicationList: ['Ibuprofen'],
        dailyChecklist: ['Take medication', 'Walk 30 minutes'],
        appointment: '2024-08-15T09:00:00',
        recommendations: ['Stay hydrated', 'Regular exercise'],
        sleepHours: 8,
        sleepQuality: 'Excellent',
      },
    });
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
  const existingMemory = await db.memory.get('memory');
  if (!existingMemory) {
    await db.memory.add({
      id: 'memory',
      episodes: [],
      procedural: {},
      semantic: [],
    });
  }
  const existingLinks = await db.links.get('links');
  if (!existingLinks) {
    await db.links.add({
      id: 'links',
      links: [],
    });
  }
  const existingGeneral = await db.general.get('general');
  if (!existingGeneral) {
    await db.general.add({
      id: 'general',
      general: {},
    });
  }
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