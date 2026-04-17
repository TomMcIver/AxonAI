import {
  getClassOverview,
  getStudentDashboard,
  getStudentMastery,
  getStudentPedagogy,
  getStudentConversations,
  getStudentFlags,
  getConcepts,
} from './axonai';

/**
 * In-flight dedupe for GETs the app already makes. Starting a request from Login
 * and the destination page shares the same Promise (no extra auth or new endpoints).
 */
const inflight = new Map();

function share(key, factory) {
  if (!inflight.has(key)) {
    const p = factory().finally(() => {
      inflight.delete(key);
    });
    inflight.set(key, p);
  }
  return inflight.get(key);
}

/** Fire early from Login → Teacher; TeacherDashboard awaits the same call. */
export function primeTeacherClassOverview(classId = 1) {
  return share(`class-overview-${classId}`, () => getClassOverview(classId));
}

export function loadTeacherClassOverview(classId = 1) {
  return primeTeacherClassOverview(classId);
}

export function primeStudentDashboard(studentId = 1) {
  return share(`student-bundle-${studentId}`, () =>
    Promise.all([
      getStudentDashboard(studentId),
      getStudentMastery(studentId),
      getStudentPedagogy(studentId),
      getStudentFlags(studentId),
      getStudentConversations(studentId, 20),
      getConcepts('Mathematics').catch(() => null),
    ]).then(([dashboard, mastery, pedagogy, flags, conversations, graphData]) => ({
      dashboard,
      mastery,
      pedagogy,
      flags,
      conversations,
      graphData,
    })),
  );
}

export function loadStudentDashboardBundle(studentId = 1) {
  return primeStudentDashboard(studentId);
}

export function primeParentDashboard(studentId = 1) {
  return share(`parent-bundle-${studentId}`, () =>
    Promise.all([
      getStudentDashboard(studentId),
      getStudentMastery(studentId),
      getStudentFlags(studentId),
      getStudentPedagogy(studentId),
    ]).then(([dashboard, mastery, flags, pedagogy]) => ({
      dashboard,
      mastery,
      flags,
      pedagogy,
    })),
  );
}

export function loadParentDashboardBundle(studentId = 1) {
  return primeParentDashboard(studentId);
}
