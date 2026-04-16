const DEFAULT_API_URL =
  'https://73edpnyeqs6gl3eh4gyfnwoji40ldhgo.lambda-url.ap-southeast-2.on.aws';
const RAW_BASE_URL = process.env.REACT_APP_API_URL || DEFAULT_API_URL;

// Normalize trailing slash so endpoint joins are predictable.
export const BASE_URL = RAW_BASE_URL.replace(/\/+$/, '');

async function fetchAPI(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!response.ok) {
    await response.text().catch(() => '');
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

// Health
export function getHealth() {
  return fetchAPI('/');
}

// Student endpoints
export function getStudentDashboard(studentId) {
  return fetchAPI(`/student/${studentId}/dashboard`);
}

export function getStudentMastery(studentId) {
  return fetchAPI(`/student/${studentId}/mastery`);
}

export function getStudentFlags(studentId) {
  return fetchAPI(`/student/${studentId}/flags`);
}

export function getStudentPedagogy(studentId) {
  return fetchAPI(`/student/${studentId}/pedagogy`);
}

export function getStudentConversations(studentId, limit = 20, offset = 0) {
  return fetchAPI(`/student/${studentId}/conversations?limit=${limit}&offset=${offset}`);
}

export function getStudentPredictions(studentId) {
  return fetchAPI(`/student/${studentId}/predictions`);
}

// Conversation messages
export function getConversationMessages(conversationId) {
  return fetchAPI(`/conversation/${conversationId}/messages`);
}

// Class endpoints
export function getClassOverview(classId) {
  return fetchAPI(`/class/${classId}/overview`);
}

// Concepts / Knowledge Graph
export function getConcepts(subject) {
  return fetchAPI(`/concepts/${subject}`);
}

/**
 * Class concept mastery summary (optional).
 * The hosted API may not expose this route yet — 404 returns null.
 * The teacher UI falls back to aggregated /student/…/mastery.
 * Deploy the handler from `routes/lambda_new_routes.py` to enable the endpoint.
 */
export async function getClassConceptSummary(classId) {
  const url = `${BASE_URL}/class/${classId}/concept-summary`;
  try {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      await response.text().catch(() => '');
      return null;
    }
    return await response.json();
  } catch {
    return null;
  }
}

// Teacher AI insights — GPT-4o generated summaries
export const getTeacherAIInsights = async (studentId) => {
  try {
    const res = await fetch(`${BASE_URL}/student/${studentId}/ai-insights`);
    return res.ok ? res.json() : null;
  } catch {
    return null;
  }
};

// Wellbeing context
export const getStudentWellbeing = async (studentId) => {
  try {
    const res = await fetch(`${BASE_URL}/student/${studentId}/wellbeing`);
    return res.ok ? res.json() : null;
  } catch {
    return null;
  }
};

// Pedagogical memory (what approaches have worked)
export const getPedagogicalMemory = async (studentId) => {
  try {
    const res = await fetch(`${BASE_URL}/student/${studentId}/pedagogical-memory`);
    return res.ok ? res.json() : null;
  } catch {
    return null;
  }
};

// Student summary — per-class concept mastery breakdown from live API
export const getStudentSummary = async (studentId) => {
  try {
    const res = await fetch(`${BASE_URL}/student/${studentId}/summary`);
    return res.ok ? res.json() : null;
  } catch {
    return null;
  }
};
